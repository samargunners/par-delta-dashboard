import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px

if st.button("🔁 Clear Cache"):
    st.cache_data.clear()
    st.experimental_rerun()


# --- Streamlit Page Config ---
st.set_page_config(page_title="Inventory Variance", layout="wide")
st.title("📦 Inventory Variance Analysis")

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Load Data from Supabase ---
@st.cache_data(ttl=3600)
def load_all_rows(table):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table(table).select("*").range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

df = load_all_rows("variance_report_summary")

# --- Check if data is valid ---
if df.empty:
    st.warning("No data returned from Supabase. Please ensure the table has records.")
    st.stop()

required_cols = [
    "pc_number", "reporting_period", "subcategory", "product_name", "qty_variance",
    "variance", "cogs", "theoretical_value", "theoretical_qty", "units_sold"
]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"The following required columns are missing: {missing_cols}")
    st.stop()

# --- Data Type Cleanup ---
df["pc_number"] = df["pc_number"].astype(str)
df["reporting_period"] = df["reporting_period"].astype(str)

# --- Subcategory Filter ---
all_subcategories = sorted(df["subcategory"].dropna().unique())
default_subcategories = [
    "Bakery", "Beverages", "Coffee", "Condiments Non Deplete", "Cooler Beverages",
    "Cream Cheese", "Dairy", "Muffins", "Sandwiches & Wraps"
]
selected_subcategories = st.multiselect(
    "Filter by Subcategory",
    options=all_subcategories,
    default=[s for s in default_subcategories if s in all_subcategories]
)

df = df[df["subcategory"].isin(selected_subcategories)]

# --- Store & Period Filters ---
store_options = ["All"] + sorted(df["pc_number"].unique())
period_options = ["All"] + sorted(df["reporting_period"].unique(), reverse=True)

col1, col2 = st.columns(2)
with col1:
    location_filter = st.selectbox("Select Store", store_options)
with col2:
    reporting_period = st.selectbox("Select Reporting Period (Week)", period_options)

if location_filter != "All":
    df = df[df["pc_number"] == location_filter]

if reporting_period != "All":
    df = df[df["reporting_period"] == reporting_period]

# --- Calculated Fields ---
df["Theoretical Cost Variance"] = df["theoretical_value"] - df["cogs"]
df["Unit Gap"] = df["theoretical_qty"] - df["units_sold"]

# --- Summary Table ---
summary = df[[
    "reporting_period", "product_name", "qty_variance", "variance", "cogs"
]].rename(columns={
    "qty_variance": "Variance Qty",
    "variance": "Variance $",
    "cogs": "COGS"
})

st.subheader("📋 Inventory Variance Summary")
st.dataframe(summary, use_container_width=True)

# --- Charts ---
# Chart 1: Top 10 Variance Qty
st.subheader("🔟 Top 10 Variance by Quantity")
top_qty_variance = df.reindex(df["qty_variance"].abs().sort_values(ascending=False).index).head(10)
top_qty_variance = top_qty_variance.sort_values("qty_variance", ascending=True)

if not top_qty_variance.empty:
    fig1 = px.bar(
        top_qty_variance,
        x="qty_variance",
        y="product_name",
        orientation="h",
        labels={"qty_variance": "Variance Qty", "product_name": "Product Name"},
        title="Top 10 Variance by Quantity",
        color="qty_variance",
        color_continuous_scale="Purples",
        hover_data=["reporting_period", "qty_variance", "variance"]
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("No data available for selected filters.")

# Chart 2: Top 10 Variance $
st.subheader("🔟 Top 10 Variance by $")
top_value_variance = df.reindex(df["variance"].abs().sort_values(ascending=False).index).head(10)
top_value_variance = top_value_variance.sort_values("variance", ascending=True)

if not top_value_variance.empty:
    fig2 = px.bar(
        top_value_variance,
        x="variance",
        y="product_name",
        orientation="h",
        labels={"variance": "Variance $", "product_name": "Product Name"},
        title="Top 10 Variance by $",
        color="variance",
        color_continuous_scale="Oranges",
        hover_data=["reporting_period", "variance"]
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No data available for selected filters.")
