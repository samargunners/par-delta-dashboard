import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
import plotly.express as px
import plotly.graph_objects as go

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Employee Punctuality", layout="wide")
st.title("⏱️ Employee Punctuality Report")
st.markdown("**Track which employees are on time and which are late**")

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
clock_df = load_all_rows("employee_clockin")
sched_df = load_all_rows("employee_schedules")
stores_df = load_all_rows("stores")

if clock_df.empty or sched_df.empty:
    st.warning("⚠️ Clock-in or schedule data is not available.")
    st.stop()

# --- Preprocessing ---
clock_df["date"] = pd.to_datetime(clock_df["date"], errors="coerce")
sched_df["date"] = pd.to_datetime(sched_df["date"], errors="coerce")
clock_df["employee_id"] = clock_df["employee_id"].astype(str)
sched_df["employee_id"] = sched_df["employee_id"].astype(str)
clock_df["pc_number"] = clock_df["pc_number"].astype(str).str.zfill(6)

# Create employee name mapping from profile
if not employee_profile_df.empty:
    employee_profile_df["employee_number"] = employee_profile_df["employee_number"].astype(str)
    employee_profile_df["full_name"] = (
        employee_profile_df["first_name"].fillna("") + " " + 
        employee_profile_df["last_name"].fillna("")
    ).str.strip()
    name_map = dict(zip(employee_profile_df["employee_number"], employee_profile_df["full_name"]))
    location_map = dict(zip(employee_profile_df["employee_number"], employee_profile_df["primary_location"]))
    position_map = dict(zip(employee_profile_df["employee_number"], employee_profile_df["primary_position"]))
else:
    name_map = {}
    location_map = {}
    position_map = {}

# Store name mapping
store_map = dict(zip(stores_df["pc_number"], stores_df["store_name"])) if not stores_df.empty else {}

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

# Location filter
location_options = ["All Stores"] + sorted(clock_df["pc_number"].unique().tolist())
location_filter = st.sidebar.selectbox("Select Store", location_options)

# Position filter (if employee profile available)
if not employee_profile_df.empty:
    position_options = ["All Positions"] + sorted(employee_profile_df["primary_position"].dropna().unique().tolist())
    position_filter = st.sidebar.selectbox("Select Position", position_options)
else:
    position_filter = "All Positions"

# Status filter
if not employee_profile_df.empty:
    status_options = ["All Statuses"] + sorted(employee_profile_df["status"].dropna().unique().tolist())
    status_filter = st.sidebar.selectbox("Select Status", status_options)
else:
    status_filter = "All Statuses"

# Date range
latest_clockin_date = clock_df["date"].max()
default_start_date = latest_clockin_date - pd.Timedelta(days=6)
default_end_date = latest_clockin_date

min_date = min(clock_df["date"].min(), sched_df["date"].min())
max_date = max(clock_df["date"].max(), sched_df["date"].max())

date_range = st.sidebar.date_input(
    "Select Date Range", 
    [default_start_date, default_end_date], 
    min_value=min_date, 
    max_value=max_date
)

# Late threshold
st.sidebar.markdown("### ⚙️ Settings")
late_threshold = st.sidebar.slider("Late time threshold (minutes)", min_value=1, max_value=15, value=5)

# --- Apply Filters ---
if location_filter != "All Stores":
    clock_df = clock_df[clock_df["pc_number"] == location_filter]
    sched_df = sched_df[sched_df["employee_id"].isin(clock_df["employee_id"].unique())]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    clock_df = clock_df[(clock_df["date"] >= start) & (clock_df["date"] <= end)]
    sched_df = sched_df[(sched_df["date"] >= start) & (sched_df["date"] <= end)]

# Filter by position/status if employee profile available
if not employee_profile_df.empty:
    filtered_employee_ids = employee_profile_df["employee_number"].astype(str)
    
    if position_filter != "All Positions":
        filtered_employee_ids = employee_profile_df[
            employee_profile_df["primary_position"] == position_filter
        ]["employee_number"].astype(str)
    
    if status_filter != "All Statuses":
        filtered_employee_ids = employee_profile_df[
            employee_profile_df["status"] == status_filter
        ]["employee_number"].astype(str)
    
    clock_df = clock_df[clock_df["employee_id"].isin(filtered_employee_ids)]
    sched_df = sched_df[sched_df["employee_id"].isin(filtered_employee_ids)]

# --- Keep earliest clock-in per employee/date ---
clock_df = clock_df.sort_values(by=["employee_id", "date", "time_in"]).drop_duplicates(
    subset=["employee_id", "date"], keep="first"
)

# --- Merge Schedule + Clockin ---
merged_df = pd.merge(
    sched_df,
    clock_df[["employee_id", "date", "time_in", "employee_name", "pc_number"]],
    on=["employee_id", "date"],
    how="left"
)

