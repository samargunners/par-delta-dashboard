import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Hourly Sales & Labor", layout="wide")
st.title("📊 Hourly Sales & Labor")

# --- Data Fetching Function ---
@st.cache_data(ttl=3600)
def load_all_rows(table, columns="*"):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table(table).select(columns).range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

# --- Load Data ---
df = load_all_rows(
    "actual_table_labor",
    columns="pc_number,date,hour_range,actual_hours,actual_labor,sales_value,check_count,sales_per_labor_hour"
)

if df.empty:
    st.error("❌ No data found in actual_table_labor table.")
    st.stop()

# --- Preprocessing ---
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
df["pc_number"] = df["pc_number"].astype(str)
df["hour_range"] = df["hour_range"].astype(str)

# --- Filters ---
stores = sorted(df["pc_number"].unique())
store_filter = st.multiselect("Select Store(s) / PC Number(s)", stores, default=stores)
dates = sorted(df["date"].unique())
date_filter = st.date_input("Select Date(s)", value=[min(dates), max(dates)])
hours = sorted(df["hour_range"].unique())
hour_filter = st.multiselect("Select Hour Range(s)", hours, default=hours)

# --- Filter Data ---
filtered_df = df[
    df["pc_number"].isin(store_filter) &
    df["date"].between(date_filter[0], date_filter[-1]) &
    df["hour_range"].isin(hour_filter)
]

st.write("### Filtered Hourly Sales & Labor Data", filtered_df)

# --- Visualization ---
if not filtered_df.empty:
    fig = px.bar(
        filtered_df,
        x="hour_range",
        y="sales_value",
        color="pc_number",
        barmode="group",
        title="Hourly Sales Value by Store"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(
        filtered_df,
        x="hour_range",
        y="actual_labor",
        color="pc_number",
        title="Hourly Labor by Store"
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data for selected filters.")
