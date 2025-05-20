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

# --- Filters ---
location_filter = st.selectbox("Select Store", ["All"] + [
    "301290", "357993", "343939", "358529", "359042", "364322", "363271"
])
date_range = st.date_input("Select Date Range", [])

# --- Data Fetching ---
@st.cache_data(ttl=3600)
def load_data(table):
    return pd.DataFrame(supabase.table(table).select("*").execute().data)

sales_df = load_data("donut_sales_hourly")
usage_df = load_data("usage_overview")

# --- Preprocessing ---
sales_df["date"] = pd.to_datetime(sales_df["date"]).dt.date
sales_df["time"] = pd.to_datetime(sales_df["time"], format="%H:%M:%S").dt.time  # Adjust format if needed
sales_df["hour"] = pd.to_datetime(sales_df["time"], format="%H:%M:%S").dt.hour
sales_df["pc_number"] = sales_df["pc_number"].astype(str)
sales_df["product_type"] = sales_df["product_type"].astype(str).str.lower()
donut_sales = sales_df[sales_df["product_type"] == "donut"]

sales_summary = donut_sales.groupby(["pc_number", "date"]).agg(SalesQty=("quantity", "sum")).reset_index()

usage_df["date"] = pd.to_datetime(usage_df["date"]).dt.date
usage_df["pc_number"] = usage_df["pc_number"].astype(str)
usage_df["product_type"] = usage_df["product_type"].astype(str).str.lower()
usage_donuts = usage_df[usage_df["product_type"] == "donuts"]

# --- Apply filters ---
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

# --- Table ---
st.subheader("📋 Donut Usage Summary")
st.dataframe(merged)

# --- Graph 1: Trend line for Ordered Qty, Sales Qty, Waste ---
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

# --- Graph 2: Gap Analysis Trend ---
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

# --- Graph 3: Hourly Donut Count for Selected Store and Date ---
st.subheader("⏰ Hourly Donut Count (Select Store & Date)")
col1, col2 = st.columns(2)
with col1:
    pc_hourly = st.selectbox("Select Store for Hourly Chart", sorted(usage_df["pc_number"].unique()))
with col2:
    date_hourly = st.date_input("Select Date for Hourly Chart", value=None)

if pc_hourly and date_hourly:
    # Get ordered_qty for the day from usage_overview and use as opening stock
    usage_row = usage_df[
        (usage_df["pc_number"] == pc_hourly) &
        (usage_df["date"] == date_hourly) &
        (usage_df["product_type"] == "donuts")
    ]
    if not usage_row.empty:
        ordered_qty = usage_row.iloc[0]["ordered_qty"]
        opening_stock = ordered_qty  # Opening stock is always ordered_qty
        wasted_qty = usage_row.iloc[0]["wasted_qty"]
        # Filter sales for this store and date
        sales_hourly = donut_sales[
            (donut_sales["pc_number"] == pc_hourly) &
            (donut_sales["date"] == date_hourly)
        ]
        hourly_sales = sales_hourly.groupby("hour").agg(SalesQty=("quantity", "sum")).sort_index().reset_index()
        # Calculate running total sold
        hourly_sales["CumulativeSales"] = hourly_sales["SalesQty"].cumsum()
        # Calculate donuts left after each hour
        hourly_sales["DonutsLeft"] = opening_stock - hourly_sales["CumulativeSales"]
        fig3 = px.line(
            hourly_sales, x="hour", y="DonutsLeft",
            labels={"hour": "Hour of Day", "DonutsLeft": "Donuts Left"},
            title=f"Hourly Donut Count for Store {pc_hourly} on {date_hourly}",
            markers=True
        )
        fig3.update_traces(mode="lines+markers", hovertemplate='Hour %{x}: %{y} donuts left')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No usage data for selected store and date.")