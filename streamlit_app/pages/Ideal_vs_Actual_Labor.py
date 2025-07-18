import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Ideal vs Actual Labor", layout="wide")
st.title("💼 Ideal vs Actual Labor")

# --- Filters ---
location_filter = st.selectbox("Select Store", ["All"] + [
    "301290", "357993", "343939", "358529", "359042", "364322", "363271"
])
date_range = st.date_input("Select Date Range", [])

# --- Load Data ---
# Add a button to clear cache
if st.button("🔄 Refresh Data (Clear Cache)"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=3600)
def load_data(table):
    return pd.DataFrame(supabase.table(table).select("*").execute().data)

actual_df = load_data("actual_table_labor")
ideal_df = load_data("ideal_table_labor")
schedule_df = load_data("schedule_table_labor")

# --- Normalize and Clean ---
for df in [actual_df, ideal_df, schedule_df]:
    df.columns = [col.lower() for col in df.columns]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["pc_number"] = df["pc_number"].astype(str)

# --- Debug: Check raw data ---
st.write("Raw Data Info:")
st.write(f"Actual df: {len(actual_df)} records, date range: {actual_df['date'].min()} to {actual_df['date'].max()}")
st.write(f"Ideal df: {len(ideal_df)} records, date range: {ideal_df['date'].min()} to {ideal_df['date'].max()}")
st.write(f"Schedule df: {len(schedule_df)} records, date range: {schedule_df['date'].min()} to {schedule_df['date'].max()}")
st.write("---")

# --- Merge Data ---
merged = actual_df.merge(ideal_df, on=["pc_number", "date", "hour_range"], how="left") \
                  .merge(schedule_df, on=["pc_number", "date", "hour_range"], how="left")

# --- Apply Filters ---
# Create a copy for weekly summary (only location filter, no date filter)
merged_for_weekly = merged.copy()
if location_filter != "All":
    merged_for_weekly = merged_for_weekly[merged_for_weekly["pc_number"] == location_filter]

# Apply filters to main merged data (for daily summary and charts)
if location_filter != "All":
    merged = merged[merged["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]).date(), pd.to_datetime(date_range[1]).date()
    merged = merged[(merged["date"] >= start) & (merged["date"] <= end)]

# --- Group Daily Summary ---
daily_summary = merged.groupby("date").agg(
    ideal_hours=("ideal_hours", "sum"),
    scheduled_hours=("scheduled_hours", "sum"),
    actual_hours=("actual_hours", "sum"),
    actual_labor=("actual_labor", "sum"),
    sales_value=("sales_value", "sum")
).reset_index()

daily_summary["actual_labor_pct_sales"] = (
    daily_summary["actual_labor"] / daily_summary["sales_value"]
) * 100

# --- Debug: Check daily summary range ---
if not daily_summary.empty:
    st.write(f"Daily summary range: {daily_summary['date'].min()} to {daily_summary['date'].max()}")
else:
    st.write("Daily summary is empty!")
st.write(f"Daily summary records: {len(daily_summary)}")

# --- Debug: Check data range ---
st.write("Filtered Data Info:")
if not merged.empty:
    st.write(f"Date range in merged data: {merged['date'].min()} to {merged['date'].max()}")
else:
    st.write("Merged data is empty!")
st.write(f"Total records: {len(merged)}")
if date_range and len(date_range) == 2:
    st.write(f"Selected date range: {date_range[0]} to {date_range[1]}")
st.write("---")

# --- Weekly Summary ---
merged_for_weekly["week"] = pd.to_datetime(merged_for_weekly["date"])
weekly_summary = merged_for_weekly.groupby(pd.Grouper(key="week", freq="W-SAT")).agg(
    ideal_hours=("ideal_hours", "sum"),
    scheduled_hours=("scheduled_hours", "sum"),
    actual_hours=("actual_hours", "sum"),
    actual_labor=("actual_labor", "sum"),
    sales_value=("sales_value", "sum")
).reset_index()
weekly_summary["week_start"] = weekly_summary["week"] - pd.to_timedelta(6, unit="d")
weekly_summary["actual_labor_pct_sales"] = (
    weekly_summary["actual_labor"] / weekly_summary["sales_value"]
) * 100

# --- Debug: Check weekly summary range ---
st.write(f"Weekly summary range: {weekly_summary['week_start'].min()} to {weekly_summary['week'].max()}")
st.write(f"Weekly summary records: {len(weekly_summary)}")

# --- Charts ---
st.subheader("📊 Actual Labor % of Sales")
if not daily_summary.empty:
    st.line_chart(daily_summary.set_index("date")[["actual_labor_pct_sales"]])
else:
    st.info("No daily data to display for selected filters.")

st.subheader("🕐 Labor Hours Comparison")
if not daily_summary.empty:
    st.line_chart(daily_summary.set_index("date")[["ideal_hours", "scheduled_hours", "actual_hours"]])

st.subheader("💰 Sales vs Labor Cost")
if not daily_summary.empty:
    st.line_chart(daily_summary.set_index("date")[["sales_value", "actual_labor"]])

# --- Raw Data Tables ---
st.subheader("📋 Daily Summary Table")
st.dataframe(daily_summary)

st.subheader("📅 Weekly Summary Table (Sunday to Saturday)")
st.dataframe(
    weekly_summary[[
        "week_start", "week", "ideal_hours", "scheduled_hours", "actual_hours",
        "actual_labor", "sales_value", "actual_labor_pct_sales"
    ]].rename(columns={"week": "week_end"})
)
