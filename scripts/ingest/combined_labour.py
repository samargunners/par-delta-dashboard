
# === dataclean.py ===
import pandas as pd
import os
import re
from datetime import datetime
from pathlib import Path

# ---------- 1. CLEAN SCHEDULE FILES (TXT) ----------
def clean_schedule_file(file_path):
    df = pd.read_csv(file_path, header=None)
    df.columns = ['RowNumber', 'EmployeeID', 'StartDateTime', 'EndDateTime', 'TimeFormat', 'Unknown']

    # Remove quotes and parse datetime
    df['StartDateTime'] = pd.to_datetime(df['StartDateTime'].str.replace('"', ''), format="%H:%M %m-%d-%y", errors='coerce')
    df['EndDateTime'] = pd.to_datetime(df['EndDateTime'].str.replace('"', ''), format="%H:%M %m-%d-%y", errors='coerce')

    # Split into Date, StartTime, EndTime
    df['Date'] = df['StartDateTime'].dt.date
    df['StartTime'] = df['StartDateTime'].dt.time
    df['EndTime'] = df['EndDateTime'].dt.time

    return df[['EmployeeID', 'Date', 'StartTime', 'EndTime']]


def clean_all_schedule_files(schedule_folder):
    all_dfs = []
    files_found = os.listdir(schedule_folder)
    print(f"📂 Found files: {files_found}")

    for file in files_found:
        if file.endswith(".txt"):
            file_path = os.path.join(schedule_folder, file)
            print(f"🧼 Cleaning schedule file: {file}")
            cleaned_df = clean_schedule_file(file_path)
            all_dfs.append(cleaned_df)

    if not all_dfs:
        raise ValueError("❌ No TXT schedule files found!")
    return pd.concat(all_dfs, ignore_index=True)

# ---------- 2. CLEAN CONSOLIDATED TIME FILE ----------
def parse_name(name_line):
    name_line = name_line.strip()

    # (M) Minor employee
    if name_line.startswith("(M)"):
        match = re.match(r"\(M\) ([^,]+), ([^ -]+) - (\d+)", name_line)
        if match:
            last, first, emp_id = match.groups()
            return f"(M) {first} {last}", emp_id

    # Hyphenated last name
    match = re.match(r"([^,]+), ([^ -]+) - (\d+)", name_line)
    if match:
        last, first, emp_id = match.groups()
        return f"{first} {last}", emp_id

    return None, None

def clean_consolidated_time_file(file_path):
    df_raw = pd.read_csv(file_path, skiprows=4, header=None)

    current_name, current_id = None, None
    clean_rows = []

    for _, row in df_raw.iterrows():
        first_col = str(row[0]).strip()

        if "-" in first_col and "," in first_col and len(first_col.split()) <= 5:
            parsed_name, parsed_id = parse_name(first_col)
            if parsed_name:
                current_name = parsed_name
                current_id = parsed_id
            continue

        if "totals" in first_col.lower():
            continue

        row_data = [current_name, current_id] + row.tolist()
        clean_rows.append(row_data)

    cleaned_df = pd.DataFrame(clean_rows)
    cleaned_df.columns = [
        "EmployeeName", "EmployeeID", "Date", "Location", "TimeIn", "TimeOut", "TotalTime",
        "PositionCode", "Rate", "RegularHours", "RegularWages",
        "OTHours", "OTWages", "TotalWages", "Sales", "Blank1", "Tips", "Blank2", "TipPool", "LastEdit"
    ]

    cleaned_df = cleaned_df[[
        "EmployeeName", "EmployeeID", "Date", "Location", "TimeIn", "TimeOut", "TotalTime",
        "Rate", "RegularHours", "RegularWages", "OTHours", "OTWages", "TotalWages"
    ]]

    # Extract Location Code (first 6-digit number)
    cleaned_df["Location Code"] = cleaned_df["Location"].str.extract(r'(\d{6})')

    cleaned_df = cleaned_df[[
        "EmployeeName", "EmployeeID", "Date", "Location", "Location Code", "TimeIn", "TimeOut",
        "TotalTime", "Rate", "RegularHours", "RegularWages", "OTHours", "OTWages", "TotalWages"
    ]]

    return cleaned_df

