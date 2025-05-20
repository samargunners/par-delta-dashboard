import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import matplotlib.pyplot as plt
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Inventory Variance", layout="wide")
st.title("📦 Inventory Variance Analysis")

# --- Load Data with Pagination ---
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
df["pc_number"] = df["pc_number"].astype(str)
df["reporting_period"] = df["reporting_period"].astype(str)

# --- Remove unwanted subcategories ---
df = df[~df["subcategory"].str.lower().isin(["donuts", "fancies", "munchkins"])]

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
    "purchases_value"
]].rename(columns={
    "qty_variance": "Variance Qty",
    "variance": "Variance $",
    "units_sold": "Units Sold",
    "cogs": "COGS $",
    "purchases_qty": "Purchase Qty",
    "purchases_value": "Purchase $"
})

st.subheader("📋 Inventory Variance Summary")
st.dataframe(summary)

# --- Charts ---
# Chart 1: Top 10 by absolute Variance Qty (sorted biggest to smallest)
st.subheader("🔟 Top 10 Variance by Quantity")
top_qty_variance = df.reindex(df["qty_variance"].abs().sort_values(ascending=False).index).head(10)
top_qty_variance = top_qty_variance.sort_values("qty_variance", ascending=True)  # for horizontal bar

if not top_qty_variance.empty:
    fig1 = px.bar(
        top_qty_variance,
        x="qty_variance",
        y="product_name",
        orientation="h",
        labels={"qty_variance": "Variance Qty", "product_name": "Product Name"},
        title="Top 10 Variance by Quantity",
        color="qty_variance",
        color_continuous_scale="Blues",
        hover_data=["reporting_period", "qty_variance"]
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("No data available for selected filters.")

# Chart 2: Top 10 by absolute Variance $ (sorted biggest to smallest)
st.subheader("🔟 Top 10 Variance by $")
top_value_variance = df.reindex(df["variance"].abs().sort_values(ascending=False).index).head(10)
top_value_variance = top_value_variance.sort_values("variance", ascending=True)  # for horizontal bar

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