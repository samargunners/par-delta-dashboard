import pandas as pd
from supabase_client import supabase  # local import

def upload_dataframe(df, table_name):
    df.replace(to_replace=["--", "'--"], value=0, inplace=True)

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].astype(str).replace("NaT", None).replace("nan", None)
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
            supabase.table(table_name).upsert(record).execute()
        except Exception as e:
            print(f"❌ Error upserting record {i+1}: {e}")
            print("⛔ Record content:", record)
            break

# === Upload Variance Report Summary
df = pd.read_excel("data/processed/formatted_variance_report.xlsx")
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df["pc_number"] = df["pc_number"].astype(str)

upload_dataframe(df, "variance_report_summary")