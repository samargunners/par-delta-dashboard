# streamlit_app/pages/Hourly_Sales_Labor.py
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
# Utilities
# -------------------------------
def parse_hour_key(hr: str):
    """Parse 'HH:MM-HH:MM' -> (HH, MM) for sorting; fallback high for bad values."""
    try:
        start = hr.split("-")[0]
        hh, mm = start.split(":")
        return (int(hh), int(mm))
    except Exception:
        return (99, 99)

def ensure_date_range(value):
    """Normalize Streamlit date_input output to (start_date, end_date)."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return value[0], value[1]
    if isinstance(value, date):
        return value, value
    today = date.today()
    return today, today

def fmt_currency(x, ndigits=0):
    try:
        return f"${x:,.{ndigits}f}" if ndigits else f"${x:,.0f}"
    except Exception:
        return "—"

# Checkbox-style multiselect (search + select all + clear + filter button)
def checkbox_multiselect(label: str, options: list, key: str, default=None, in_sidebar=True):
    """
    Checkbox-based multi-select with search, 'Select All', 'Clear', and 'Filter' buttons.
    Returns: list of selected options.
    """
    if default is None:
        default = options

    sel_key = f"{key}_selected"
    search_key = f"{key}_search"
    tick_keys_key = f"{key}_tick_keys"

    if sel_key not in st.session_state:
        st.session_state[sel_key] = list(default)
    if search_key not in st.session_state:
        st.session_state[search_key] = ""
    if tick_keys_key not in st.session_state:
        st.session_state[tick_keys_key] = {opt: f"{key}_opt_{i}" for i, opt in enumerate(options)}

    container = st.sidebar if in_sidebar else st
    use_popover = hasattr(st, "popover")
    wrapper = container.popover(label) if use_popover else container.expander(label, expanded=False)

    with wrapper:
        # Search box
        st.session_state[search_key] = st.text_input("Search", value=st.session_state[search_key], key=f"{key}_searchbox")
        q = st.session_state[search_key].strip().lower()
        filtered = [o for o in options if q in str(o).lower()] if q else options

        current_sel = set(st.session_state[sel_key])
        all_filtered_selected = len(filtered) > 0 and all(o in current_sel for o in filtered)

        col1, col2 = st.columns([1, 1])
        # Track if select all or clear was pressed
        select_all_pressed = False
        clear_pressed = False
        with col1:
            select_all = st.checkbox("Select All", value=all_filtered_selected, key=f"{key}_select_all")
            if select_all and not all_filtered_selected:
                current_sel = current_sel.union(set(filtered))
                select_all_pressed = True
        with col2:
            if st.button("Clear", key=f"{key}_clear_btn"):
                current_sel = current_sel.difference(set(filtered))
                clear_pressed = True

        if len(filtered) == 0:
            st.caption("No results.")
        else:
            for o in filtered:
                ck = st.session_state[tick_keys_key][o]
                checked = o in current_sel
                new_checked = st.checkbox(str(o), value=checked, key=ck)
                if new_checked:
                    current_sel.add(o)
                else:
                    current_sel.discard(o)

        # If clear was pressed, also uncheck select all
        if clear_pressed:
            st.session_state[f"{key}_select_all"] = False

        # If not all filtered are selected, uncheck select all
        if not (len(filtered) > 0 and all(o in current_sel for o in filtered)):
            st.session_state[f"{key}_select_all"] = False
        elif len(filtered) > 0 and all(o in current_sel for o in filtered):
            st.session_state[f"{key}_select_all"] = True

        _ = st.button("Filter", type="primary", key=f"{key}_apply_btn")  # cosmetic; state already applied
        st.session_state[sel_key] = sorted(current_sel)

    return st.session_state[sel_key]

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
        chunk = resp.data
        if not chunk:
            break
        all_data.extend(chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

# Refresh (clear cache) button
left, _ = st.columns([1, 8])
with left:
    if st.button("🔄 Refresh (Clear Cache)"):
        st.cache_data.clear()
        st.rerun()

# -------------------------------
# Load & Preprocess
# -------------------------------
df = load_all_rows(
    "actual_table_labor",
    columns="pc_number,date,hour_range,actual_hours,actual_labor,sales_value,check_count,sales_per_labor_hour"
)

if df.empty:
    st.error("❌ No data found in `actual_table_labor`.")
    st.stop()

df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df = df.dropna(subset=["date"]).copy()
df["pc_number"] = df["pc_number"].astype(str)
df["hour_range"] = df["hour_range"].astype(str)
df["_hour_key"] = df["hour_range"].apply(parse_hour_key)

# -------------------------------
# Sidebar Filters
# -------------------------------
st.sidebar.header("🔎 Filters")

# Stores
stores = sorted(df["pc_number"].unique())
selected_stores = checkbox_multiselect(
    label="Stores / PC Numbers",
    options=stores,
    key="stores_filter",
    default=stores,
    in_sidebar=True
)

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
    custom_range = st.sidebar.date_input("Custom range", value=(min_date, max_date))
    start_date, end_date = ensure_date_range(custom_range)

# Hours
hours_all = sorted(df["hour_range"].unique(), key=parse_hour_key)
selected_hours = checkbox_multiselect(
    label="Hour Range(s)",
    options=hours_all,
    key="hours_filter",
    default=hours_all,
    in_sidebar=True
)

# -------------------------------
# Apply Filters
# -------------------------------
mask = (
    df["pc_number"].isin(selected_stores)
    & df["date"].between(start_date, end_date)
    & df["hour_range"].isin(selected_hours)
)

filtered = df.loc[mask].copy()
filtered.sort_values(by=["date", "_hour_key", "pc_number"], inplace=True)

if filtered.empty:
    st.info("ℹ️ No data for the selected filters. Try expanding the date range or selecting different stores/hours.")
    st.stop()

# -------------------------------
# KPIs
# -------------------------------
total_sales = filtered["sales_value"].fillna(0).sum()
total_labor = filtered["actual_labor"].fillna(0).sum()
total_checks = int(filtered["check_count"].fillna(0).sum())

has_splh = filtered["sales_per_labor_hour"].notna().any()
if has_splh:
    splh_value = filtered["sales_per_labor_hour"].dropna().mean()
else:
    hours_sum = filtered["actual_hours"].fillna(0).sum()
    splh_value = (total_sales / hours_sum) if hours_sum else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Sales", fmt_currency(total_sales))
k2.metric("Labor $", fmt_currency(total_labor))
k3.metric("Checks", f"{total_checks:,}")
k4.metric("Sales / Labor Hour", fmt_currency(splh_value))

# -------------------------------
# Tabs: Charts / Table
# -------------------------------
tab_charts, tab_table = st.tabs(["📈 Charts", "🧾 Table"])

with tab_charts:
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

    st.subheader("Sales per Labor Hour (SPLH)")
    splh_df = filtered.copy()
    if not has_splh:
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
    cols_show = [
        "pc_number", "date", "hour_range",
        "actual_hours", "actual_labor",
        "sales_value", "check_count", "sales_per_labor_hour"
    ]
    table_df = filtered[cols_show].sort_values(by=["date", "_hour_key", "pc_number"])
    st.dataframe(table_df, use_container_width=True, hide_index=True)

    csv = table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download CSV",
        data=csv,
        file_name="hourly_sales_labor_filtered.csv",
        mime="text/csv",
    )

# -------------------------------
# Helper
# -------------------------------
with st.expander("ℹ️ How to use this page"):
    st.markdown(
        """
- Use the **sidebar** to filter by store(s), date range (with quick presets), and hour ranges.
- Checkbox filters support **search**, **Select All**, and **Clear**, similar to grid UIs.
- **Charts** show sales, labor, and SPLH by hour with proper hour sorting.
- **Table** provides an export of the filtered data.
- Click **Refresh** if you've just uploaded or updated data.
        """
    )