# Add employee profile info if available
if name_map:
    merged_df["full_name"] = merged_df["employee_id"].map(name_map)
    merged_df["full_name"] = merged_df["full_name"].fillna(merged_df["employee_name"])
else:
    merged_df["full_name"] = merged_df["employee_name"]

if location_map:
    merged_df["primary_location"] = merged_df["employee_id"].map(location_map)
else:
    merged_df["primary_location"] = merged_df["pc_number"].map(store_map)

if position_map:
    merged_df["primary_position"] = merged_df["employee_id"].map(position_map)
else:
    merged_df["primary_position"] = ""

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

# --- Summary Statistics ---
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

total_employees = merged_df["employee_id"].nunique()
on_time_count = len(merged_df[merged_df["status"] == "On Time"])
late_count = len(merged_df[merged_df["status"] == "Late"])
absent_count = len(merged_df[merged_df["status"] == "Absent"])

with col1:
    st.metric("Total Employees", total_employees)
with col2:
    st.metric("On Time Records", on_time_count, delta=f"{on_time_count/(on_time_count+late_count)*100:.1f}%" if (on_time_count+late_count) > 0 else "0%")
with col3:
    st.metric("Late Records", late_count, delta=f"-{late_count/(on_time_count+late_count)*100:.1f}%" if (on_time_count+late_count) > 0 else "0%")
with col4:
    st.metric("Absent Records", absent_count)

# --- Employee Punctuality Summary Table ---
st.markdown("---")
st.subheader("📋 Employee Punctuality Summary")

# Calculate detailed metrics per employee
detailed_report = merged_df.groupby(["employee_id", "full_name", "primary_position", "primary_location", "pc_number"]).agg(
    days_scheduled=("status", "count"),
    times_on_time=("status", lambda x: (x == "On Time").sum()),
    times_late=("status", lambda x: (x == "Late").sum()),
    times_early=("status", lambda x: (x == "Early").sum()),
    times_absent=("status", lambda x: (x == "Absent").sum()),
    avg_late_minutes=("late_minutes", lambda x: round(x[x > 0].mean(), 2) if (x > 0).any() else 0)
).reset_index()

# Calculate punctuality percentage
detailed_report["attendance_days"] = (
    detailed_report["times_on_time"] + 
    detailed_report["times_late"] + 
    detailed_report["times_early"]
)
detailed_report["punctuality_percentage"] = detailed_report.apply(
    lambda row: round((row["times_on_time"] + row["times_early"]) / row["attendance_days"] * 100, 1) 
    if row["attendance_days"] > 0 else 0, axis=1
)

# Add store name
if store_map:
    detailed_report["store_name"] = detailed_report["pc_number"].map(store_map)
    detailed_report["store_name"] = detailed_report["store_name"].fillna(detailed_report["pc_number"])