# ---------- 3. MAIN ----------
if __name__ == "__main__":
    # Get the project root directory (2 levels up from this script)
    script_dir = Path(__file__).parent  # scripts/ingest/
    project_root = script_dir.parent.parent  # project root
    
    main_folder = project_root / "data" / "raw" / "labour"
    schedule_folder = main_folder / "Schedules"  # Note: capital S as shown in your tree
    consolidated_file = main_folder / "consolidated_time.csv"

    # Process schedule TXT files
    print("📅 Cleaning schedule files...")
    cleaned_schedule_df = clean_all_schedule_files(str(schedule_folder))
    cleaned_schedule_df.to_excel(main_folder / "cleaned_all_schedules.xlsx", index=False)

    # Process consolidated time file
    print("🧾 Cleaning consolidated time file...")
    cleaned_time_df = clean_consolidated_time_file(str(consolidated_file))
    cleaned_time_df.to_excel(main_folder / "cleaned_consolidated_time.xlsx", index=False)

    print("✅ All cleaned files saved to:", main_folder)


# === format_hourly.py ===
import pandas as pd

def format_hourly_data(project_root):
    # === Step 1: Load the Excel File ===
    file_path = project_root / "data" / "raw" / "labour" / "ideal Hourly Sales & Labour Prompted.xlsx"
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
    output_file = project_root / "data" / "raw" / "labour" / "cleaned_labour_sales_data.xlsx"
    df_final.to_excel(output_file, index=False)
    print(f"✅ Cleaned data saved to '{output_file}'")
    
    return df_final


# === Original labour.py logic ===
def process_final_data(project_root):
    raw_path = project_root / "data" / "raw" / "labour"
    processed_path = project_root / "data" / "processed"
    processed_path.mkdir(parents=True, exist_ok=True)

    # === CLOCKINS ===
    clockins_df = pd.read_excel(raw_path / "cleaned_consolidated_time.xlsx", skiprows=1)
    clockins_df.columns = [
        "employee_name", "employee_id", "date", "location_name", "pc_number", 
        "time_in", "time_out", "total_time", "rate", 
        "regular_hours", "regular_wages", "ot_hours", "ot_wages", "total_wages"
    ]
    clockins_df["date"] = pd.to_datetime(clockins_df["date"], errors="coerce").dt.date
    clockins_df = clockins_df.dropna(subset=["pc_number"])
    clockins_df["pc_number"] = clockins_df["pc_number"].astype(float).astype(int).astype(str)

    # Replace None, NaN, and empty strings with 0
    clockins_df = clockins_df.replace(r'^\s*$', 0, regex=True)  # Replace blank strings with 0
    clockins_df = clockins_df.fillna(0)  # Replace NaN/None with 0

    clockins_df.to_excel(processed_path / "employee_clockin.xlsx", index=False)
    print("✅ Saved cleaned clockins to employee_clockin.xlsx")

    # === SCHEDULES ===
    schedules_df = pd.read_excel(raw_path / "cleaned_all_schedules.xlsx", skiprows=1)
    schedules_df.columns = ["employee_id", "date", "start_time", "end_time"]
    schedules_df["date"] = pd.to_datetime(schedules_df["date"]).dt.date
    schedules_df["employee_id"] = schedules_df["employee_id"].astype(str)

    schedules_df.to_excel(processed_path / "employee_schedules.xlsx", index=False)
    print("✅ Saved cleaned schedules to employee_schedules.xlsx")

    # === HOURLY LABOR SUMMARY ===
    labor_df = pd.read_excel(raw_path / "cleaned_labour_sales_data.xlsx", skiprows=1)
    labor_df.columns = [
        "pc_number", "date", "hour_range", "forecasted_checks", "forecasted_sales",
        "ideal_hours", "scheduled_hours", "actual_hours", "actual_labor",
        "sales_value", "check_count", "sales_per_labor_hour"
    ]
    # Option 1: Allow 2-digit year parsing
    labor_df["date"] = pd.to_datetime(labor_df["date"], format="%m/%d/%y").dt.date
    labor_df["pc_number"] = labor_df["pc_number"].astype(str)

    labor_df.to_excel(processed_path / "hourly_labor_summary.xlsx", index=False)
    print("✅ Saved cleaned hourly labor data to hourly_labor_summary.xlsx")

# === MAIN EXECUTION ===
if __name__ == "__main__":
    # Get the project root directory (2 levels up from this script)
    script_dir = Path(__file__).parent  # scripts/ingest/
    project_root = script_dir.parent.parent  # project root
    
    print("🚀 Starting combined labour processing...")
    print(f"📁 Project root: {project_root}")
    
    try:
        # Step 1: Format hourly data if Excel file exists
        hourly_file = project_root / "data" / "raw" / "labour" / "ideal Hourly Sales & Labour Prompted.xlsx"
        if hourly_file.exists():
            print("📊 Processing hourly labor data...")
            format_hourly_data(project_root)
        else:
            print(f"⚠️  Hourly file not found: {hourly_file}")
    
        # Step 2: Process final data
        print("🔄 Processing final cleaned data...")
        process_final_data(project_root)
        
        print("✅ All labour processing completed successfully!")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        raise

