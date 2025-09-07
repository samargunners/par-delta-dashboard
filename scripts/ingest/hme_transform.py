import re
from datetime import datetime
import pandas as pd
import numpy as np

def parse_hme_to_desired(hme_path: str) -> pd.DataFrame:
    xls = pd.ExcelFile(hme_path)
    df = pd.read_excel(xls, sheet_name="Paginated Summary Multi Store R")

    # ---- Extract the date ("Day: mm/dd/yyyy") anywhere in the sheet ----
    date_val = None
    for col in df.columns:
        for val in df[col].astype(str).fillna(""):
            m = re.search(r"Day:\s*(\d{2}/\d{2}/\d{4})", val)
            if m:
                date_val = datetime.strptime(m.group(1), "%m/%d/%Y").date()
                break
        if date_val:
            break

    # ---- Find the header row (the one containing "Time Measure") ----
    header_row_idx = None
    for i in range(len(df)):
        if (df.iloc[i] == "Time Measure").any():
            header_row_idx = i
            break
    if header_row_idx is None:
        raise RuntimeError("Could not find 'Time Measure' header row.")

    header_row = df.iloc[header_row_idx]
    tm_matches = np.where(header_row.values == "Time Measure")[0]
    if len(tm_matches) == 0:
        raise RuntimeError("Could not locate 'Time Measure' column index.")
    time_measure_col = int(tm_matches[0])

    # ---- Map the columns we care about to their indices ----
    wanted = {
        "Total Cars": "Total Cars",
        "Menu Board": "Menu Board",
        "Greet": "Greet",
        "Menu 1": "Menu 1",
        "Greet 1": "Greet 1",
        "Menu 2": "Menu 2",
        "Greet 2": "Greet 2",
        "Service": "service",
        "Lane Queue": "lane_queue",
        "Lane Total": "lane_total",
    }
    idx_map = {}
    for j, v in enumerate(header_row):
        if isinstance(v, str) and v in wanted:
            idx_map[wanted[v]] = j

    records = []
    current_store = None

    for r in range(header_row_idx + 1, len(df)):
        row = df.iloc[r]
        if pd.isna(row).all():
            continue

        # Store appears once per block; keep the last seen
        v0 = row.iloc[0]
        if isinstance(v0, str) and v0.strip():
            current_store = v0.strip()

        time_measure = row.iloc[time_measure_col]
        if pd.isna(time_measure) or not current_store:
            continue

        def get_val(key):
            j = idx_map.get(key)
            if j is None:
                return None
            v = row.iloc[j]
            try:
                return float(v)
            except Exception:
                return pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]

        rec = {
            "Date": pd.to_datetime(date_val),
            "store": current_store,
            "time_measure": str(time_measure),
            "Total Cars": get_val("Total Cars"),
            "Menu Board": get_val("Menu Board"),
            "Greet": get_val("Greet"),
            "Menu 1": get_val("Menu 1"),
            "Greet 1": get_val("Greet 1"),
            "Menu 2": get_val("Menu 2"),
            "Greet 2": get_val("Greet 2"),
            "service": get_val("service"),
            "lane_queue": get_val("lane_queue"),
            "lane_total": get_val("lane_total"),
        }

        # Your rules:
        rec["menu_all"]  = rec["Menu Board"] if pd.notna(rec["Menu Board"]) else rec["Menu 1"]
        rec["greet_all"] = rec["Greet"]      if pd.notna(rec["Greet"])      else rec["Greet 1"]

        records.append(rec)

    out = pd.DataFrame.from_records(records)
    final_cols = [
        "Date","store","time_measure","Total Cars","menu_all","greet_all",
        "Menu Board","Greet","Menu 1","Greet 1","Menu 2","Greet 2",
        "service","lane_queue","lane_total",
    ]
    return out[final_cols]

if __name__ == "__main__":
    import argparse, os
    parser = argparse.ArgumentParser(description="Transform HME report to Supabase-ready format.")
    parser.add_argument("input", help="Path to HME Excel (e.g., hme_report.xlsx)")
    parser.add_argument("--csv",  default="hme_transformed.csv",  help="Output CSV path")
    parser.add_argument("--xlsx", default="hme_transformed.xlsx", help="Output XLSX path")
    args = parser.parse_args()

    df_out = parse_hme_to_desired(args.input)
    df_out.to_csv(args.csv, index=False)
    df_out.to_excel(args.xlsx, index=False)
    print(f"[OK] Wrote {len(df_out)} rows to:\n- {os.path.abspath(args.csv)}\n- {os.path.abspath(args.xlsx)}")




    # --- Optional: upload to Supabase ---
    # pip install supabase
    from supabase import create_client
    import os, math

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # use service role for server scripts
    TABLE_NAME   = os.getenv("SUPABASE_TABLE", "hme_dayparts")

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # convert timestamps and NaNs for Supabase
    payload = df_out.where(pd.notnull(df_out), None).to_dict(orient="records")

    # upsert or insert in chunks
    chunk = 500
    for i in range(0, len(payload), chunk):
        batch = payload[i:i+chunk]
        # .upsert(batch, on_conflict="store,Date,time_measure")  # if you set a unique index
        res = supabase.table(TABLE_NAME).insert(batch).execute()
        if res.data is None and res.count == 0:
            print("[WARN] Insert returned no data; check RLS/policies.")
    print("[OK] Uploaded to Supabase:", TABLE_NAME)


