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
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df

# --- Load Tables ---
clock_df = load_all_rows("employee_clockin")
sched_df = load_all_rows("employee_schedules")
stores_df = load_all_rows("stores")  # includes pc_number and store_name

if clock_df.empty or sched_df.empty:
    st.warning("⚠️ One or both tables are empty.")
    st.stop()

# --- Preprocessing ---
clock_df["date"] = pd.to_datetime(clock_df["date"], errors="coerce")
sched_df["date"] = pd.to_datetime(sched_df["date"], errors="coerce")
clock_df["employee_id"] = clock_df["employee_id"].astype(str)
sched_df["employee_id"] = sched_df["employee_id"].astype(str)
clock_df["pc_number"] = clock_df["pc_number"].astype(str).str.zfill(6)

# --- Filters ---
location_filter = st.selectbox("Select Store", ["All"] + sorted(clock_df["pc_number"].unique()))

# Set default date range based on latest date in clockin table (7 days back from latest)
latest_clockin_date = clock_df["date"].max()
default_start_date = latest_clockin_date - pd.Timedelta(days=6)  # 7 days total (including latest date)
default_end_date = latest_clockin_date

# Overall min/max dates for the date picker limits
min_date = min(clock_df["date"].min(), sched_df["date"].min())
max_date = max(clock_df["date"].max(), sched_df["date"].max())

date_range = st.date_input("Select Date Range", [default_start_date, default_end_date], min_value=min_date, max_value=max_date)

st.markdown("### ⚙️ Settings")
late_threshold = st.slider("Late time threshold (minutes)", min_value=1, max_value=15, value=5)

