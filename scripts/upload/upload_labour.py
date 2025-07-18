import pandas as pd
import os
from datetime import datetime, timedelta
from supabase_client import supabase

# === Clean and prepare DataFrame ===
def clean_for_supabase(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["pc_number"] = df["pc_number"].astype(str)
    df = df.astype(object).where(pd.notnull(df), None)
    return df

# === Batched upsert ===
def batch_upsert(df, table_name, batch_size=500):
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"\n📦 Uploading {total} records to '{table_name}' in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table(table_name).upsert(batch).execute()
            print(f"✅ Uploaded records {i+1} to {i+len(batch)}")
        except Exception as e:
            print(f"❌ Error uploading records {i+1} to {i+len(batch)}: {e}")

# === Main upload function ===
def upload_cleaned_labor_data(file_path):
    df = pd.read_excel(file_path)
    df = clean_for_supabase(df)

    # Define table-specific column sets
    ideal_cols = ["pc_number", "date", "hour_range", "forecasted_checks", "forecasted_sales", "ideal_hours"]
    schedule_cols = ["pc_number", "date", "hour_range", "scheduled_hours"]
    actual_cols = [
        "pc_number", "date", "hour_range",
        "actual_hours", "actual_labor", "sales_value",
        "check_count", "sales_per_labor_hour"
    ]

    # Subset DataFrames
    ideal_df = df[ideal_cols]
    schedule_df = df[schedule_cols]
    actual_df = df[actual_cols]

    # Batched uploads
    batch_upsert(ideal_df, "ideal_table_labor")
    batch_upsert(schedule_df, "schedule_table_labor")
    batch_upsert(actual_df, "actual_table_labor")

# === Entry point ===
if __name__ == "__main__":
    # Get the project root directory (par-delta-dashboard)
    script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts/upload/
    project_root = os.path.dirname(os.path.dirname(script_dir))  # par-delta-dashboard/
    file_path = os.path.join(project_root, "data", "processed", "hourly_labor_summary.xlsx")
    
    print(f"📁 Reading file from: {file_path}")
    upload_cleaned_labor_data(file_path)
