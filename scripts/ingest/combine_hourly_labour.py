#!/usr/bin/env python3
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import pandas as pd

# ---------------- Paths ----------------
SCRIPT_PATH  = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
INPUT_DIR    = PROJECT_ROOT / "data" / "raw" / "labour" / "actual_labor"
OUTPUT_DIR   = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV      = OUTPUT_DIR / "actual_and_schedule_hourly.csv"

DEBUG = os.getenv("DEBUG", "0") == "1"

# ------------- Heuristics & Keys -------------
HOUR_PATTERNS = [
    r"^\s*\d{1,2}\s*[ap]\.?m\.?\s*$",              # 6 am, 6 AM
    r"^\s*\d{1,2}:\d{2}\s*[ap]\.?m\.?\s*$",        # 06:00 AM
    r"^\s*\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2}\s*$",  # 06:00-07:00
    r"^\s*\d{1,2}\s*-\s*\d{1,2}\s*[ap]\.?m\.?\s*$" # 6 - 7 AM
]
HOUR_RE = re.compile("|".join(HOUR_PATTERNS), flags=re.IGNORECASE)

COL_KEYS = {
    "hour": [
        "hour", "hours", "hour range", "time", "time range", "60 minute interval"
    ],
    "actual_hours":     ["actual hours", "labor hours", "labour hours", "hours", "hrs"],
    "actual_labor":     ["actual labor", "actual labour", "labor $", "labour $", "labor amount", "labour amount", "labor cost", "labour cost"],
    "sales_value":      ["net sales", "sales value", "sales $", "sales amount", "sales"],
    "check_count":      ["checks", "check count", "transactions", "tickets"],
    "sales_per_labour_hour": ["splh", "sales per labor hour", "sales per labour hour", "sales/labor hr", "sales/labour hr", "sales per lab hr", "sales / labor hour - mm"],
    "scheduled_hours":  ["scheduled hours", "sched hours", "schedule hours", "scheduled hrs", "sched. hours", "sch hours"],
}

def norm(s):
    return str(s).strip().lower()

def to_num(x):
    if pd.isna(x):
        return None
    try:
        return float(str(x).replace(",", "").replace("$", "").strip())
    except Exception:
        return None

def looks_like_hour(val):
    if pd.isna(val):
        return False
    s = str(val).strip()
    return bool(HOUR_RE.match(s))

