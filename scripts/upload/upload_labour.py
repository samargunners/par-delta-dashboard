import pandas as pd
from datetime import datetime, timedelta
from supabase_client import supabase  # Your working Supabase connection

def get_reporting_weeks(reference_date=None):
    """Returns start/end dates for last, current, and next week (Monday-Sunday)."""
    today = reference_date or datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    last_week = start_of_week - timedelta(days=7)
    next_week = start_of_week + timedelta(days=7)

    return {
        "last": (last_week, last_week + timedelta(days=6)),
        "current": (start_of_week, start_of_week + timedelta(days=6)),
        "next": (next_week, next_week + timedelta(days=6)),
    }

def clean_dataframe(df):
    df.replace(to_replace=["--", "'--", "’--", "–", "'–", "—"], value=pd.NA, inplace=True)

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].astype(str).replace("NaT", None).replace("nan", None)
        elif df[col].dtype == "object":
            df[col] = df[col].replace(r'^\s*$', None, regex=True)
        elif pd.api.types.is_numeric_dtype(df[col]):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.where(pd.notnull(df), None)
    return df

def upsert_dataframe(df, table_name):
    records = df.to_dict(orient="records")
    print(f"✅ Prepared {len(records)} records for upsert to {table_name}")

    for i, record in enumerate(records):
        try:
            supabase.table(table_name).upsert(record).execute()
        except Exception as e:
            print(f"❌ Error upserting record {i+1}: {e}")
            continue

def upload_labor_data_weekly(file_path):
    labor_df = pd.read_excel(file_path)
    labor_df.columns = labor_df.columns.str.strip().str.lower().str.replace(" ", "_")
    labor_df["date"] = pd.to_datetime(labor_df["date"])
    labor_df["pc_number"] = labor_df["pc_number"].astype(str)

    weeks = get_reporting_weeks()
    update_fields = ["scheduled_hours", "actual_hours", "actual_labor", "sales_value", "check_count", "sales_per_labor_hour"]

    for label, (start_date, end_date) in weeks.items():
        week_df = labor_df[(labor_df["date"] >= start_date) & (labor_df["date"] <= end_date)].copy()

        if label == "last":
            # Fully clean and upload last week's data (overwrite allowed)
            week_df["date"] = week_df["date"].dt.strftime("%Y-%m-%d")
            cleaned = clean_dataframe(week_df)
            upsert_dataframe(cleaned, "hourly_labor_summary")
        else:
            # Clean but only upload if existing record is missing or 0 — partial fill
            week_df["date"] = week_df["date"].dt.strftime("%Y-%m-%d")
            cleaned = clean_dataframe(week_df)

            response = supabase.table("hourly_labor_summary") \
                .select("*") \
                .gte("date", start_date.strftime("%Y-%m-%d")) \
                .lte("date", end_date.strftime("%Y-%m-%d")) \
                .execute()
            existing_df = pd.DataFrame(response.data)

            if not existing_df.empty:
                merged = pd.merge(
                    cleaned,
                    existing_df,
                    on=["pc_number", "date", "hour_range"],
                    suffixes=("", "_existing"),
                    how="left"
                )

                for field in update_fields:
                    existing_field = f"{field}_existing"
                    merged[field] = merged.apply(
                        lambda row: row[field] if pd.isna(row[existing_field]) or row[existing_field] == 0 else row[existing_field],
                        axis=1
                    )

                final_df = merged[cleaned.columns]
            else:
                final_df = cleaned

            upsert_dataframe(final_df, "hourly_labor_summary")

# === Usage ===
upload_labor_data_weekly("data/processed/hourly_labor_summary.xlsx")

