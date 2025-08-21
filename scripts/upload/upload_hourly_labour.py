#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from supabase_client import supabase

SCRIPT_PATH  = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
INPUT_CSV    = PROJECT_ROOT / "data" / "processed" / "actual_and_schedule_hourly.csv"

ACTUAL_TABLE = "actual_table_labor"
SCHED_TABLE  = "schedule_table_labor"
CHUNK = 1000  # rows per batch, can be made configurable

def require_env():
    # Credentials are loaded in supabase_client.py
    if not supabase:
        raise SystemExit("[ERROR] Supabase client not initialized.")

def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"[ERROR] Input CSV not found: {path}")
    df = pd.read_csv(path, dtype={
        "pc_number": str,
        "hour_range": str,
    }, parse_dates=["date"])
    # Ensure date column is date-only (not datetime)
    df["date"] = df["date"].dt.date
    return df

def split_frames(df: pd.DataFrame):
    actual_cols = ["pc_number","date","hour_range","actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour"]
    sched_cols  = ["pc_number","date","hour_range","scheduled_hours"]

    actual = df[actual_cols].copy()
    sched  = df[sched_cols].copy()

    # Drop rows that are entirely empty on payload columns
    actual = actual.dropna(how="all", subset=["actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour"])
    sched  = sched.dropna(how="all", subset=["scheduled_hours"])

    # Basic sanitization
    for c in ["pc_number","hour_range"]:
        actual[c] = actual[c].astype(str)
        sched[c]  = sched[c].astype(str)

    # Deduplicate by key
    actual = actual.drop_duplicates(subset=["pc_number","date","hour_range"])
    sched  = sched.drop_duplicates(subset=["pc_number","date","hour_range"])

    # Ensure 'date' column is string for JSON serialization
    actual["date"] = actual["date"].astype(str)
    sched["date"] = sched["date"].astype(str)

    actual = actual.replace([np.inf, -np.inf], np.nan)
    sched = sched.replace([np.inf, -np.inf], np.nan)
    actual = actual.where(pd.notnull(actual), None)
    sched = sched.where(pd.notnull(sched), None)

    # Fill NaN in numeric columns with 0
    numeric_actual_cols = ["actual_hours", "actual_labor", "sales_value", "check_count", "sales_per_labor_hour"]
    numeric_sched_cols = ["scheduled_hours"]

    actual[numeric_actual_cols] = actual[numeric_actual_cols].fillna(0)
    sched[numeric_sched_cols] = sched[numeric_sched_cols].fillna(0)

    return actual, sched

def upsert(table: str, rows: List[Dict], conflict_cols: List[str]):
    if not rows:
        print(f"[INFO] No rows to upsert for {table}.")
        return
    total = len(rows)
    for i in range(0, total, CHUNK):
        batch = rows[i:i+CHUNK]
        supabase.table(table).upsert(batch, on_conflict=conflict_cols).execute()
        print(f"[UPSERT:{table}] {i+len(batch)}/{total}")

def main():
    require_env()
    df = read_csv(INPUT_CSV)

    # Quick sanity stats
    min_date = df["date"].min()
    max_date = df["date"].max()
    print(f"[INFO] Loaded {len(df)} rows from {INPUT_CSV}")
    print(f"[INFO] Date span: {min_date} → {max_date}")
    print(f"[INFO] Distinct PCs: {df['pc_number'].nunique()} | Distinct dates: {df['date'].nunique()}")

    actual, sched = split_frames(df)
    print(f"[INFO] Prepared actuals:  {len(actual)} rows")
    print(f"[INFO] Prepared schedule: {len(sched)} rows")

    # Convert to list-of-dicts for upload
    upsert(ACTUAL_TABLE, actual.to_dict(orient="records"), ["pc_number","date","hour_range"])
    upsert(SCHED_TABLE,  sched.to_dict(orient="records"),  ["pc_number","date","hour_range"])

    print("[DONE] Upload complete.")

if __name__ == "__main__":
    main()