def normalize_hour_range(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    try:
        if "-" in s:
            left, right = [t.strip(" -") for t in s.split("-", 1)]
            t1 = pd.to_datetime(left).strftime("%H:%M")
            t2 = pd.to_datetime(right).strftime("%H:%M")
            return f"{t1}-{t2}"
        else:
            t1 = pd.to_datetime(s).strftime("%H:%M")
            t2 = (pd.to_datetime(s) + pd.Timedelta(hours=1)).strftime("%H:%M")
            return f"{t1}-{t2}"
    except Exception:
        return s

def pick_col(df: pd.DataFrame, keys: List[str]) -> Optional[str]:
    # exact normalized match first
    nmap = {c: norm(c) for c in df.columns}
    inv = {v: k for k, v in nmap.items()}
    for k in keys:
        if k in inv:
            return inv[k]
    # contains match
    for c in df.columns:
        lc = norm(c)
        if any(k in lc for k in keys):
            return c
    return None

def find_header_row(df_raw: pd.DataFrame, max_rows=300) -> Optional[int]:
    """
    Try to find the table header row.
    Strategy:
      1) Row that contains "hour" and any of: sales/labor/labour/checks/splh.
      2) Row where first non-empty cell equals/contains 'hour'.
    """
    lim = min(max_rows, len(df_raw))
    for i in range(lim):
        row = df_raw.iloc[i].astype(str).str.strip().str.lower()
        if row.str.contains("hour").any() and (
            row.str.contains("sales").any() or row.str.contains("labour").any() or
            row.str.contains("labor").any() or row.str.contains("checks").any() or
            row.str.contains("splh").any()
        ):
            return i
    for i in range(lim):
        row = df_raw.iloc[i]
        first_nonempty = None
        for v in row:
            if pd.notna(v) and str(v).strip() != "":
                first_nonempty = str(v).strip().lower()
                break
        if first_nonempty and "hour" in first_nonempty:
            return i
    return None

def parse_sheet_tokens(sheet_name: str):
    """
    Expect '<PC>, <mdyyyy>' like '301290, 8202025' (Aug 20, 2025).
    Extract left 5-6 digit PC and try to parse the rest as a date.
    """
    parts = [p.strip() for p in sheet_name.split(",")]
    pc = None
    bdate = None
    if parts:
        m = re.search(r"\b(\d{5,6})\b", parts[0])
        if m:
            pc = m.group(1)
    # Try to parse any date-looking token in the remainder
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
        # special case like '8202025' -> '08-20-2025'
        digits = re.sub(r"\D", "", p)
        if len(digits) in (7, 8):
            try:
                if len(digits) == 7:
                    md = int(digits[:-4])
                    y  = int(digits[-4:])
                    s  = f"{md:04d}{y}"
                    bdate = datetime.strptime(s, "%m%d%Y").date()
                else:
                    bdate = datetime.strptime(digits, "%m%d%Y").date()
            except Exception:
                pass
    return pc, bdate

def strip_unnamed(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

def drop_total_rows(df: pd.DataFrame) -> pd.DataFrame:
    # Drop rows that are clearly totals/summary
    mask_total = df.apply(lambda r: r.astype(str).str.contains(r"\btotal\b", case=False, regex=True).any(), axis=1)
    hour_mask = df.iloc[:, 0].astype(str).map(looks_like_hour)
    return df[~(mask_total & ~hour_mask)]

def parse_one_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    sname = (sheet_name or "").strip().lower()
    if sname == "total, total":
        if DEBUG:
            print("  [SKIP] {}: rollup sheet".format(sheet_name))
        return pd.DataFrame()

    # Always use row 6 as header (data starts from row 7)
    hdr = 6

    df = pd.read_excel(path, sheet_name=sheet_name, header=hdr, engine="openpyxl")
    df = strip_unnamed(df)
    df.columns = [str(c).strip() for c in df.columns]

    # Pick columns
    col_hour = pick_col(df, COL_KEYS["hour"])
    if not col_hour:
        for c in df.columns[:4]:
            if df[c].astype(str).map(looks_like_hour).any():
                col_hour = c
                break

    col_act_hrs   = pick_col(df, COL_KEYS["actual_hours"])
    col_act_lab   = pick_col(df, COL_KEYS["actual_labor"])
    col_sales     = pick_col(df, COL_KEYS["sales_value"])
    col_checks    = pick_col(df, COL_KEYS["check_count"])
    col_sales_per_labour_hour = pick_col(df, COL_KEYS["sales_per_labour_hour"])
    col_sched     = pick_col(df, COL_KEYS["scheduled_hours"])

    if not col_hour:
        if DEBUG:
            print("  [FAIL] {}:{} no hour column found in columns={}".format(path.name, sheet_name, list(df.columns)))
            print(df.head(25))
        return pd.DataFrame()

    keep = [col_hour, col_act_hrs, col_act_lab, col_sales, col_checks, col_sales_per_labour_hour, col_sched]
    keep = [c for c in keep if c]
    sub = df[keep].copy()
    sub = drop_total_rows(sub)

    # Rename
    rn = {col_hour: "hour_range"}
    if col_act_hrs: rn[col_act_hrs] = "actual_hours"
    if col_act_lab: rn[col_act_lab] = "actual_labor"
    if col_sales:   rn[col_sales]   = "sales_value"
    if col_checks:  rn[col_checks]  = "check_count"
    if col_sales_per_labour_hour:
        rn[col_sales_per_labour_hour] = "sales_per_labour_hour"
    if col_sched:   rn[col_sched]   = "scheduled_hours"
    sub = sub.rename(columns=rn)

    # Cast numerics
    for col in ["actual_hours","actual_labor","sales_value","check_count","sales_per_labour_hour","scheduled_hours"]:
        if col in sub.columns:
            sub[col] = sub[col].map(to_num)

    # Normalize hour_range and drop blanks
    sub["hour_range"] = sub["hour_range"].map(normalize_hour_range)
    sub = sub.dropna(subset=["hour_range"])

    # Attach PC/date from sheet name
    pc, bdate = parse_sheet_tokens(sheet_name)
    sub["pc_number"] = pc
    sub["date"] = bdate

    # Order columns and clean
    for col in ["actual_hours","actual_labor","sales_value","check_count","sales_per_labour_hour","scheduled_hours"]:
        if col not in sub.columns:
            sub[col] = None

    sub = sub[["pc_number","date","hour_range","actual_hours","actual_labor","sales_value","check_count","sales_per_labour_hour","scheduled_hours"]]
    sub = sub.dropna(subset=["pc_number","date"])
    sub = sub.dropna(how="all", subset=["actual_hours","actual_labor","sales_value","check_count","sales_per_labor_hour","scheduled_hours"])
    sub = sub.drop_duplicates(subset=["pc_number","date","hour_range"])
    return sub

def combine():
    files = sorted(INPUT_DIR.glob("*.xls*"))
    if not files:
        print("[INFO] No Excel files found in {}".format(INPUT_DIR))
        return
    all_rows = []
    total_rows = 0
    for f in files:
        try:
            xl = pd.ExcelFile(f, engine="openpyxl")
            print("[FILE] {} | sheets={}".format(f.name, len(xl.sheet_names)))
            for sn in xl.sheet_names:
                df = parse_one_sheet(f, sn)
                if not df.empty:
                    cnt = len(df)
                    total_rows += cnt
                    all_rows.append(df)
                    print("  [OK] {}: {} rows".format(sn, cnt))
                else:
                    print("  [SKIP] {}: 0 rows parsed".format(sn))
        except Exception as e:
            print("[WARN] Failed on {}: {}".format(f.name, e))

    if not all_rows:
        print("[INFO] No rows parsed.")
        if DEBUG:
            print("[DEBUG] Try: DEBUG=1 python3 scripts/ingest/combine_hourly_labour.py to see sheet previews.")
        return

    out = pd.concat(all_rows, ignore_index=True)
    out = out.drop_duplicates(subset=["pc_number","date","hour_range"])
    out.to_csv(OUT_CSV, index=False)
    print("[DONE] Wrote {} rows -> {}".format(len(out), OUT_CSV))

if __name__ == "__main__":
    combine()
