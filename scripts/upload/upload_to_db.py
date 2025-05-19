import pandas as pd
from scripts.upload.supabase_client import supabase

def upload_dataframe(df, table_name, batch_size=500):
    df = df.copy()

    # Convert datetime to string for Supabase JSON compatibility
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].astype(str)

    data = df.to_dict(orient="records")

    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]
        supabase.table(table_name).insert(batch).execute()
        print(f"✅ Uploaded {i + len(batch)} / {total} rows to {table_name}")

    print(f"✅ Finished uploading to {table_name}: {total} rows")


# === Upload CML Usage Overview ===
usage_df = pd.read_excel("data/processed/cml_usage.xlsx")

# Ensure pc_number exists and is string
if "pc_number" not in usage_df.columns:
    raise ValueError("❌ 'pc_number' column missing in cml_usage.xlsx")

usage_df["pc_number"] = usage_df["pc_number"].astype(str)

# Select and reorder columns
usage_df = usage_df[[
    "pc_number", "date", "product_type",
    "ordered_qty", "wasted_qty", "waste_percent",
    "waste_dollar", "expected_consumption"
]]

upload_dataframe(usage_df, "usage_overview")


# === Upload Donut Sales Hourly ===
sales_df = pd.read_excel("data/processed/donut_sales.xlsx")

if "pc_number" not in sales_df.columns:
    raise ValueError("❌ 'pc_number' column missing in donut_sales.xlsx")

sales_df["pc_number"] = sales_df["pc_number"].astype(str)

sales_df = sales_df[[
    "pc_number", "sale_datetime", "product_name",
    "product_type", "quantity", "value"
]]

upload_dataframe(sales_df, "donut_sales_hourly")
