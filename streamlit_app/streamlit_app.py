import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client

st.set_page_config(page_title="Par Delta Dashboard", layout="wide")
st.title("📊 Par Delta Operational Dashboard")

st.markdown("""
Welcome to the central dashboard for Dunkin' operations at Par Delta.  
Select a module below to navigate:
""")

# Use correct relative paths
st.page_link("pages/Donut_Waste_&_Gap.py", label="Donut Waste & Gap", icon="🍩")
st.page_link("pages/Labor_Punctuality.py", label="Labor Punctuality", icon="⏱️")
st.page_link("pages/Ideal_vs_Actual_Labor.py", label="Ideal vs Actual Labor", icon="💼")
st.page_link("pages/Inventory_Variance.py", label="Inventory Variance", icon="📦")
st.page_link("pages/Retail_Merchandise.py", label="Retail Merchandise", icon="🛍️")

st.markdown("""
---
Live data is loaded from Supabase.
""")

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Load Data for Home Page Overview ---
@st.cache_data(ttl=3600)
def load_all_rows(table):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        try:
            response = supabase.table(table).select("*").range(offset, offset + chunk_size - 1).execute()
        except Exception as e:
            st.error(f"Error loading table '{table}': {e}")
            break
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

sales_df = load_all_rows("donut_sales_hourly")
usage_df = load_all_rows("usage_overview")

# --- Preprocessing ---
sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce").dt.date
sales_df["pc_number"] = sales_df["pc_number"].astype(str).str.strip().str.zfill(6)
sales_df["product_type"] = sales_df["product_type"].astype(str).str.lower()

usage_df["date"] = pd.to_datetime(usage_df["date"], errors="coerce").dt.date
usage_df["pc_number"] = usage_df["pc_number"].astype(str).str.strip().str.zfill(6)
usage_df["product_type"] = usage_df["product_type"].astype(str).str.lower()

# --- Calculate rolling 7-day window (Sunday to Saturday) ---
today = datetime.now().date()
# Find the most recent Saturday (weekday 5 = Saturday)
days_since_saturday = (today.weekday() + 2) % 7  # Convert to days since Saturday
last_saturday = today - timedelta(days=days_since_saturday)
seven_days_ago = last_saturday - timedelta(days=6)  # 7 days total including Saturday

# --- Filter for last 7 days and only donuts ---
donut_sales = sales_df[
    (sales_df["product_type"].str.contains("donut", na=False)) &
    (sales_df["date"] >= seven_days_ago) & (sales_df["date"] <= last_saturday)
]
usage_donuts = usage_df[
    (usage_df["product_type"].str.contains("donut", na=False)) &
    (usage_df["date"] >= seven_days_ago) & (usage_df["date"] <= last_saturday)
]

# --- Aggregate sales by date and pc_number ---
sales_summary = donut_sales.groupby(["date", "pc_number"]).agg(SalesQty=("quantity", "sum")).reset_index()

# --- Merge and calculate ---
merged = pd.merge(usage_donuts, sales_summary, on=["date", "pc_number"], how="left")
merged["SalesQty"] = merged["SalesQty"].fillna(0)
merged["CalculatedWaste"] = merged["ordered_qty"] - merged["SalesQty"]
merged["Gap"] = merged["CalculatedWaste"] - merged["wasted_qty"]

# --- Rolling 7-day averages per pc_number ---
donut_overview = merged.groupby("pc_number").agg(
    Calculated_Waste_7d_Avg=("CalculatedWaste", "mean"),
    Recorded_Waste_7d_Avg=("wasted_qty", "mean"),
    Gap=("Gap", "mean")
).reset_index()
donut_overview.rename(columns={"pc_number": "PC Number"}, inplace=True)

st.subheader(
    f"🍩 Donut Overview (Last 7 Days: {seven_days_ago.strftime('%Y-%m-%d')} to {last_saturday.strftime('%Y-%m-%d')})"
)
st.dataframe(donut_overview[["PC Number", "Calculated_Waste_7d_Avg", "Recorded_Waste_7d_Avg", "Gap"]])

# --- Labor Overview Table ---
# Schedule
sched_resp = supabase.table("schedule_table_labor") \
    .select("pc_number, scheduled_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lte("date", last_saturday.isoformat()) \
    .execute()
sched_df = pd.DataFrame(sched_resp.data)

# Ideal
ideal_resp = supabase.table("ideal_table_labor") \
    .select("pc_number, ideal_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lte("date", last_saturday.isoformat()) \
    .execute()
ideal_df = pd.DataFrame(ideal_resp.data)

# Actual
actual_resp = supabase.table("actual_table_labor") \
    .select("pc_number, actual_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lte("date", last_saturday.isoformat()) \
    .execute()
actual_df = pd.DataFrame(actual_resp.data)

# Merge and calculate variances
if not sched_df.empty and not ideal_df.empty and not actual_df.empty:
    sched_sum = sched_df.groupby("pc_number")["scheduled_hours"].sum().reset_index()
    ideal_sum = ideal_df.groupby("pc_number")["ideal_hours"].sum().reset_index()
    actual_sum = actual_df.groupby("pc_number")["actual_hours"].sum().reset_index()

    labor = sched_sum.merge(ideal_sum, on="pc_number", how="outer").merge(actual_sum, on="pc_number", how="outer").fillna(0)
    labor["Schedule_vs_Ideal_Var_%"] = ((labor["scheduled_hours"] - labor["ideal_hours"]) / labor["ideal_hours"].replace(0, 1)) * 100
    labor["Schedule_vs_Actual_Var_%"] = ((labor["scheduled_hours"] - labor["actual_hours"]) / labor["actual_hours"].replace(0, 1)) * 100
    labor.rename(columns={"pc_number": "PC Number"}, inplace=True)
    st.subheader(
        f"⏱️ Labor Overview (Last 7 Days: {seven_days_ago.strftime('%Y-%m-%d')} to {last_saturday.strftime('%Y-%m-%d')})"
    )
    st.dataframe(labor[["PC Number", "Schedule_vs_Ideal_Var_%", "Schedule_vs_Actual_Var_%"]])
else:
    st.info("No labor data available for the last 7 days.")


