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

# Use the consolidated hourly_labor_summary table instead of merging separate tables
hourly_data = load_data("hourly_labor_summary")

# --- Normalize and Clean ---
hourly_data.columns = [col.lower() for col in hourly_data.columns]
hourly_data["date"] = pd.to_datetime(hourly_data["date"]).dt.date
hourly_data["pc_number"] = hourly_data["pc_number"].astype(str)

# --- Merge Data ---
# No need to merge since we're using the consolidated table
merged = hourly_data.copy()

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