# --- Apply Filters ---
if location_filter != "All":
    clock_df = clock_df[clock_df["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    clock_df = clock_df[(clock_df["date"] >= start) & (clock_df["date"] <= end)]
    sched_df = sched_df[(sched_df["date"] >= start) & (sched_df["date"] <= end)]

# --- Keep earliest clock-in per employee/date ---
clock_df = clock_df.sort_values(by=["employee_id", "date", "time_in"]).drop_duplicates(subset=["employee_id", "date"], keep="first")

# --- Merge Schedule + Clockin ---
merged_df = pd.merge(
    sched_df,
    clock_df[["employee_id", "date", "time_in", "employee_name", "pc_number"]],
    on=["employee_id", "date"],
    how="left"
)

# --- Evaluate Punctuality ---
def evaluate(row):
    try:
        if pd.isna(row["start_time"]):
            if pd.notna(row["time_in"]):
                return pd.Series(["On Call", None])
            else:
                return pd.Series(["No Schedule", None])
        if pd.isna(row["time_in"]):
            return pd.Series(["Absent", None])

        start_dt = datetime.combine(datetime.today(), pd.to_datetime(row["start_time"]).time())
        timein_dt = datetime.combine(datetime.today(), pd.to_datetime(row["time_in"]).time())
        delta = (timein_dt - start_dt).total_seconds() / 60

        if abs(delta) <= late_threshold:
            return pd.Series(["On Time", 0])
        elif delta > late_threshold:
            return pd.Series(["Late", round(delta)])
        elif delta < -late_threshold:
            return pd.Series(["Early", 0])
        else:
            return pd.Series(["Other", None])
    except Exception as e:
        return pd.Series(["Invalid", None])


merged_df[["status", "late_minutes"]] = merged_df.apply(evaluate, axis=1)

# --- Summary Report ---
summary = merged_df.copy()
report = summary.groupby(["employee_id", "employee_name", "pc_number"]).agg(
    count_ontime=("status", lambda x: (x == "On Time").sum()),
    count_late=("status", lambda x: (x == "Late").sum()),
    count_early=("status", lambda x: (x == "Early").sum()),
    count_absent=("status", lambda x: (x == "Absent").sum()),
    avg_late_minutes=("late_minutes", lambda x: round(x[x > 0].mean(), 2) if (x > 0).any() else 0)
).reset_index()

store_map = dict(zip(stores_df["pc_number"], stores_df["store_name"]))
report["location"] = report["pc_number"].map(store_map)
report.drop(columns="pc_number", inplace=True)

# --- Enhanced Employee Punctuality Table ---
st.subheader("📋 Employee Punctuality Summary")

# Calculate punctuality metrics
detailed_report = summary.groupby(["employee_id", "employee_name", "pc_number"]).agg(
    days_scheduled=("status", "count"),
    times_on_time=("status", lambda x: (x == "On Time").sum()),
    times_late=("status", lambda x: (x == "Late").sum()),
    times_early=("status", lambda x: (x == "Early").sum()),
    times_absent=("status", lambda x: (x == "Absent").sum()),
    avg_late_minutes=("late_minutes", lambda x: round(x[x > 0].mean(), 2) if (x > 0).any() else 0)
).reset_index()

# Calculate punctuality percentage
# Punctuality = (On Time + Early) / (On Time + Late + Early) * 100
# Excludes absent days from the calculation
detailed_report["attendance_days"] = (detailed_report["times_on_time"] + 
                                    detailed_report["times_late"] + 
                                    detailed_report["times_early"])
detailed_report["punctuality_percentage"] = detailed_report.apply(
    lambda row: round((row["times_on_time"] + row["times_early"]) / row["attendance_days"] * 100, 1) 
    if row["attendance_days"] > 0 else 0, axis=1
)

# Add location mapping
detailed_report["location"] = detailed_report["pc_number"].map(store_map)

# Create display dataframe
display_report = detailed_report[[
    "employee_name", "location", "days_scheduled", "times_on_time", 
    "times_late", "times_early", "times_absent", "punctuality_percentage", "avg_late_minutes"
]].rename(columns={
    "employee_name": "Employee Name",
    "location": "Store Location",
    "days_scheduled": "Days Scheduled",
    "times_on_time": "Times On Time",
    "times_late": "Times Late",
    "times_early": "Times Early", 
    "times_absent": "Times Absent",
    "punctuality_percentage": "Punctuality %",
    "avg_late_minutes": "Avg Late (mins)"
})

# Function to get color based on punctuality percentage
def get_punctuality_color(percentage):
    if percentage >= 95:
        return "background-color: #28a745; color: white"  # Dark Green
    elif percentage >= 90:
        return "background-color: #5cb85c; color: white"  # Medium Green
    elif percentage >= 85:
        return "background-color: #f0ad4e; color: white"  # Yellow-Orange
    elif percentage >= 80:
        return "background-color: #fd7e14; color: white"  # Bright Orange
    elif percentage >= 75:
        return "background-color: #e67e22; color: white"  # Deep Orange
    elif percentage >= 70:
        return "background-color: #d35400; color: white"  # Dark Orange
    else:
        return "background-color: #dc3545; color: white"  # Bold Red

# Apply styling to the dataframe
def style_punctuality_table(df):
    def apply_color(row):
        percentage = row["Punctuality %"]
        color = get_punctuality_color(percentage)
        return [color if col == "Employee Name" else "" for col in row.index]
    
    return df.style.apply(apply_color, axis=1).format({
        "Punctuality %": "{:.1f}%",
        "Avg Late (mins)": "{:.1f}"
    })

# Sort by punctuality percentage (best first by default)
display_report_sorted = display_report.sort_values("Punctuality %", ascending=False)

# Display the styled table
styled_table = style_punctuality_table(display_report_sorted)
st.dataframe(styled_table, use_container_width=True)

# Add legend for color coding
st.markdown("""
**Color Legend:**
- 🟢 **Green (95%+)**: Excellent punctuality
- 🟢 **Medium Green (90-94%)**: Very good punctuality  
- 🟡 **Yellow-Orange (85-89%)**: Good punctuality
- 🟠 **Bright Orange (80-84%)**: Fair punctuality
- 🟠 **Deep Orange (75-79%)**: Poor punctuality
- 🟠 **Dark Orange (70-74%)**: Very poor punctuality
- 🔴 **Red (<70%)**: Critical punctuality issues
""")

# Display summary statistics
col1, col2, col3, col4 = st.columns(4)
with col1:
    avg_punctuality = detailed_report["punctuality_percentage"].mean()
    st.metric("Average Punctuality", f"{avg_punctuality:.1f}%")
with col2:
    best_employee = detailed_report.loc[detailed_report["punctuality_percentage"].idxmax(), "employee_name"]
    best_percentage = detailed_report["punctuality_percentage"].max()
    st.metric("Best Performer", f"{best_employee}", f"{best_percentage:.1f}%")
with col3:
    worst_employee = detailed_report.loc[detailed_report["punctuality_percentage"].idxmin(), "employee_name"]
    worst_percentage = detailed_report["punctuality_percentage"].min()
    st.metric("Needs Attention", f"{worst_employee}", f"{worst_percentage:.1f}%")
with col4:
    critical_count = len(detailed_report[detailed_report["punctuality_percentage"] < 70])
    st.metric("Critical Cases", f"{critical_count} employees", "< 70%")

st.dataframe(report)

# --- On Time vs Late per Employee ---
st.subheader("📊 On Time vs Late per Employee")
plot_data = report[["employee_name", "count_ontime", "count_late"]].copy()
plot_data = pd.melt(plot_data, id_vars="employee_name", var_name="Status", value_name="Count")
plot_data["Status"] = plot_data["Status"].str.replace("count_", "").str.title()

fig_bar = px.bar(plot_data, x="employee_name", y="Count", color="Status", barmode="group",
                 title="On Time vs Late Clock-ins per Employee")
fig_bar.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_bar, use_container_width=True)

# --- Daily Trend ---
st.subheader("📆 Daily Punctuality Trend")
trend_data = summary[summary["status"].isin(["On Time", "Late"])].copy()
trend_grouped = trend_data.groupby(["date", "status"]).size().reset_index(name="count")

fig_trend = px.line(trend_grouped, x="date", y="count", color="status", markers=True,
                    title="Daily Punctuality Trend")
st.plotly_chart(fig_trend, use_container_width=True)

# --- Searchable Employee Clock-in Table ---
st.subheader("🔍 Search Employee Clock-in Records")
search_name = st.text_input("Search by Employee Name (partial or full):").strip().lower()

sched_df_dedup = sched_df.sort_values(by=["employee_id", "date", "start_time"]).drop_duplicates(
    subset=["employee_id", "date"], keep="first")

search_df = pd.merge(
    clock_df,
    sched_df_dedup[["employee_id", "date", "start_time", "end_time"]],
    on=["employee_id", "date"], how="left"
)
search_df["date"] = search_df["date"].dt.strftime("%Y-%m-%d")
search_df = search_df[[
    "employee_id", "employee_name", "date", "start_time", "end_time", "time_in", "time_out", "pc_number"
]].rename(columns={
    "pc_number": "location",
    "time_in": "clock_in",
    "time_out": "clock_out"
})

if search_name:
    search_df = search_df[search_df["employee_name"].str.lower().str.contains(search_name)]

page_size = 20
total_rows = len(search_df)
total_pages = (total_rows - 1) // page_size + 1
page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
start_idx = (page_num - 1) * page_size
end_idx = start_idx + page_size
st.dataframe(search_df.iloc[start_idx:end_idx], use_container_width=True)
st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")

# --- Store-wise Summary ---
st.subheader("🏪 Store-wise Punctuality Breakdown")
store_summary = summary[summary["status"].isin(["On Time", "Late"])].copy()
store_counts = store_summary.groupby(["pc_number", "status"]).size().reset_index(name="Count")
store_counts["store_name"] = store_counts["pc_number"].map(store_map)
store_counts["Status"] = store_counts["status"]

fig_store = px.bar(
    store_counts,
    x="store_name", y="Count", color="Status", barmode="group",
    title="On Time vs Late Clock-ins by Store"
)
fig_store.update_layout(xaxis_title="Store", yaxis_title="Clock-in Count", xaxis_tickangle=-30)
st.plotly_chart(fig_store, use_container_width=True)
