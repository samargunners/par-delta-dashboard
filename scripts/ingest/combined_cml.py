
# === formatsales.py ===
import pandas as pd

def transform_donut_sales(filepath):
    # Load raw sales file
    df = pd.read_excel(filepath)

    # Define excluded D-Variety variants
    exclude_keywords = ["Assorted Munchkins", "Blueberry Glazed", "Chocolate", "Glazed 2"]

    # Filter donut-related rows
    donut_mask = (
        df["ProductName"].str.contains("1 Donut", case=False, na=False) |
        df["ProductName"].str.contains("6 Donuts", case=False, na=False) |
        df["ProductName"].str.contains("12 Donuts", case=False, na=False) |
        (
            df["ProductName"].str.contains("D-Variety", case=False, na=False) &
            ~df["ProductName"].str.contains("|".join(exclude_keywords), case=False, na=False)
        )
    )
    df_filtered = df[donut_mask].copy()

    # Assign product type
    df_filtered["ProductType"] = "Donut"

    # Quantity transformation
    def adjust_quantity(row):
        name = row["ProductName"]
        qty = row["Quantity"]
        value = row["Value"]

        if value == 0:
            return 0
        elif "1 Donut" in name:
            return qty * 1
        elif "6 Donuts" in name:
            return qty * 6
        elif "12 Donuts" in name:
            return qty * 12
        elif "D-Variety" in name and not any(exclude.lower() in name.lower() for exclude in exclude_keywords):
            return qty * 1
        return 0  # Catch-all fallback

    df_filtered["Quantity"] = df_filtered.apply(adjust_quantity, axis=1)

    # Split DateTime into Date and Time columns
    df_filtered["Date"] = pd.to_datetime(df_filtered["DateTime"]).dt.date
    df_filtered["Time"] = pd.to_datetime(df_filtered["DateTime"]).dt.time

    # Final selection
    df_formatted = df_filtered[[
        "Date", "Time", "LocationCode", "ProductName", "ProductType", "Quantity", "Value"
    ]].copy()


    return df_formatted

# ===== Main Execution =====
if __name__ == "__main__":
    input_file = "DataStreamExport.xlsx"
    output_file = "DonutSales.xlsx"

    df_result = transform_donut_sales(input_file)
    df_result.to_excel(output_file, index=False)
    print(f"✅ Donut sales file saved as: {output_file}")


# === formatusageoverview.py ===
import pandas as pd

# List of known store names
store_list = [
    "Columbia", "Elizabethtown", "Enola",
    "Lititz", "Marietta", "Mount Joy", "Paxton"
]

# Mapping of store names to location numbers
location_map_updated = {
    "Enola": 357993,
    "Paxton": 301290,
    "Mount Joy": 343939,
    "Columbia": 358529,
    "Lititz": 359042,
    "Marietta": 363271,
    "Elizabethtown": 364322,
}

def transform_usage_overview_with_strict_location_match(filepath):
    # Read Excel file starting after metadata
    df = pd.read_excel(filepath, sheet_name="UsageOverviewReport", skiprows=5)
    df = df.dropna(how='all')  # Remove completely empty rows

    current_store = None
    current_date = None
    records = []

    for _, row in df.iterrows():
        val0 = str(row[0]).strip() if pd.notna(row[0]) else ""

        # Check for store name in current row
        matched_store = next((store for store in store_list if store.lower() in val0.lower()), None)
        if matched_store:
            current_store = matched_store
            continue

        # Check for date in current row
        if "2025" in val0:
            try:
                current_date = pd.to_datetime(val0)
            except:
                continue

        # If it's a known product, extract data
        elif val0 in ["Donuts", "Fancies", "Munchkins"]:
            record = {
                "Location": current_store,
                "Date": current_date,
                "product": val0,
                "Order #": row[1],
                "Waste #": row[2],
                "Waste %": row[3],
                "Waste $": row[4],
                "Expected Consumption": row[5]
            }
            records.append(record)

    # Create final dataframe
    df_final = pd.DataFrame(records)

    # Add location number
    df_final["Location Number"] = df_final["Location"].apply(
        lambda loc: location_map_updated.get(loc, None)
    )

    # Reorder and return
    return df_final[[
        "Location", "Location Number", "Date", "product",
        "Order #", "Waste #", "Waste %", "Waste $", "Expected Consumption"
    ]]

# ===== Main Execution =====
if __name__ == "__main__":
    original_path = "UsageOverview.xlsx"  # Excel file must be in same folder
    output_path = "UsageOverview_Formatted.xlsx"

    df_result = transform_usage_overview_with_strict_location_match(original_path)
    df_result.to_excel(output_path, index=False)
    print(f"✅ File saved as: {output_path}")


# === Original cml.py logic ===
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

