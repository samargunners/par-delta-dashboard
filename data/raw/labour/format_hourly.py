import pandas as pd

# === Step 1: Load the Excel File ===
file_path = "ideal Hourly Sales & Labour Prompted.xlsx"
df = pd.read_excel(file_path, header=[2, 3])  # Header is on row 3 (index 2)

# === Step 2: Flatten MultiIndex Columns ===
df.columns = [f"{col[0]}__{col[1]}" for col in df.columns]

# === Step 3: Identify Date & Interval Columns ===
date_col = next((col for col in df.columns if "Date" in col), None)
interval_col = next((col for col in df.columns if "Minute Interval" in col), None)

if not date_col or not interval_col:
    raise ValueError("Could not find 'Date' or '60 Minute Interval' columns.")

# === Step 4: Remove Rows Where Interval Contains 'Total' ===
df = df[~df[interval_col].astype(str).str.contains("Total", case=False, na=False)]

# === Step 5: Prepare for Melting ===
id_vars = [date_col, interval_col]
value_vars = [col for col in df.columns if col not in id_vars and "Total" not in col]

# === Step 6: Melt to Long Format ===
df_melted = df.melt(
    id_vars=id_vars,
    value_vars=value_vars,
    var_name="Store_Metric",
    value_name="Value"
)

# === ✅ Step 6.5: Clean '--' values ===
df_melted["Value"] = df_melted["Value"].replace(['--', '—', '–', '―', '‑', '‒', '−'], 0)
df_melted["Value"] = pd.to_numeric(df_melted["Value"], errors="coerce").fillna(0)

# === Step 7: Extract Store Code & Metric from Flattened Column ===
df_melted[["Location Code", "Metric"]] = df_melted["Store_Metric"].str.split("__", expand=True)

# === Step 8: Rename Date & Interval for Clarity ===
df_melted = df_melted.rename(columns={
    date_col: "Date",
    interval_col: "Interval"
})

# === Step 9: Pivot to Get Metrics as Columns ===
df_final = df_melted.pivot_table(
    index=["Location Code", "Date", "Interval"],
    columns="Metric",
    values="Value",
    aggfunc="first"
).reset_index()

# === Step 10: Reorder Columns (if present) ===
desired_order = [
    "Location Code", "Date", "Interval",
    "Forecasted Checks", "Forecasted Sales", "Ideal Hours", "Scheduled Hours",
    "Actual Hours", "Actual Labor", "Sales", "Check Count",
    "Total Labor Value as % of Sales", "Sales / Labor Hour - MM"
]
final_columns = [col for col in desired_order if col in df_final.columns]
df_final = df_final[final_columns]

# Format the Date column as MM/DD/YY
df_final["Date"] = pd.to_datetime(df_final["Date"]).dt.strftime("%m/%d/%y")

# === Step 11: Save to Excel ===
output_file = "cleaned_labour_sales_data.xlsx"
df_final.to_excel(output_file, index=False)
print(f"✅ Cleaned data saved to '{output_file}'")
