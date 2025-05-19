import pandas as pd
from pathlib import Path

def transform_variance_report(input_file, output_file):
    # Step 1: Load raw Excel file (no header)
    df_raw = pd.read_excel(input_file, header=None)

    # Step 2: Extract reporting period from row 4
    reporting_period_raw = df_raw.iloc[3, 0]
    reporting_period = reporting_period_raw.split(":", maxsplit=2)[-1].strip()

    # Step 3: Flatten headers from row 6 and 7
    header_row_1 = df_raw.iloc[5].fillna(method="ffill")
    header_row_2 = df_raw.iloc[6]
    flattened_headers = [
        f"{loc.strip()}__{metric.strip()}" if pd.notna(loc) and pd.notna(metric) else metric
        for loc, metric in zip(header_row_1, header_row_2)
    ]

    # Step 4: Create DataFrame from actual data (starting row 8)
    df = df_raw.iloc[7:].copy()
    df.columns = flattened_headers
    df["reporting_period"] = reporting_period

    # Step 5: Rename first 3 columns to base fields
    df.columns.values[0] = "Subcategory"
    df.columns.values[1] = "Product Name"
    df.columns.values[2] = "Inventory Unit"

    # ✅ Step 5.1: Remove rows where Inventory Unit contains 'total'
    df = df[~df["Inventory Unit"].astype(str).str.lower().str.contains("total")]

    # Step 6: Identify base columns and value columns
    base_cols = ["reporting_period", "Subcategory", "Product Name", "Inventory Unit"]
    value_cols = [col for col in df.columns if isinstance(col, str) and "__" in col]

    # Step 7: Melt into long format
    df_melted = df.melt(
        id_vars=base_cols,
        value_vars=value_cols,
        var_name="Location_Metric",
        value_name="Value"
    )

    # Step 8: Extract location name and metric
    df_melted[["location_name", "metric"]] = df_melted["Location_Metric"].str.split("__", expand=True)

    # Step 9: Extract PC number from location name
    df_melted["pc_number"] = df_melted["location_name"].str.split(" - ").str[0]

    # Step 10: Pivot to get formatted table
    df_pivot = df_melted.pivot_table(
        index=["reporting_period", "Subcategory", "Product Name", "Inventory Unit", "pc_number"],
        columns="metric",
        values="Value",
        aggfunc="first"
    ).reset_index()

    df_pivot.columns.name = None

    # Step 11: Export to Excel
    df_pivot.to_excel(output_file, index=False)
    print(f"✅ Saved formatted variance report to: {output_file}")

# Example usage
if __name__ == "__main__":
    input_path = Path("data/raw/crunchtime/variance_report.xlsx")
    output_path = Path("data/processed/formatted_variance_report.xlsx")
    transform_variance_report(input_path, output_path)
