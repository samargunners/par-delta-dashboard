import pandas as pd
from supabase_client import supabase

def clean_for_supabase(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["pc_number"] = df["pc_number"].astype(str)
    df = df.astype(object).where(pd.notnull(df), None)
    return df

def batch_upsert(df, table_name, batch_size=500):
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"📦 Uploading {total} remaining schedule records in batches of {batch_size}")

    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table(table_name).upsert(batch).execute()
            print(f"✅ Uploaded records {i+1} to {i+len(batch)} to {table_name}")
        except Exception as e:
            print(f"❌ Error uploading records {i+1} to {i+len(batch)}: {e}")

def upload_remaining_schedule(file_path):
    df = pd.read_excel(file_path)
    df = clean_for_supabase(df)

    # Get only the relevant schedule columns
    schedule_cols = ["pc_number", "date", "hour_range", "scheduled_hours"]
    schedule_df = df[schedule_cols]

    # Upload only records from 4562 onward
    remaining_df = schedule_df.iloc[4561:]
    batch_upsert(remaining_df, "schedule_table_labor")

if __name__ == "__main__":
    upload_remaining_schedule("/Users/samarpatel/Desktop/samar/Dunkin/par-delta-dashboard/data/processed/hourly_labor_summary.xlsx")
