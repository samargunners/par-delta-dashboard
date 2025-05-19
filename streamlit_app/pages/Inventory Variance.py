import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Inventory Variance", layout="wide")
st.title("📦 Inventory Variance Analysis")

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data():
    return pd.DataFrame(supabase.table("variance_report_summary").select("*").execute().data)

df = load_data()
df["pc_number"] = df["pc_number"].astype(str)
df["reporting_period"] = df["reporting_period"].astype(str)

# --- Filters ---
store_options = ["All"] + sorted(df["pc_number"].unique())
period_options = ["All"] + sorted(df["reporting_period"].unique())

location_filter = st.selectbox("Select Store", store_options)
reporting_period = st.selectbox("Select Reporting Period (Week)", period_options)

# --- Apply Filters ---
if location_filter != "All":
    df = df[df["pc_number"] == location_filter]

if reporting_period != "All":
    df = df[df["reporting_period"] == reporting_period]

# --- Key Metrics ---
df["Theoretical Cost Variance"] = df["theoretical_value"] - df["cogs"]
df["Unit Gap"] = df["theoretical_qty"] - df["units_sold"]

# --- Summary Table ---
summary = df[[
    "pc_number", "reporting_period", "product_name", "subcategory", "inventory_unit",
    "beginning_inv_qty", "ending_inv_qty", "purchases_qty", "units_sold",
    "waste", "variance", "qty_variance", "theoretical_qty", "Unit Gap",
    "cogs", "theoretical_value", "Theoretical Cost Variance"
]]

st.subheader("📋 Inventory Variance Summary")
st.dataframe(summary)

# --- Charts ---
st.subheader("📉 Top Variance by Product")
top_variance = df.sort_values("variance", ascending=False).head(15)
if not top_variance.empty:
    st.bar_chart(top_variance.set_index("product_name")["variance"])
else:
    st.info("No data available for selected filters.")