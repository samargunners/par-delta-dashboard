import pandas as pd
from pathlib import Path

# Set file paths
base_path = Path("/Users/samarpatel/desktop/samar/dunkin/par-delta-dashboard/data/raw/supplyit")
usage_path = base_path / "UsageOverview_Formatted.xlsx"
sales_path = base_path / "DonutSales.xlsx"

# Output path
processed_path = Path("/Users/samarpatel/desktop/samar/dunkin/par-delta-dashboard/data/processed")
processed_path.mkdir(parents=True, exist_ok=True)

# === USAGE OVERVIEW CLEANING ===
usage_df = pd.read_excel(usage_path)

# Standardize column names
usage_df.columns = [
    "store_name", "pc_number", "date", "product_type", 
    "ordered_qty", "wasted_qty", "waste_percent", 
    "waste_dollar", "expected_consumption"
]

# Format types
usage_df["date"] = pd.to_datetime(usage_df["date"]).dt.date
usage_df["pc_number"] = usage_df["pc_number"].astype(str)

# Save cleaned version
usage_df.to_excel(processed_path / "cml_usage.xlsx", index=False)
print("✅ Cleaned usage data saved to data/processed/cml_usage.xlsx")

# === DONUT SALES CLEANING ===
sales_df = pd.read_excel(sales_path)

# Standardize column names
sales_df.columns = [
    "date", "time", "pc_number", 
    "product_name", "product_type", "quantity", "value"
]

# Format datetime and types
sales_df["sale_datetime"] = pd.to_datetime(sales_df["date"].astype(str) + " " + sales_df["time"].astype(str))
sales_df["pc_number"] = sales_df["pc_number"].astype(str)

# Reorder and drop original date/time
sales_df = sales_df[[
    "pc_number", "sale_datetime", "product_name", 
    "product_type", "quantity", "value"
]]

# Save cleaned version
sales_df.to_excel(processed_path / "donut_sales.xlsx", index=False)
print("✅ Cleaned sales data saved to data/processed/donut_sales.xlsx")
