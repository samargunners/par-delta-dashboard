import pandas as pd
from supabase import create_client

# === SETUP ===
SUPABASE_URL = "https://ertcdieopoecjddamgkx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVydGNkaWVvcG9lY2pkZGFtZ2t4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU5Nzk5NzUsImV4cCI6MjA2MTU1NTk3NX0.luonNX2zmRAYou1303uKht2p9nwBPDHd62_P0k2DmkY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def prepare_labor_data(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Replace '-- or '–' strings with NaN
    df.replace(to_replace=["--", "'--", "’--", "–", "'–", "—"], value=pd.NA, inplace=True)

    # Convert all expected numeric columns
    numeric_cols = [
        "forecasted_checks", "forecasted_sales", "ideal_hours", "scheduled_hours",
        "actual_hours", "actual_labor", "sales_value", "check_count", "sales_per_labor_hour"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Ensure proper types
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["pc_number"] = df["pc_number"].astype(str)

    return df


def full_replace_by_date(file_path, table_name="hourly_labor_summary"):
    df = prepare_labor_data(file_path)

    # Get all unique dates in the Excel sheet
    unique_dates = df["date"].unique().tolist()

    print(f"🗑 Deleting existing records for dates: {unique_dates}")

    # Delete existing records for each date
    for date_str in unique_dates:
        try:
            supabase.table(table_name).delete().eq("date", date_str).execute()
            print(f"✅ Deleted records for {date_str}")
        except Exception as e:
            print(f"❌ Error deleting records for {date_str}: {e}")

    # Clean data
    df = df.where(pd.notnull(df), None)
    records = df.to_dict(orient="records")

    # Upload new records
    print(f"📤 Uploading {len(records)} new records to Supabase...")
    for i, record in enumerate(records):
        try:
            supabase.table(table_name).upsert(record).execute()
        except Exception as e:
            print(f"❌ Error uploading record {i+1}: {e}")
            continue

full_replace_by_date("hourly_labor_summary.xlsx")