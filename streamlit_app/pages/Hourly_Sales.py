import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, date, timedelta
import plotly.express as px

# -------------------------------
# Page & Theme
# -------------------------------
st.set_page_config(page_title="Hourly Sales & Labor", layout="wide")
st.title("📊 Hourly Sales & Labor")

# -------------------------------
# Supabase Setup
# -------------------------------
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# -------------------------------
# Utility
# -------------------------------
def _parse_hour_start(hr: str):
    """
    Parse hour_range like '02:00-02:59' -> time(02:00) for proper sorting.
    Returns (hour:int, minute:int) fallback to large number if bad.
    """
    try:
        start = hr.split("-")[0]  # 'HH:MM'
        hh, mm = start.split(":")
        return (int(hh), int(mm))
    except Exception:
        return (99, 99)

def _ensure_date_range(value):
    """
    Streamlit's date_input can return a single date or a tuple/list.
    Normalize to (start, end).
    """
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0], value[1]
    if isinstance(value, date):
        return value, value
    # Fallback: today
    return date.today(), date.today()

def _fmt_currency(x):
    try:
        return f"${x:,.0f}"
    except Exception:
        return "—"

def _fmt_float(x, ndigits=2):
    try:
        return f"{x:.{ndigits}f}"
    except Exception:
        return "—"

# -------------------------------
# Data Fetching
# -------------------------------
@st.cache_data(ttl=3600)
def load_all_rows(table, columns="*"):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        resp = supabase.table(table).select(columns).range(offset, offset + chunk_size - 1).execute()
        data_chunk = resp.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

# Button to clear cache & rerun (handy on Streamlit Cloud)
col_refresh, _ = st.columns([1, 8])
with col_refresh:
    if st.button("🔄 Refresh (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()

# -------------------------------
# Load Data
# -------------------------------
df = load_all_rows(
    "actual_table_labor",
    columns="pc_number,date,hour_range,actual_hours,actual_labor,sales_value,check_count,sales_per_labor_hour"
)

if df.empty:
    st.error("❌ No data found in `actual_table_labor` table.")
    st.stop()

# Preprocess
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df = df.dropna(subset=["date"]).copy()
df["pc_number"] = df["pc_number"].astype(str)
df["hour_range"] = df["hour_range"].astype(str)

# For hour sorting
df["_hour_key"] = df["hour_range"].apply(_parse_hour_start)

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("🔎 Filters")

# Store filter
stores = sorted(df["pc_number"].unique())
store_filter = st.sidebar.multiselect("Store(s) / PC Number(s)", stores, default=stores)

# Date presets
dates_all = sorted(df["date"].unique())
min_date, max_date = dates_all[0], dates_all[-1]

preset = st.sidebar.radio(
    "Date Range",
    ["Today", "Last 7 days", "Custom"],
    index=1 if (max_date - timedelta(days=6) >= min_date) else 2,
    horizontal=True
)

if preset == "Today":
    start_date, end_date = max_date, max_date
elif preset == "Last 7 days":
    start_date, end_date = max(min_date, max_date - timedelta(days=6)), max_date
else:
    custom = st.sidebar.date_input("Custom range", value=(min_date, max_date))
    start_date, end_date = _ensure_date_range(custom)

# Hour filter (sorted by start time)
hours_all = sorted(df["hour_range"].unique(), key=_parse_hour_start)
hour_filter = st.sidebar.multiselect("Hour Range(s)", hours_all, default=hours_all)

# -------------------------------
# Apply Filters
# -------------------------------
mask = (
    df["pc_number"].isin(store_filter)
    & df["date"].between(start_date, end_date)
    & df["hour_range"].isin(hour_filter)
)

filtered = df.loc[mask].copy()
filtered.sort_values(by=["date", "_hour_key", "pc_number"], inplace=True)

# -------------------------------
# Header KPIs
# -------------------------------
if filtered.empty:
    st.info("ℹ️ No data for the selected filters. Try expanding the date range or selecting different stores/hours.")
    st.stop()

total_sales = filtered["sales_value"].fillna(0).sum()
total_labor = filtered["actual_labor"].fillna(0).sum()
total_checks = filtered["check_count"].fillna(0).sum()
# Weighted SPLH fallback: if not present, compute as sales / hours
has_splh = filtered["sales_per_labor_hour"].notna().any()
if has_splh:
    # Average SPLH across rows (not weighted)
    splh_value = filtered["sales_per_labor_hour"].dropna().mean()
else:
    # Weighted by actual_hours to avoid division by zero
    hours_sum = filtered["actual_hours"].fillna(0).sum()
    splh_value = (total_sales / hours_sum) if hours_sum else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Sales", _fmt_currency(total_sales))
k2.metric("Labor $", _fmt_currency(total_labor))
k3.metric("Checks", f"{int(total_checks):,}")
k4.metric("Sales / Labor Hour", _fmt_currency(splh_value))

# -------------------------------
# Tabs: Charts / Table
# -------------------------------
tab_charts, tab_table = st.tabs(["📈 Charts", "🧾 Table"])

with tab_charts:
    # Sales by hour (grouped by store)
    st.subheader("Hourly Sales Value by Store")
    fig_sales = px.bar(
        filtered,
        x="hour_range",
        y="sales_value",
        color="pc_number",
        barmode="group",
        category_orders={"hour_range": hours_all},
        labels={"hour_range": "Hour", "sales_value": "Sales ($)", "pc_number": "Store"},
    )
    fig_sales.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_sales, use_container_width=True)

    # Labor by hour (line)
    st.subheader("Hourly Labor ($) by Store")
    fig_labor = px.line(
        filtered,
        x="hour_range",
        y="actual_labor",
        color="pc_number",
        markers=True,
        category_orders={"hour_range": hours_all},
        labels={"hour_range": "Hour", "actual_labor": "Labor ($)", "pc_number": "Store"},
    )
    fig_labor.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_labor, use_container_width=True)

    # Optional: SPLH by hour
    st.subheader("Sales per Labor Hour (SPLH)")
    splh_df = filtered.copy()
    if not has_splh:
        # Compute per row if missing
        splh_df["sales_per_labor_hour"] = splh_df.apply(
            lambda r: (r["sales_value"] / r["actual_hours"]) if r.get("actual_hours", 0) else None, axis=1
        )
    fig_splh = px.line(
        splh_df,
        x="hour_range",
        y="sales_per_labor_hour",
        color="pc_number",
        markers=True,
        category_orders={"hour_range": hours_all},
        labels={"hour_range": "Hour", "sales_per_labor_hour": "SPLH", "pc_number": "Store"},
    )
    fig_splh.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_splh, use_container_width=True)

with tab_table:
    st.subheader("Filtered Hourly Sales & Labor Data")
    # Pretty table ordering
    show_cols = [
        "pc_number", "date", "hour_range",
        "actual_hours", "actual_labor",
        "sales_value", "check_count", "sales_per_labor_hour"
    ]
    table_df = filtered[show_cols].sort_values(by=["date", "_hour_key", "pc_number"])
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True
    )

    # Download
    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="hourly_sales_labor_filtered.csv",
        mime="text/csv",
    )

# -------------------------------
# Footer helpers
# -------------------------------
with st.expander("ℹ️ How to use this page"):
    st.markdown(
        """
- Use the **sidebar** to filter by store(s), date range (with quick presets), and hour ranges.
- **Charts** show sales, labor, and SPLH by hour with proper hour sorting.
- **Table** provides an export of the filtered data for deeper analysis.
- Click **Refresh** at the top if you've just uploaded or updated data.
        """
    )
