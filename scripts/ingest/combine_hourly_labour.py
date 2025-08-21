#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
combine_hourly_labour.py — fixed-header (skip 6 rows) parser

What it does
------------
• Reads all *.xls* files under data/raw/labour/actual_labor
• For every sheet, reads with header=6 (i.e., skips the first 6 rows)
• Extracts: hour_range, actual_hours, actual_labor, sales_value, check_count, sales_per_labor_hour, scheduled_hours
• Normalizes hour_range to HH:MM-HH:MM
• pc_number and date parsed from sheet name like "<PC>, <mdyyyy>" or "<PC>, 08/20/2025"
• Skips rollup/summary sheets
• If Sales or SPLH is missing, derives it from the other when possible

Outputs
-------
data/processed/actual_and_schedule_hourly.csv
data/processed/actual_table_labor.csv
data/processed/schedule_table_labor.csv
"""

import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import pandas as pd

# ---------------- Paths (defaults) ----------------
SCRIPT_PATH  = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
DEFAULT_INPUT_DIR  = PROJECT_ROOT / "data" / "raw" / "labour" / "actual_labor"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

DEBUG = os.getenv("DEBUG", "0") == "1"

# ------------- Heuristics & Keys -------------
# Always use header row at index 6 (i.e., skip 0..5)
FIXED_HEADER_ROW = 6

HOUR_PATTERNS = [
    r"^\s*\d{1,2}\s*[ap]\.?m\.?\s*$",              # 6 am, 6 AM
    r"^\s*\d{1,2}:\d{2}\s*[ap]\.?m\.?\s*$",        # 06:00 AM
    r"^\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*$",  # 06:00-07:00
    r"^\s*\d{1,2}\s*-\s*\d{1,2}\s*[ap]\.?m\.?\s*$" # 6 - 7 AM
]
HOUR_RE = re.compile("|".join(HOUR_PATTERNS), flags=re.IGNORECASE)

def norm(s: str) -> str:
    return re.sub(r"[\s/_\-\(\)]+", "", str(s).strip().lower())

# Richer key list for common report flavors
COL_KEYS = {
    "hour": [
        "hour", "hours", "hourrange", "time", "timerange", "60minuteinterval"
    ],
    "actual_hours": [
        "actualhours", "laborhours", "labourhours", "hours", "hrs"
    ],
    "actual_labor": [
        "actuallabor", "actuallabour",
        "labor$", "labour$", "laboramount", "labouramount",
        "laborcost", "labourcost"
    ],
    "sales_value": [
        # common
        "netsales", "salesvalue", "sales$", "salesamount", "sales",
        # variants seen in some exports
        "netsalesmm", "netsales-lm", "netsales-mtd", "netsales-mm", "netsales-m/m"
    ],
    "check_count": [
        "checks", "checkcount", "transactions", "tickets"
    ],
    "sales_per_labor_hour": [
        "splh", "salesperlaborhour", "salesperlabourhour",
        "sales/laborhr", "sales/labourhr", "salesperlabhr",
        "sales/laborhour-mm", "sales_per_labor_hour", "sales_per_labour_hour",
        # sometimes punctuation
        "saleslaborhour", "salesperlaborhour-mm"
    ],
    "scheduled_hours": [
        "scheduledhours", "schedhours", "schedulehours",
        "scheduledhrs", "sched.hours", "schhours"
    ],
}

# --------- Utilities ----------
def log(msg: str):
    print(msg, flush=True)

def to_num(x):
    """Parse numeric with $, commas, spaces; keep None for blanks."""
    if pd.isna(x):
        return None
    try:
        return float(str(x).replace(",", "").replace("$", "").strip())
    except Exception:
        return None

def looks_like_hour(val):
    if pd.isna(val): return False
    s = str(val).strip()
    return bool(HOUR_RE.match(s)) or ("-" in s and ":" in s)

def normalize_hour_range(val):
    """Return HH:MM-HH:MM for single times or ranges."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        if "-" in s and any(ch.isdigit() for ch in s):
            left, right = [t.strip(" -") for t in s.split("-", 1)]
            t1 = pd.to_datetime(left).strftime("%H:%M")
            t2 = pd.to_datetime(right).strftime("%H:%M")
            return f"{t1}-{t2}"
        else:
            t1 = pd.to_datetime(s).strftime("%H:%M")
            t2 = (pd.to_datetime(s) + pd.Timedelta(hours=1)).strftime("%H:%M")
            return f"{t1}-{t2}"
    except Exception:
        return s  # leave as-is if we can't parse

def pick_col(df: pd.DataFrame, keys: List[str]) -> Optional[str]:
    """Pick a column by normalized exact match first, then 'contains'."""
    nmap = {c: norm(c) for c in df.columns}
    inv = {}
    for k, v in nmap.items():
        if v not in inv:
            inv[v] = k
    for k in keys:
        if k in inv:
            return inv[k]
    for c in df.columns:
        lc = norm(c)
        if any(k in lc for k in keys):
            return c
    return None

