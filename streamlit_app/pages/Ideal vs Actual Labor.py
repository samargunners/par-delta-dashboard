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
@st.cache_data(ttl=3600)
def load_data(table):
    return pd.DataFrame(supabase.table(table).select("*").execute().data)

df = load_data("hourly_labor_summary")
df["date"] = pd.to_datetime(df["date"]).dt.date  # Convert to date only
df["pc_number"] = df["pc_number"].astype(str)

# --- Apply Filters ---
if location_filter != "All":
    df = df[df["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]).date(), pd.to_datetime(date_range[1]).date()
    df = df[(df["date"] >= start) & (df["date"] <= end)]

# --- Summary by Date ---
daily_summary = df.groupby("date").agg(
    ideal_hours=("ideal_hours", "sum"),
    scheduled_hours=("scheduled_hours", "sum"),
    actual_hours=("actual_hours", "sum"),
    actual_labor=("actual_labor", "sum"),
    forecasted_sales=("forecasted_sales", "sum"),
    sales_value=("sales_value", "sum")
).reset_index()

# --- Calculate Actual Labor % of Sales ---
daily_summary["actual_labor_pct_sales"] = (
    daily_summary["actual_labor"] / daily_summary["sales_value"]
) * 100

# --- Charts ---
st.subheader("📊 Actual Labor % of Sales")
st.line_chart(daily_summary.set_index("date")[["actual_labor_pct_sales"]])

st.subheader("🕐 Labor Hours Comparison")
st.line_chart(daily_summary.set_index("date")[["ideal_hours", "scheduled_hours", "actual_hours"]])

st.subheader("💰 Sales vs Labor Cost")
st.line_chart(daily_summary.set_index("date")[["forecasted_sales", "sales_value", "actual_labor"]])

st.subheader("📊 Actual Labor % of Sales")
st.line_chart(daily_summary.set_index("date")[["actual_labor_pct_sales"]])

# --- Raw Data Table ---
st.subheader("📋 Daily Summary Table")
st.dataframe(daily_summary)
