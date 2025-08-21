#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload combined hourly labour file into Supabase.

- Reads data/processed/actual_and_schedule_hourly.csv
- Splits into:
    * actual_table_labor (pc_number, date, hour_range, actual_hours, actual_labor, sales_value, check_count, sales_per_labor_hour)
    * schedule_table_labor (pc_number, date, hour_range, scheduled_hours)
- JSON-sanitizes all records (no NaN/±Inf; ISO dates)
- Upserts in CHUNKs; if unique index is missing -> falls back to delete+insert merge.

Requires either:
  * from supabase_client import supabase  (your helper that reads .env), OR
  * SUPABASE_URL and SUPABASE_KEY in environment (.env)

Python 3.9 compatible.
"""
import os
import math
from typing import List, Dict, Any, Tuple
from pathlib import Path

import numpy as np
import pandas as pd

# Prefer your local client if present
_SUPABASE_READY = False
try:
    from supabase_client import supabase  # your existing helper
    _SUPABASE_READY = True
except Exception:
    pass

if not _SUPABASE_READY:
    from dotenv import load_dotenv
    from supabase import create_client
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise SystemExit("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in .env")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Paths ----------------
SCRIPT_PATH  = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
INPUT_CSV    = PROJECT_ROOT / "data" / "processed" / "actual_and_schedule_hourly.csv"

# ---------------- Config ----------------
ACTUAL_TABLE = "actual_table_labor"
SCHED_TABLE  = "schedule_table_labor"
CHUNK        = int(os.getenv("UPLOAD_CHUNK_SIZE", "1000"))  # rows per request
DRY_RUN      = bool(int(os.getenv("DRY_RUN", "0")))         # set 1 to skip DB writes

# JSON-safe numeric columns
NUM_COLS_ACTUAL = ["actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour"]
NUM_COLS_SCHED  = ["scheduled_hours"]

# ------------- Helpers -------------
def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"[ERROR] Input CSV not found: {path}")
    df = pd.read_csv(
        path,
        dtype={"pc_number": str, "hour_range": str},
        parse_dates=["date"],
        dayfirst=False, infer_datetime_format=True
    )
    # Coerce to date-only ISO strings to satisfy PostgREST
    df["date"] = df["date"].dt.date.astype(str)
    return df

def split_frames(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    actual_cols = ["pc_number","date","hour_range","actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour"]
    sched_cols  = ["pc_number","date","hour_range","scheduled_hours"]

    # Ensure columns exist even if missing from some files
    for c in actual_cols:
        if c not in df.columns:
            df[c] = np.nan
    for c in sched_cols:
        if c not in df.columns:
            df[c] = np.nan

    actual = df[actual_cols].copy()
    sched  = df[sched_cols].copy()

    # Drop rows with no payload at all
    actual = actual.dropna(how="all", subset=NUM_COLS_ACTUAL)
    sched  = sched.dropna(how="all", subset=NUM_COLS_SCHED)

    # Deduplicate on key
    actual = actual.drop_duplicates(subset=["pc_number","date","hour_range"])
    sched  = sched.drop_duplicates(subset=["pc_number","date","hour_range"])

    # Normalize numeric columns to float; leave missing as NaN
    for col in NUM_COLS_ACTUAL:
        actual[col] = pd.to_numeric(actual[col], errors="coerce")
    for col in NUM_COLS_SCHED:
        sched[col] = pd.to_numeric(sched[col], errors="coerce")

    # Ensure key types are strings
    for c in ["pc_number","hour_range","date"]:
        actual[c] = actual[c].astype(str)
        sched[c]  = sched[c].astype(str)

    return actual, sched

def _finite_or_none(x: Any) -> Any:
    # Convert numpy scalars to Python
    if isinstance(x, (np.generic,)):
        x = x.item()
    if x is None:
        return None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, (int, bool, str)):
        return x
    # For anything odd, try float then fallback None
    try:
        xf = float(x)
        return xf if math.isfinite(xf) else None
    except Exception:
        return None

def json_sanitize_records(df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
    # First replace ±Inf with NaN, then convert NaN to None
    df = df.replace([np.inf, -np.inf], np.nan)
    records = df.to_dict(orient="records")
    clean: List[Dict[str, Any]] = []
    for rec in records:
        out: Dict[str, Any] = {}
        for k, v in rec.items():
            # numeric columns must be numbers or None
            if k in numeric_cols:
                out[k] = _finite_or_none(v)
            else:
                # keep strings/booleans; strip non-finite floats
                out[k] = _finite_or_none(v)
        clean.append(out)
    return clean

def _on_conflict_value(cols: List[str]) -> Any:
    """
    Supabase Python client accepts either a list or a comma string depending on version.
    We'll pass a comma-joined string to be safe across versions.
    """
    return ",".join(cols)

def _do_upsert(table: str, rows: List[Dict[str, Any]], conflict_cols: List[str]) -> None:
    supabase.table(table).upsert(rows, on_conflict=_on_conflict_value(conflict_cols)).execute()

def _do_insert(table: str, rows: List[Dict[str, Any]]) -> None:
    supabase.table(table).insert(rows).execute()

def _do_delete_keys(table: str, keys: List[Tuple[str,str,str]]) -> None:
    """
    Delete by composite key in manageable chunks using an IN filter on a synthetic key.
    We build a synthetic key "pc|date|hour" in both Python and SQL for efficient matching.
    """
    if not keys:
        return
    # Build list of composite key strings
    key_strings = [f"{pc}|{dt}|{hr}" for (pc, dt, hr) in keys]

    # Delete in chunks of ~500 to keep URL length reasonable
    step = 500
    for i in range(0, len(key_strings), step):
        batch_keys = key_strings[i:i+step]
        # Use PostgREST "in" filter on a computed column expression via .or() is tricky;
        # Instead, send them as an equality list on a helper column value using 'in'.
        # We'll push as RPC alternative if you prefer later; for now we delete row-by-row for safety.
        for ks in batch_keys:
            pc, dt, hr = ks.split("|", 2)
            supabase.table(table) \
                .delete() \
                .eq("pc_number", pc) \
                .eq("date", dt) \
                .eq("hour_range", hr) \
                .execute()

def _merge_without_index(table: str, rows: List[Dict[str, Any]]) -> None:
    """
    Fallback when unique index is missing: delete then insert for the batch.
    """
    if not rows:
        return
    # Collect keys present in the incoming batch
    keys = []
    for r in rows:
        pc = str(r.get("pc_number", ""))
        dt = str(r.get("date", ""))
        hr = str(r.get("hour_range", ""))
        if pc and dt and hr:
            keys.append((pc, dt, hr))

    _do_delete_keys(table, keys)   # delete any existing rows with those keys
    _do_insert(table, rows)        # insert fresh

def upsert_with_fallback(table: str, rows: List[Dict[str, Any]], conflict_cols: List[str]) -> None:
    if not rows:
        return
    try:
        _do_upsert(table, rows, conflict_cols)
    except Exception as e:
        # If the DB lacks a unique index, PostgREST returns 42P10
        msg = str(e)
        if "42P10" in msg or "no unique or exclusion constraint" in msg:
            print(f"[WARN] {table}: missing unique index on {conflict_cols}. Using delete+insert merge for this batch.")
            _merge_without_index(table, rows)
        else:
            raise

def upload_table(table: str, rows: List[Dict[str, Any]], conflict_cols: List[str]) -> None:
    total = len(rows)
    if total == 0:
        print(f"[INFO] {table}: nothing to upload.")
        return
    for i in range(0, total, CHUNK):
        batch = rows[i:i+CHUNK]
        if DRY_RUN:
            print(f"[DRY] {table}: would upload {len(batch)} rows ({i+len(batch)}/{total})")
            continue
        upsert_with_fallback(table, batch, conflict_cols)
        print(f"[UPSERT:{table}] {i+len(batch)}/{total}")

def main():
    # 1) Read
    df = read_csv(INPUT_CSV)

    # 2) Quick stats
    print(f"[INFO] Loaded {len(df)} rows from {INPUT_CSV}")
    try:
        print(f"[INFO] Date span: {df['date'].min()} → {df['date'].max()}")
    except Exception:
        pass
    print(f"[INFO] Distinct PCs: {df['pc_number'].nunique()} | Distinct dates: {df['date'].nunique()}")

    # 3) Split
    actual_df, sched_df = split_frames(df)
    print(f"[INFO] Prepared actuals:  {len(actual_df)} rows")
    print(f"[INFO] Prepared schedule: {len(sched_df)} rows")

    # 4) JSON sanitize
    actual_rows = json_sanitize_records(actual_df, NUM_COLS_ACTUAL)
    sched_rows  = json_sanitize_records(sched_df,  NUM_COLS_SCHED)

    # 5) Upload (with fallback if unique index is missing)
    upload_table(ACTUAL_TABLE, actual_rows, ["pc_number","date","hour_range"])
    upload_table(SCHED_TABLE,  sched_rows,  ["pc_number","date","hour_range"])

    print("[DONE] Upload complete.")

if __name__ == "__main__":
    main()
