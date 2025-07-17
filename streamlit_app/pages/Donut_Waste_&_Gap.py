import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Donut Waste & Gap", layout="wide")
st.title("🍩 Donut Waste & Gap Analysis")

# --- Data Fetching Function ---
@st.cache_data(ttl=3600)
def load_all_rows(table):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table(table).select("*").range(offset, offset + chunk_size - 1).execute()

        st.sidebar.write(f"Chunk from `{table}` at offset {offset}:", response.data)

        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size

    df = pd.DataFrame(all_data)
    st.sidebar.write(f"Loaded DataFrame for `{table}`:", df.head())
    st.sidebar.write("Final columns:", df.columns.tolist())
    return df


# --- Load Data ---
sales_df = load_all_rows("donut_sales_hourly")
st.sidebar.write("Sales column names:", sales_df.columns.tolist())
st.sidebar.write("First 5 rows:", sales_df.head())
usage_df = load_all_rows("usage_overview")

# --- Preprocessing ---
sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce").dt.date
sales_df["pc_number"] = sales_df["pc_number"].astype(str).str.strip().str.zfill(6)
sales_df["time"] = pd.to_datetime(sales_df["time"], format="%H:%M:%S", errors="coerce").dt.time
sales_df["hour"] = pd.to_datetime(sales_df["time"], format="%H:%M:%S", errors="coerce").dt.hour
sales_df["product_type"] = sales_df["product_type"].astype(str).str.lower()

usage_df["date"] = pd.to_datetime(usage_df["date"], errors="coerce").dt.date
usage_df["pc_number"] = usage_df["pc_number"].astype(str).str.strip().str.zfill(6)
usage_df["product_type"] = usage_df["product_type"].astype(str).str.lower()

# --- Filter Setup ---
location_filter = st.selectbox("Select Store", ["All"] + sorted(sales_df["pc_number"].unique()))
min_date = min(sales_df["date"].min(), usage_df["date"].min())
max_date = max(sales_df["date"].max(), usage_df["date"].max())
date_range = st.date_input("Select Date Range", [min_date, max_date])

# --- Apply Initial Filters ---
donut_sales = sales_df[sales_df["product_type"].str.contains("donut", na=False)]
sales_summary = donut_sales.groupby(["date", "pc_number"]).agg(SalesQty=("quantity", "sum")).reset_index()

usage_donuts = usage_df[usage_df["product_type"].str.contains("donut", na=False)]

if location_filter != "All":
    usage_donuts = usage_donuts[usage_donuts["pc_number"] == location_filter]
    sales_summary = sales_summary[sales_summary["pc_number"] == location_filter]
    donut_sales = donut_sales[donut_sales["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0]).date()
    end_date = pd.to_datetime(date_range[1]).date()
    usage_donuts = usage_donuts[(usage_donuts["date"] >= start_date) & (usage_donuts["date"] <= end_date)]
    sales_summary = sales_summary[(sales_summary["date"] >= start_date) & (sales_summary["date"] <= end_date)]
    donut_sales = donut_sales[(donut_sales["date"] >= start_date) & (donut_sales["date"] <= end_date)]

# --- Merge & Calculate ---
merged = pd.merge(usage_donuts, sales_summary, on=["date", "pc_number"], how="left")
merged["SalesQty"] = merged["SalesQty"].fillna(0)
merged["CalculatedWaste"] = merged["ordered_qty"] - merged["SalesQty"]
merged["Gap"] = merged["CalculatedWaste"] - merged["wasted_qty"]
merged["DonutCost"] = merged["wasted_qty"] * 0.36

# --- Table Output ---
st.subheader("📋 Donut Usage Summary")
st.dataframe(merged)

# --- Graph 1: Ordered, Sales, Waste Trend ---
st.subheader("📈 Donut Ordered, Sold, and Waste Trend")
pivot1 = merged.groupby("date").agg({
    "ordered_qty": "sum",
    "SalesQty": "sum",
    "wasted_qty": "sum"
}).reset_index()

fig1 = px.line(
    pivot1, x="date",
    y=["ordered_qty", "SalesQty", "wasted_qty"],
    labels={"value": "Quantity", "date": "Date", "variable": "Metric"},
    title="Ordered Qty, Sales Qty, and Waste Over Time",
    markers=True
)
fig1.update_traces(mode="lines+markers", hovertemplate='%{y}')
st.plotly_chart(fig1, use_container_width=True)

# --- Graph 2: Gap Trend ---
st.subheader("📉 Donut Waste Gap Analysis Trend")
pivot2 = merged.groupby("date").agg({
    "CalculatedWaste": "sum",
    "wasted_qty": "sum"
}).reset_index()
pivot2["Gap"] = pivot2["CalculatedWaste"] - pivot2["wasted_qty"]

fig2 = px.line(
    pivot2, x="date", y="Gap",
    labels={"Gap": "Gap (Expected Waste - Actual Waste)", "date": "Date"},
    title="Gap Analysis Over Time",
    markers=True
)
fig2.update_traces(mode="lines+markers", hovertemplate='Gap: %{y}')
st.plotly_chart(fig2, use_container_width=True)

# --- Graph 3: Hourly Donut Count ---
st.subheader("⏰ Hourly Donut Count (Select Store & Date)")
col1, col2 = st.columns(2)
with col1:
    pc_hourly = st.selectbox("Select Store for Hourly Chart", sorted(usage_df["pc_number"].unique()))
with col2:
    date_hourly = st.date_input("Select Date for Hourly Chart", value=None)

if pc_hourly and date_hourly:
    usage_row = usage_df[
        (usage_df["pc_number"] == pc_hourly) &
        (usage_df["date"] == date_hourly) &
        (usage_df["product_type"].str.contains("donut", na=False))
    ]
    if not usage_row.empty:
        ordered_qty = usage_row.iloc[0]["ordered_qty"]
        opening_stock = ordered_qty
        wasted_qty = usage_row.iloc[0]["wasted_qty"]

        sales_hourly = donut_sales[
            (donut_sales["pc_number"] == pc_hourly) &
            (donut_sales["date"] == date_hourly)
        ]
        hourly_sales = sales_hourly.groupby("hour").agg(SalesQty=("quantity", "sum")).sort_index().reset_index()
        hourly_sales["CumulativeSales"] = hourly_sales["SalesQty"].cumsum()
        hourly_sales["DonutsLeft"] = opening_stock - hourly_sales["CumulativeSales"]

        fig3 = px.line(
            hourly_sales, x="hour", y="DonutsLeft",
            labels={"hour": "Hour of Day", "DonutsLeft": "Donuts Left"},
            title=f"Hourly Donut Count for Store {pc_hourly} on {date_hourly}",
            markers=True
        )
        fig3.update_traces(mode="lines+markers", hovertemplate='%{y} donuts left')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No usage data for selected store and date.")