# Create display dataframe
display_report = detailed_report[[
    "full_name", "primary_position", "store_name", "days_scheduled", 
    "times_on_time", "times_late", "times_early", "times_absent", 
    "punctuality_percentage", "avg_late_minutes"
]].rename(columns={
    "full_name": "Employee Name",
    "primary_position": "Position",
    "store_name": "Store",
    "days_scheduled": "Days Scheduled",
    "times_on_time": "✅ On Time",
    "times_late": "❌ Late",
    "times_early": "⏰ Early",
    "times_absent": "🚫 Absent",
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

# Apply styling
def style_punctuality_table(df):
    def apply_color(row):
        percentage = row["Punctuality %"]
        color = get_punctuality_color(percentage)
        styles = [""] * len(row)
        # Apply color to Employee Name column
        name_idx = row.index.get_loc("Employee Name")
        styles[name_idx] = color
        return styles
    
    return df.style.apply(apply_color, axis=1).format({
        "Punctuality %": "{:.1f}%",
        "Avg Late (mins)": "{:.1f}"
    })

# Sort options
sort_option = st.selectbox(
    "Sort by:",
    ["Punctuality % (Best First)", "Punctuality % (Worst First)", "Most Late", "Most On Time", "Employee Name"]
)

if sort_option == "Punctuality % (Best First)":
    display_report_sorted = display_report.sort_values("Punctuality %", ascending=False)
elif sort_option == "Punctuality % (Worst First)":
    display_report_sorted = display_report.sort_values("Punctuality %", ascending=True)
elif sort_option == "Most Late":
    display_report_sorted = display_report.sort_values("❌ Late", ascending=False)
elif sort_option == "Most On Time":
    display_report_sorted = display_report.sort_values("✅ On Time", ascending=False)
else:
    display_report_sorted = display_report.sort_values("Employee Name", ascending=True)

# Display the styled table
styled_table = style_punctuality_table(display_report_sorted)
st.dataframe(styled_table, use_container_width=True, height=400)

# Color legend
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

# --- Visualizations ---
st.markdown("---")
st.subheader("📊 Visualizations")

# On Time vs Late Chart
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### ✅ On Time vs ❌ Late per Employee")
    plot_data = detailed_report[["full_name", "times_on_time", "times_late"]].copy()
    plot_data = plot_data.sort_values("times_late", ascending=False).head(20)  # Top 20 by late count
    plot_data = pd.melt(plot_data, id_vars="full_name", var_name="Status", value_name="Count")
    plot_data["Status"] = plot_data["Status"].str.replace("times_", "").str.replace("_", " ").str.title()
    
    fig_bar = px.bar(
        plot_data, 
        x="full_name", 
        y="Count", 
        color="Status", 
        barmode="group",
        title="On Time vs Late (Top 20 by Late Count)",
        color_discrete_map={"On Time": "#28a745", "Late": "#dc3545"}
    )
    fig_bar.update_layout(xaxis_tickangle=-45, showlegend=True)
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.markdown("#### 📈 Punctuality Distribution")
    punctuality_data = detailed_report[detailed_report["punctuality_percentage"] > 0].copy()
    fig_hist = px.histogram(
        punctuality_data,
        x="punctuality_percentage",
        nbins=20,
        title="Distribution of Punctuality Percentages",
        labels={"punctuality_percentage": "Punctuality %", "count": "Number of Employees"},
        color_discrete_sequence=["#5cb85c"]
    )
    fig_hist.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="Critical Threshold (70%)")
    st.plotly_chart(fig_hist, use_container_width=True)

# Daily Trend
st.markdown("#### 📆 Daily Punctuality Trend")
trend_data = merged_df[merged_df["status"].isin(["On Time", "Late"])].copy()
trend_grouped = trend_data.groupby(["date", "status"]).size().reset_index(name="count")

fig_trend = px.line(
    trend_grouped, 
    x="date", 
    y="count", 
    color="status", 
    markers=True,
    title="Daily On Time vs Late Trend",
    color_discrete_map={"On Time": "#28a745", "Late": "#dc3545"}
)
st.plotly_chart(fig_trend, use_container_width=True)

# Store-wise breakdown
if not detailed_report.empty and "store_name" in detailed_report.columns:
    st.markdown("#### 🏪 Store-wise Punctuality")
    store_summary = detailed_report.groupby("store_name").agg({
        "times_on_time": "sum",
        "times_late": "sum",
        "punctuality_percentage": "mean"
    }).reset_index()
    
    store_plot = pd.melt(
        store_summary[["store_name", "times_on_time", "times_late"]],
        id_vars="store_name",
        var_name="Status",
        value_name="Count"
    )
    store_plot["Status"] = store_plot["Status"].str.replace("times_", "").str.replace("_", " ").str.title()
    
    fig_store = px.bar(
        store_plot,
        x="store_name",
        y="Count",
        color="Status",
        barmode="group",
        title="On Time vs Late by Store",
        color_discrete_map={"On Time": "#28a745", "Late": "#dc3545"}
    )
    fig_store.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig_store, use_container_width=True)

# --- Detailed Records Search ---
st.markdown("---")
st.subheader("🔍 Search Individual Clock-in Records")
search_name = st.text_input("Search by Employee Name (partial or full):").strip().lower()

search_df = merged_df.copy()
search_df["date"] = search_df["date"].dt.strftime("%Y-%m-%d")
search_df = search_df[[
    "full_name", "primary_position", "date", "start_time", "end_time", 
    "time_in", "status", "late_minutes", "store_name"
]].rename(columns={
    "full_name": "Employee",
    "primary_position": "Position",
    "start_time": "Scheduled Start",
    "end_time": "Scheduled End",
    "time_in": "Actual Clock-in",
    "status": "Status",
    "late_minutes": "Late (mins)",
    "store_name": "Store"
})

if search_name:
    search_df = search_df[search_df["Employee"].str.lower().str.contains(search_name)]

# Status filter for search
status_filter_search = st.multiselect(
    "Filter by Status",
    options=["On Time", "Late", "Early", "Absent", "On Call"],
    default=["On Time", "Late"]
)
if status_filter_search:
    search_df = search_df[search_df["Status"].isin(status_filter_search)]

# Pagination
page_size = 20
total_rows = len(search_df)
total_pages = max(1, (total_rows - 1) // page_size + 1)
page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
start_idx = (page_num - 1) * page_size
end_idx = start_idx + page_size

st.dataframe(search_df.iloc[start_idx:end_idx], use_container_width=True)
st.caption(f"Showing {start_idx+1}-{min(end_idx, total_rows)} of {total_rows} records")