def strip_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

def drop_total_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mask_total = df.apply(lambda r: r.astype(str).str.contains(r"\btotal\b", case=False, regex=True).any(), axis=1)
    hour_mask = df.iloc[:, 0].astype(str).map(looks_like_hour)
    return df[~(mask_total & ~hour_mask)]

def collapse_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.columns.duplicated().any():
        data = {}
        for col in pd.unique(df.columns):
            dupes = [c for c in df.columns if c == col]
            if len(dupes) == 1:
                data[col] = df[col]
            else:
                ser = df[dupes].bfill(axis=1).iloc[:, 0]
                data[col] = ser
        df2 = pd.DataFrame(data, index=df.index)
        df2 = df2[[c for c in df2.columns]]
        return df2
    return df

def parse_sheet_tokens(sheet_name: str):
    """
    Expect '<PC>, <mdyyyy>' or '<PC>, 08/20/2025'.
    """
    parts = [p.strip() for p in str(sheet_name).split(",")]
    pc = None
    bdate = None
    if parts:
        m = re.search(r"\b(\d{5,6})\b", parts[0])
        if m:
            pc = m.group(1)
    for p in parts[1:]:
        token = re.sub(r"[^0-9/.-]", "", p)
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%m.%d.%Y", "%m%d%Y"):
            try:
                bdate = datetime.strptime(token, fmt).date()
                break
            except Exception:
                continue
        if bdate:
            break
        digits = re.sub(r"\D", "", p)
        if len(digits) in (7, 8):
            try:
                if len(digits) == 7:
                    md = int(digits[:-4]); y = int(digits[-4:])
                    s  = f"{md:04d}{y}"
                    bdate = datetime.strptime(s, "%m%d%Y").date()
                else:
                    bdate = datetime.strptime(digits, "%m%d%Y").date()
            except Exception:
                pass
    return pc, bdate

# --------- Core parsing ----------
def parse_one_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    # Always skip 6 rows -> header is row index 6
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, header=FIXED_HEADER_ROW, engine=None)
    except Exception:
        # Some legacy xls need openpyxl explicitly
        df = pd.read_excel(path, sheet_name=sheet_name, header=FIXED_HEADER_ROW, engine="openpyxl")

    sname = (sheet_name or "").strip().lower()
    if sname in {"total, total", "total,total", "summary", "totals"}:
        if DEBUG:
            log(f"  [SKIP] rollup sheet: {sheet_name}")
        return pd.DataFrame()

    df = strip_unnamed(df)
    df.columns = [str(c).strip() for c in df.columns]

    # Identify columns
    col_hour   = pick_col(df, COL_KEYS["hour"])
    col_act_hrs = pick_col(df, COL_KEYS["actual_hours"])
    col_act_lab = pick_col(df, COL_KEYS["actual_labor"])
    col_sales   = pick_col(df, COL_KEYS["sales_value"])
    col_checks  = pick_col(df, COL_KEYS["check_count"])
    col_splh    = pick_col(df, COL_KEYS["sales_per_labor_hour"])
    col_sched   = pick_col(df, COL_KEYS["scheduled_hours"])

    if not col_hour:
        # fallback: first column that looks like hour in first 4
        for c in df.columns[:4]:
            try:
                if df[c].astype(str).map(looks_like_hour).any():
                    col_hour = c
                    break
            except Exception:
                continue
    if not col_hour:
        if DEBUG:
            log(f"  [FAIL] {path.name}:{sheet_name} no hour column. cols={list(df.columns)}")
        return pd.DataFrame()

    keep = [col_hour, col_act_hrs, col_act_lab, col_sales, col_checks, col_splh, col_sched]
    keep = [c for c in keep if c]
    sub = df[keep].copy()
    sub = drop_total_rows(sub)

    # Rename to target names
    rn = {col_hour: "hour_range"}
    if col_act_hrs: rn[col_act_hrs] = "actual_hours"
    if col_act_lab: rn[col_act_lab] = "actual_labor"
    if col_sales:   rn[col_sales]   = "sales_value"
    if col_checks:  rn[col_checks]  = "check_count"
    if col_splh:    rn[col_splh]    = "sales_per_labor_hour"
    if col_sched:   rn[col_sched]   = "scheduled_hours"
    sub = sub.rename(columns=rn)

    # Collapse any duplicates caused by rename
    sub = collapse_duplicate_columns(sub)

    # Normalize numbers
    for col in ["actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour","scheduled_hours"]:
        if col in sub.columns:
            sub[col] = sub[col].apply(to_num)

    # Try to derive missing sales / SPLH when possible
    if "sales_per_labor_hour" not in sub.columns or sub["sales_per_labor_hour"].isna().all():
        if "sales_value" in sub.columns and "actual_hours" in sub.columns:
            with pd.option_context("mode.use_inf_as_na", True):
                sub["sales_per_labor_hour"] = sub.apply(
                    lambda r: (r["sales_value"]/r["actual_hours"]) if (to_num(r.get("sales_value")) is not None and to_num(r.get("actual_hours")) not in (None, 0)) else None,
                    axis=1
                )
    if ("sales_value" not in sub.columns or sub["sales_value"].isna().all()) and \
       ("sales_per_labor_hour" in sub.columns and "actual_hours" in sub.columns):
        sub["sales_value"] = sub.apply(
            lambda r: (r["sales_per_labor_hour"] * r["actual_hours"]) if (to_num(r.get("sales_per_labor_hour")) is not None and to_num(r.get("actual_hours")) is not None) else None,
            axis=1
        )

    # Normalize hour_range
    sub["hour_range"] = sub["hour_range"].map(normalize_hour_range)
    sub = sub.dropna(subset=["hour_range"])

    # pc/date from sheet name
    pc, bdate = parse_sheet_tokens(sheet_name)
    sub["pc_number"] = pc
    sub["date"] = bdate

    # Ensure all expected columns exist
    for col in ["actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour","scheduled_hours"]:
        if col not in sub.columns:
            sub[col] = None

    # Final shape & clean
    sub = sub[[
        "pc_number","date","hour_range",
        "actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour","scheduled_hours"
    ]]
    sub = sub.dropna(subset=["pc_number","date"])
    sub = sub.drop_duplicates(subset=["pc_number","date","hour_range"])

    return sub

