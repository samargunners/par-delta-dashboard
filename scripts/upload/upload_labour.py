import pandas as pd
from supabase_client import supabase  # local import

def upload_dataframe(df, table_name):
    df.replace(to_replace=["--", "'--"], value=0, inplace=True)

    # Convert datetime/time columns to string
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].astype(str).replace("NaT", None).replace("nan", None)

    # Clean up space-only and blank strings in object columns
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].replace(r'^\\s*$', None, regex=True)

    df = df.where(pd.notnull(df), None)

    data = df.to_dict(orient="records")

    filtered_data = [
        record for record in data
        if record and any(str(val).strip().lower() not in ["", "none", "nat", "nan"] for val in record.values())
    ]

    print(f"✅ Prepared {len(filtered_data)} records for upsert to {table_name}")

    for i, record in enumerate(filtered_data):
        try:
            print(f"📤 UPSERT record {i+1}/{len(filtered_data)}: {record}")
            supabase.table(table_name).upsert(record).execute()
        except Exception as e:
            print(f"❌ Error upserting record {i+1}: {e}")
            print("⛔ Record content:", record)
            break

# === Upload Employee Clockins (using pc_number)
clockins_df = pd.read_excel("data/processed/employee_clockins.xlsx")
clockins_df.columns = clockins_df.columns.str.strip().str.lower().str.replace(" ", "_")
clockins_df["pc_number"] = clockins_df["pc_number"].astype(str)

clockins_df = clockins_df[[
    "employee_id", "employee_name", "pc_number", "date", 
    "time_in", "time_out", "total_time", "rate", 
    "regular_hours", "regular_wages", 
    "ot_hours", "ot_wages", "total_wages"
]]
upload_dataframe(clockins_df, "employee_clockins")

# === Upload Employee Schedules
schedules_df = pd.read_excel("data/processed/employee_schedules.xlsx")
schedules_df.columns = schedules_df.columns.str.strip().str.lower().str.replace(" ", "_")
schedules_df = schedules_df[["employee_id", "date", "start_time", "end_time"]]
upload_dataframe(schedules_df, "employee_schedules")

# === Upload Hourly Labor Summary (using pc_number)
labor_df = pd.read_excel("data/processed/hourly_labor_summary.xlsx")
labor_df.columns = labor_df.columns.str.strip().str.lower().str.replace(" ", "_")
labor_df["pc_number"] = labor_df["pc_number"].astype(str)

upload_dataframe(labor_df, "hourly_labor_summary")