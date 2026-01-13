import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Employee Punctuality", layout="wide")
st.title("🕒 Employee Punctuality Overview")

# --- Load Data with Pagination ---
@st.cache_data(ttl=3600)
def load_all_rows(table):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table(table).select("*").range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    df = pd.DataFrame(all_data)
    if not df.empty:
        df.columns = [str(col).strip().lower() for col in df.columns]
    return df

# --- Load Tables ---
employee_profile_df = load_all_rows("employee_profile")
employee_clockin_df = load_all_rows("employee_clockin")
employee_schedules_df = load_all_rows("employee_schedules")
try:
    stores_df = load_all_rows("stores")
except Exception:
    stores_df = pd.DataFrame()

if employee_profile_df.empty or employee_clockin_df.empty or employee_schedules_df.empty:
    st.error("❌ Required employee data is not available. Please upload all necessary data.")
    st.stop()

# --- Data Preprocessing ---
employee_clockin_df["date"] = pd.to_datetime(employee_clockin_df["date"], errors="coerce")
employee_clockin_df["employee_id"] = employee_clockin_df["employee_id"].astype(str)
employee_schedules_df["date"] = pd.to_datetime(employee_schedules_df["date"], errors="coerce")
employee_schedules_df["employee_id"] = employee_schedules_df["employee_id"].astype(str)
employee_profile_df["hired_date"] = pd.to_datetime(employee_profile_df["hired_date"], errors="coerce")

# --- Sidebar Filters ---
st.sidebar.header("📅 Filter Options")
if not employee_clockin_df.empty:
    min_date = employee_clockin_df["date"].min().date()
    max_date = employee_clockin_df["date"].max().date()
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
else:
    date_range = [datetime.today().date(), datetime.today().date()]

store_options = ["All"] + sorted(employee_clockin_df["pc_number"].unique()) if "pc_number" in employee_clockin_df.columns else ["All"]
selected_store = st.sidebar.selectbox("Select Store", store_options)

# --- Filter Data ---
filtered_clockin = employee_clockin_df.copy()
if selected_store != "All" and "pc_number" in filtered_clockin.columns:
    filtered_clockin = filtered_clockin[filtered_clockin["pc_number"] == selected_store]
if date_range:
    start_date, end_date = date_range
    filtered_clockin = filtered_clockin[(filtered_clockin["date"] >= pd.to_datetime(start_date)) & (filtered_clockin["date"] <= pd.to_datetime(end_date))]

# --- Merge and Calculate Punctuality ---
merged_df = pd.merge(filtered_clockin, employee_schedules_df, on=["employee_id", "date"], suffixes=("_clockin", "_schedule"))
if not merged_df.empty:
    # Handle column names based on what's available after merge
    # The actual columns are: start_time (scheduled) and time_in (clock-in)
    if "start_time" in merged_df.columns:
        scheduled_col = "start_time"
    elif "scheduled_start" in merged_df.columns:
        scheduled_col = "scheduled_start"
    elif "scheduled_start_schedule" in merged_df.columns:
        scheduled_col = "scheduled_start_schedule"
    elif "scheduled_time" in merged_df.columns:
        scheduled_col = "scheduled_time"
    elif "scheduled_time_schedule" in merged_df.columns:
        scheduled_col = "scheduled_time_schedule"
    else:
        st.error(f"Cannot find scheduled start column. Available columns: {list(merged_df.columns)}")
        st.stop()
    
    if "time_in" in merged_df.columns:
        clockin_col = "time_in"
    elif "clockin_time" in merged_df.columns:
        clockin_col = "clockin_time"
    elif "clockin_time_clockin" in merged_df.columns:
        clockin_col = "clockin_time_clockin"
    elif "clock_in_time" in merged_df.columns:
        clockin_col = "clock_in_time"
    elif "clock_in_time_clockin" in merged_df.columns:
        clockin_col = "clock_in_time_clockin"
    else:
        st.error(f"Cannot find clock-in time column. Available columns: {list(merged_df.columns)}")
        st.stop()
    
    merged_df[scheduled_col] = pd.to_datetime(merged_df[scheduled_col], errors="coerce")
    merged_df[clockin_col] = pd.to_datetime(merged_df[clockin_col], errors="coerce")
    merged_df["punctuality_minutes"] = (merged_df[clockin_col] - merged_df[scheduled_col]).dt.total_seconds() / 60
    st.subheader("Employee Punctuality Table")
    st.dataframe(merged_df[["employee_id", "date", scheduled_col, clockin_col, "punctuality_minutes"]])
    st.subheader("Punctuality Distribution")
    fig = px.histogram(merged_df, x="punctuality_minutes", nbins=30, title="Distribution of Punctuality (Minutes)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No matching records for the selected filters.")

# --- Performance Overview ---
st.subheader("Employee Performance Overview")
if not filtered_clockin.empty:
    performance_summary = filtered_clockin.groupby("employee_id").agg({"date": "count"}).rename(columns={"date": "Days Worked"})
    st.dataframe(performance_summary)
else:
    st.info("No performance data for the selected filters.")
