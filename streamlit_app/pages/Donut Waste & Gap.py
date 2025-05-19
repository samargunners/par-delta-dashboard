import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

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
sales_df["sale_datetime"] = pd.to_datetime(sales_df["sale_datetime"])
sales_df["date"] = sales_df["sale_datetime"].dt.date
sales_df["pc_number"] = sales_df["pc_number"].astype(str)
sales_df["product_type"] = sales_df["product_type"].astype(str).str.lower()
donut_sales = sales_df[sales_df["product_type"] == "donut"]

sales_summary = donut_sales.groupby(["date", "pc_number"]).agg(SalesQty=("quantity", "sum")).reset_index()

usage_df["date"] = pd.to_datetime(usage_df["date"]).dt.date
usage_df["pc_number"] = usage_df["pc_number"].astype(str)
usage_df["product_type"] = usage_df["product_type"].astype(str).str.lower()
usage_donuts = usage_df[usage_df["product_type"] == "donuts"]

# --- Apply filters ---
if location_filter != "All":
    usage_donuts = usage_donuts[usage_donuts["pc_number"] == location_filter]
    sales_summary = sales_summary[sales_summary["pc_number"] == location_filter]

if date_range and len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0]).date()
    end_date = pd.to_datetime(date_range[1]).date()
    usage_donuts = usage_donuts[(usage_donuts["date"] >= start_date) & (usage_donuts["date"] <= end_date)]
    sales_summary = sales_summary[(sales_summary["date"] >= start_date) & (sales_summary["date"] <= end_date)]

# --- Merge & Calculate ---
merged = pd.merge(usage_donuts, sales_summary, on=["date", "pc_number"], how="left")
merged["SalesQty"] = merged["SalesQty"].fillna(0)
merged["CalculatedWaste"] = merged["ordered_qty"] - merged["SalesQty"]
merged["Gap"] = merged["CalculatedWaste"] - merged["wasted_qty"]
merged["DonutCost"] = merged["wasted_qty"] * 0.36

# --- Display ---
st.subheader("📋 Donut Usage Summary")
st.dataframe(merged)

# --- Charts ---
st.subheader("📈 Donut Waste vs Sales Over Time")
pivot = merged.groupby("date").agg({
    "ordered_qty": "sum",
    "SalesQty": "sum",
    "wasted_qty": "sum",
    "CalculatedWaste": "sum"
}).reset_index()

st.line_chart(pivot.set_index("date"))