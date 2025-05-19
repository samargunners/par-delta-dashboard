
import pandas as pd
from scripts.upload.supabase_client import supabase

# Helper function to upload a DataFrame to a Supabase table
def upload_dataframe(df, table_name):
    data = df.to_dict(orient="records")
    for record in data:
        supabase.table(table_name).insert(record).execute()
    print(f"✅ Uploaded to {table_name}: {len(data)} rows")

# === Upload Usage Overview ===
usage_df = pd.read_excel("data/processed/cml_usage.xlsx")

product_type_map = {"Donuts": 1, "Fancies": 2, "Munchkins": 3}
usage_df["product_type_id"] = usage_df["product_type"].map(product_type_map)

usage_df = usage_df[[
    "store_id", "date", "product_type_id", 
    "ordered_qty", "wasted_qty", "waste_percent", 
    "waste_dollar", "expected_consumption"
]]

upload_dataframe(usage_df, "usage_overview")

# === Upload Donut Sales ===
sales_df = pd.read_excel("data/processed/donut_sales.xlsx")

product_type_map = {"Donut": 1, "Fancy": 2, "Munchkin": 3}
sales_df["product_type_id"] = sales_df["product_type"].map(product_type_map)

sales_df = sales_df[[
    "store_id", "sale_datetime", "product_name", 
    "product_type_id", "quantity", "value"
]]

upload_dataframe(sales_df, "donut_sales_hourly")
