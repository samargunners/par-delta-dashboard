import pandas as pd
from scripts.upload.supabase_client import supabase

def upload_dataframe(df, table_name, batch_size=500):
    df = df.copy()

    # Convert datetime to string for JSON serialization
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].astype(str)

    data = df.to_dict(orient="records")

    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i + batch_size]
        supabase.table(table_name).insert(batch).execute()
        print(f"✅ Uploaded {i + len(batch)} / {total} rows to {table_name}")

    print(f"✅ Finished uploading to {table_name}: {total} rows")


# === Get store_id mapping from Supabase using pc_number ===
store_map = supabase.table("stores").select("store_id, pc_number").execute()
store_lookup = {str(entry["pc_number"]): entry["store_id"] for entry in store_map.data}

# === Upload Usage Overview ===
usage_df = pd.read_excel("data/processed/cml_usage.xlsx")

# Map pc_number to store_id
usage_df["store_id"] = usage_df["store_id"].astype(str).map(store_lookup)

# Reorder and keep required columns
usage_df = usage_df[[
    "store_id", "date", "product_type",
    "ordered_qty", "wasted_qty", "waste_percent",
    "waste_dollar", "expected_consumption"
]]

upload_dataframe(usage_df, "usage_overview")

# === Upload Donut Sales ===
sales_df = pd.read_excel("data/processed/donut_sales.xlsx")

# Map pc_number to store_id
sales_df["store_id"] = sales_df["store_id"].astype(str).map(store_lookup)

# Reorder and keep required columns
sales_df = sales_df[[
    "store_id", "sale_datetime", "product_name",
    "product_type", "quantity", "value"
]]

upload_dataframe(sales_df, "donut_sales_hourly")