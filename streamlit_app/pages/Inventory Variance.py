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
    "reporting_period",
    "product_name",
    "qty_variance",
    "variance",
    "units_sold",
    "cogs",
    "purchases_qty",
    "purchase_value"
]].rename(columns={
    "qty_variance": "Variance Qty",
    "variance": "Variance $",
    "units_sold": "Units Sold",
    "cogs": "COGS $",
    "purchases_qty": "Purchase Qty",
    "purchase_value": "Purchase $"
})

st.subheader("📋 Inventory Variance Summary")
st.dataframe(summary)

# --- Charts ---
# Chart 1: Top 10 by absolute Variance Qty
st.subheader("🔟 Top 10 Variance by Quantity")
top_qty_variance = df.reindex(df["qty_variance"].abs().sort_values(ascending=False).index).head(10)
if not top_qty_variance.empty:
    st.bar_chart(top_qty_variance.set_index("product_name")["qty_variance"].rename("Variance Qty"))
else:
    st.info("No data available for selected filters.")

# Chart 2: Top 10 by absolute Variance $
st.subheader("🔟 Top 10 Variance by $")
top_value_variance = df.reindex(df["variance"].abs().sort_values(ascending=False).index).head(10)
if not top_value_variance.empty:
    st.bar_chart(top_value_variance.set_index("product_name")["variance"].rename("Variance $"))
else:
    st.info("No data available for selected filters.")