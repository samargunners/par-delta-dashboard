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

# --- Late threshold ---
st.markdown("### ⚙️ Settings")
late_threshold = st.slider("Late time threshold (minutes)", min_value=1, max_value=15, value=5)

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data(table):
    df = pd.DataFrame(supabase.table(table).select("*").execute().data)
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df

clock_df = load_data("employee_clockin")
sched_df = load_data("employee_schedules")
stores_df = load_data("stores")  # must include pc_number + store_name

if clock_df.empty or sched_df.empty:
    st.warning("⚠️ One or both tables are empty.")
    st.stop()

# --- Preprocess ---
clock_df["date"] = pd.to_datetime(clock_df["date"])
sched_df["date"] = pd.to_datetime(sched_df["date"])
clock_df["employee_id"] = clock_df["employee_id"].astype(str)
sched_df["employee_id"] = sched_df["employee_id"].astype(str)
clock_df["pc_number"] = clock_df["pc_number"].astype(str).str.zfill(6)

if location_filter != "All":
    clock_df = clock_df[clock_df["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    clock_df = clock_df[(clock_df["date"] >= start) & (clock_df["date"] <= end)]
    sched_df = sched_df[(sched_df["date"] >= start) & (sched_df["date"] <= end)]

# --- Keep earliest clock-in per employee/date
clock_df = clock_df.sort_values(by=["employee_id", "date", "time_in"]).drop_duplicates(
    subset=["employee_id", "date"], keep="first"
)

# --- Merge schedule + earliest clockin
merged_df = pd.merge(
    sched_df,
    clock_df[["employee_id", "date", "time_in", "employee_name", "pc_number"]],
    on=["employee_id", "date"],
    how="left"
)

# --- Evaluate clock-in status
def evaluate(row):
    try:
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
    except:
        return pd.Series(["Invalid", None])

merged_df[["status", "late_minutes"]] = merged_df.apply(evaluate, axis=1)

# --- Grouping + Summary ---
summary = merged_df.copy()
report = summary.groupby(["employee_id", "employee_name", "pc_number"]).agg(
    count_ontime=("status", lambda x: (x == "On Time").sum()),
    count_late=("status", lambda x: (x == "Late").sum()),
    count_early=("status", lambda x: (x == "Early").sum()),
    count_absent=("status", lambda x: (x == "Absent").sum()),
    avg_late_minutes=("late_minutes", lambda x: round(x[x > 0].mean(), 2) if (x > 0).any() else 0)
).reset_index()

# --- Map store name
store_map = dict(zip(stores_df["pc_number"], stores_df["store_name"]))
report["location"] = report["pc_number"].map(store_map)
report.drop(columns="pc_number", inplace=True)

# --- Display Summary Table ---
st.subheader("📋 Employee Punctuality Summary")
st.dataframe(report)

# --- Bar Chart: On Time vs Late per Employee ---
st.subheader("📊 On Time vs Late per Employee")
plot_data = report[["employee_name", "count_ontime", "count_late"]].copy()
plot_data = pd.melt(plot_data, id_vars="employee_name", var_name="Status", value_name="Count")
plot_data["Status"] = plot_data["Status"].str.replace("count_", "").str.title()

fig_bar = px.bar(plot_data, x="employee_name", y="Count", color="Status", barmode="group",
                 title="On Time vs Late Clock-ins per Employee")
fig_bar.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_bar, use_container_width=True)

# --- 📆 Daily Punctuality Trend Line ---
st.subheader("📈 Daily Punctuality Trend")
trend_data = summary[summary["status"].isin(["On Time", "Late"])].copy()
trend_grouped = trend_data.groupby(["date", "status"]).size().reset_index(name="count")

fig_trend = px.line(
    trend_grouped, x="date", y="count", color="status",
    markers=True, title="Daily Punctuality Trend"
)
st.plotly_chart(fig_trend, use_container_width=True)

# --- 🔥 Heatmap of Status by Day ---
st.subheader("🗓️ Heatmap: Daily Punctuality Status")
heatmap_data = summary.copy()
heatmap_data["day"] = heatmap_data["date"].dt.strftime("%Y-%m-%d")
heatmap_pivot = heatmap_data.pivot_table(
    index="day", columns="status", values="employee_id", aggfunc="count", fill_value=0
).reset_index()

heatmap_long = pd.melt(heatmap_pivot, id_vars="day", var_name="Status", value_name="Count")

fig_heatmap = px.density_heatmap(
    heatmap_long, x="Status", y="day", z="Count", color_continuous_scale="Blues",
    title="Punctuality Heatmap by Day"
)
fig_heatmap.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(fig_heatmap, use_container_width=True)