def combine(input_dir: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_csv = output_dir / "actual_and_schedule_hourly.csv"
    out_actual = output_dir / "actual_table_labor.csv"
    out_schedule = output_dir / "schedule_table_labor.csv"

    files = sorted(list(input_dir.glob("*.xls")) + list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xlsm")))
    if not files:
        log(f"[INFO] No Excel files found in {input_dir}")
        return out_csv

    all_rows = []
    for f in files:
        try:
            xl = pd.ExcelFile(f, engine=None)
        except Exception:
            xl = pd.ExcelFile(f, engine="openpyxl")
        log(f"[FILE] {f.name} | sheets={len(xl.sheet_names)}")
        for sn in xl.sheet_names:
            df = parse_one_sheet(f, sn)
            if not df.empty:
                all_rows.append(df)
                log(f"  [OK] {sn}: {len(df)} rows")
            else:
                log(f"  [SKIP] {sn}: 0 rows parsed")

    if not all_rows:
        log("[INFO] No rows parsed from any sheet.")
        return out_csv

    combined = pd.concat(all_rows, ignore_index=True)
    combined = combined.drop_duplicates(subset=["pc_number","date","hour_range"])
    combined.to_csv(out_csv, index=False)

    # Splits for DB tables
    actual_cols = ["pc_number","date","hour_range","actual_hours","actual_labor","sales_value","check_count"]
    schedule_cols = ["pc_number","date","hour_range","scheduled_hours"]
    combined[actual_cols].to_csv(out_actual, index=False)
    combined[schedule_cols].to_csv(out_schedule, index=False)

    # Summary log
    dmin = pd.to_datetime(combined["date"]).min()
    dmax = pd.to_datetime(combined["date"]).max()
    log(f"[INFO] Date span: {getattr(dmin, 'date', lambda: 'N/A')() if pd.notna(dmin) else 'N/A'} → {getattr(dmax, 'date', lambda: 'N/A')() if pd.notna(dmax) else 'N/A'}")
    log(f"[INFO] Distinct PCs: {combined['pc_number'].nunique()} | Distinct dates: {combined['date'].nunique()}")
    log(f"[DONE] Wrote {len(combined)} rows -> {out_csv}")
    log(f"[DONE] Wrote actual table CSV   -> {out_actual}")
    log(f"[DONE] Wrote schedule table CSV -> {out_schedule}")

    return out_csv

# ------------- CLI -------------
def main():
    parser = argparse.ArgumentParser(description="Combine hourly labour & sales Excel files (skip first 6 rows).")
    parser.add_argument("--input", "-i", type=str, default=str(DEFAULT_INPUT_DIR),
                        help="Input directory containing *.xls* files (default: data/raw/labour/actual_labor)")
    parser.add_argument("--output", "-o", type=str, default=str(DEFAULT_OUTPUT_DIR),
                        help="Output directory for processed CSVs (default: data/processed)")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    log(f"[INFO] Input:  {input_dir}")
    log(f"[INFO] Output: {output_dir}")

    combine(input_dir, output_dir)

if __name__ == "__main__":
    main()
