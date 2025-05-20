import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Labor Punctuality", layout="wide")
st.title("⏱️ Labor Punctuality Report")

# --- Filters ---
location_filter = st.selectbox("Select Store", ["All"] + [
    "301290", "357993", "343939", "358529", "359042", "364322", "363271"
])
date_range = st.date_input("Select Date Range", [])

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data(table):
    df = pd.DataFrame(supabase.table(table).select("*").execute().data)
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df

clock_df = load_data("employee_clockin")
sched_df = load_data("employee_schedules")

# --- Validate ---
if clock_df.empty or sched_df.empty:
    st.warning("⚠️ One or both tables are empty. Check Supabase data.")
    st.stop()

# --- Clean and filter ---
clock_df["date"] = pd.to_datetime(clock_df["date"])
sched_df["date"] = pd.to_datetime(sched_df["date"])
clock_df["employee_id"] = clock_df["employee_id"].astype(str)
sched_df["employee_id"] = sched_df["employee_id"].astype(str)

# Keep only the earliest clock-in for each employee on a given date
clock_df = clock_df.sort_values(by=["employee_id", "date", "time_in"]).drop_duplicates(subset=["employee_id", "date"], keep="first")

if location_filter != "All":
    clock_df = clock_df[clock_df["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    clock_df = clock_df[(clock_df["date"] >= start) & (clock_df["date"] <= end)]
    sched_df = sched_df[(sched_df["date"] >= start) & (sched_df["date"] <= end)]

# --- Merge ---
merged_df = pd.merge(
    clock_df,
    sched_df,
    on=["employee_id", "date"],
    how="inner",
    suffixes=("_actual", "_scheduled")
)

# --- Evaluate ---
def evaluate_clock_in(row):
    try:
        scheduled = datetime.combine(datetime.today(), pd.to_datetime(row['start_time']).time())
        actual = datetime.combine(datetime.today(), pd.to_datetime(row['time_in']).time())
        delta = (actual - scheduled).total_seconds() / 60
        if abs(delta) <= 5:
            return pd.Series(['On Time', 0])
        elif delta > 5:
            return pd.Series(['Late', delta])
        else:
            return pd.Series(['Early', 0])
    except:
        return pd.Series(['Missing', None])

merged_df[["status", "late_minutes"]] = merged_df.apply(evaluate_clock_in, axis=1)

# --- Absence Calculation ---
# All scheduled shifts
all_sched = sched_df[["employee_id", "date"]].copy()
# All clock-ins (already filtered)
all_clock = clock_df[["employee_id", "date", "employee_name", "pc_number"]].copy()
# Merge to find scheduled shifts with no clock-in
absent_df = pd.merge(
    all_sched,
    all_clock,
    on=["employee_id", "date"],
    how="left",
    indicator=True
)
absent_df = absent_df[absent_df["_merge"] == "left_only"]

# Get latest known employee_name and pc_number for each employee from clock_df
emp_info = clock_df.groupby("employee_id")[["employee_name", "pc_number"]].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None).reset_index()

# Count absences per employee/location
absent_count = absent_df.groupby("employee_id").size().reset_index(name="days_absent")
absent_count = pd.merge(absent_count, emp_info, on="employee_id", how="left")

# --- Summary ---
summary = merged_df[merged_df["status"].isin(["On Time", "Late"])]
report = summary.groupby(["employee_name", "employee_id", "pc_number"]).agg(
    count_ontime=("status", lambda x: (x == "On Time").sum()),
    count_late=("status", lambda x: (x == "Late").sum()),
    avg_late_minutes=("late_minutes", lambda x: round(x[x > 0].mean(), 2) if (x > 0).any() else 0)
).reset_index().rename(columns={"pc_number": "location"})

# Merge absence count into report
report = pd.merge(
    report,
    absent_count.rename(columns={"employee_name": "employee_name", "pc_number": "location"}),
    on=["employee_id", "employee_name", "location"],
    how="left"
)
report["days_absent"] = report["days_absent"].fillna(0).astype(int)

# --- Display Table ---
st.subheader("📋 Employee Punctuality Summary")
st.dataframe(report)

# --- Visual: Bar chart by location ---
st.subheader("📊 On Time vs Late Clock-ins per Location")
plot_data = report.groupby("location")[["count_ontime", "count_late"]].sum().reset_index()
plot_data = pd.melt(plot_data, id_vars="location", value_vars=["count_ontime", "count_late"], 
                    var_name="Status", value_name="Count")
plot_data["Status"] = plot_data["Status"].str.replace("count_", "").str.title()

fig = px.bar(plot_data, x="location", y="Count", color="Status", barmode="group", title="Punctuality by Location")
st.plotly_chart(fig, use_container_width=True)

# --- Employee Search Table ---
st.subheader("🔍 Search Employee Clock-in Records")
search_name = st.text_input("Search by Employee Name (partial or full):").strip().lower()

# Prepare a DataFrame with all relevant info
search_df = clock_df.copy()
search_df["date"] = search_df["date"].dt.strftime("%Y-%m-%d")
search_df = search_df[["employee_id", "employee_name", "date", "time_in", "time_out", "pc_number"]]
search_df = search_df.rename(columns={
    "pc_number": "location",
    "time_in": "clock_in",
    "time_out": "clock_out"
})

if search_name:
    search_df = search_df[search_df["employee_name"].str.lower().str.contains(search_name)]

st.dataframe(search_df, use_container_width=True)