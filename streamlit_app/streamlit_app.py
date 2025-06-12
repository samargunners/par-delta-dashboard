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

# --- Rolling 7-day window ---
today = datetime.now().date()
seven_days_ago = today - timedelta(days=7)

# --- Donut Overview Table ---
donut_resp = supabase.table("usage_donut_waste_and_gap_analysis") \
    .select("pc_number, calculated_waste, recorded_waste, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lt("date", today.isoformat()) \
    .execute()

donut_df = pd.DataFrame(donut_resp.data)
st.write("Donut DataFrame shape:", donut_df.shape)
st.write(donut_df.head())
if not donut_df.empty:
    donut_grouped = donut_df.groupby("pc_number").agg(
        Calculated_Waste_7d_Avg=("calculated_waste", "mean"),
        Recorded_Waste_7d_Avg=("recorded_waste", "mean")
    ).reset_index()
    donut_grouped["Gap"] = donut_grouped["Calculated_Waste_7d_Avg"] - donut_grouped["Recorded_Waste_7d_Avg"]
    donut_grouped.rename(columns={"pc_number": "PC Number"}, inplace=True)
    st.subheader("🍩 Donut Overview (Last 7 Days Rolling Avg)")
    st.dataframe(donut_grouped[["PC Number", "Calculated_Waste_7d_Avg", "Recorded_Waste_7d_Avg", "Gap"]])
else:
    st.info("No donut waste data available for the last 7 days.")

# --- Labor Overview Table ---
# Schedule
sched_resp = supabase.table("schedule_table_labour") \
    .select("pc_number, scheduled_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lt("date", today.isoformat()) \
    .execute()
sched_df = pd.DataFrame(sched_resp.data)

# Ideal
ideal_resp = supabase.table("ideal_table_labour") \
    .select("pc_number, ideal_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lt("date", today.isoformat()) \
    .execute()
ideal_df = pd.DataFrame(ideal_resp.data)

# Actual
actual_resp = supabase.table("actual_table_labour") \
    .select("pc_number, actual_hours, date") \
    .gte("date", seven_days_ago.isoformat()) \
    .lt("date", today.isoformat()) \
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
    st.subheader("⏱️ Labor Overview (Last 7 Days Rolling Total)")
    st.dataframe(labor[["PC Number", "Schedule_vs_Ideal_Var_%", "Schedule_vs_Actual_Var_%"]])
else:
    st.info("No labor data available for the last 7 days.")

st.markdown("""
---
Live data is loaded from Supabase.
""")
