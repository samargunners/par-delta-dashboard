import pandas as pd
from pathlib import Path

raw_path = Path("data/raw/labour")
processed_path = Path("data/processed")
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
labor_df["date"] = pd.to_datetime(labor_df["date"], format="%m/%d/%Y").dt.date
labor_df["pc_number"] = labor_df["pc_number"].astype(str)

labor_df.to_excel(processed_path / "hourly_labor_summary.xlsx", index=False)
print("✅ Saved cleaned hourly labor data to hourly_labor_summary.xlsx")