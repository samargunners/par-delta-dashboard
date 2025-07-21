import pandas as pd
import os
from pathlib import Path
from supabase_client import supabase

def get_latest_date(table_name, date_col):
    result = supabase.table(table_name).select(date_col).order(date_col, desc=True).limit(1).execute()
    if result.data:
        return result.data[0][date_col]
    return None

def upload_dataframe_after_date(df, table_name, date_col, batch_size=500):
    df = df.copy()
    # Convert datetime to string for Supabase JSON compatibility
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].astype(str)

    latest_date = get_latest_date(table_name, date_col)
    if latest_date:
        df = df[df[date_col] > latest_date]

    if df.empty:
        print(f"✅ No new rows to upload to {table_name}")
        return

    data = df.to_dict(orient="records")
    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]
        supabase.table(table_name).insert(batch).execute()
        print(f"✅ Uploaded {i + len(batch)} / {total} new rows to {table_name}")

    print(f"✅ Finished uploading to {table_name}: {total} new rows")


# Get the project root directory (2 levels up from current script location)
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent

# === Upload CML Usage Overview ===
cml_usage_path = project_root / "data" / "processed" / "cml_usage.xlsx"
print(f"📁 Reading CML usage file from: {cml_usage_path}")
usage_df = pd.read_excel(cml_usage_path)

if "pc_number" not in usage_df.columns:
    raise ValueError("❌ 'pc_number' column missing in cml_usage.xlsx")

usage_df["pc_number"] = usage_df["pc_number"].astype(str)  # Ensure varchar
usage_df["date"] = pd.to_datetime(usage_df["date"]).dt.strftime("%Y-%m-%d")  # Ensure string date

usage_df = usage_df[[
    "pc_number", "date", "product_type",
    "ordered_qty", "wasted_qty", "waste_percent",
    "waste_dollar", "expected_consumption"
]]

upload_dataframe_after_date(usage_df, "usage_overview", "date")


# === Upload Donut Sales Hourly ===
donut_sales_path = project_root / "data" / "processed" / "donut_sales.xlsx"
print(f"📁 Reading Donut sales file from: {donut_sales_path}")
sales_df = pd.read_excel(donut_sales_path)

if "pc_number" not in sales_df.columns:
    raise ValueError("❌ 'pc_number' column missing in donut_sales.xlsx")

sales_df["pc_number"] = sales_df["pc_number"].astype(str)  # Ensure varchar for consistency
sales_df["sale_datetime"] = pd.to_datetime(sales_df["sale_datetime"])
sales_df["date"] = sales_df["sale_datetime"].dt.strftime("%Y-%m-%d")  # Ensure string date
sales_df["time"] = sales_df["sale_datetime"].dt.time.astype(str)

sales_df = sales_df[[
    "pc_number", "date", "time", "product_name",
    "product_type", "quantity", "value"
]]

upload_dataframe_after_date(sales_df, "donut_sales_hourly", "date")
