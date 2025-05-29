import streamlit as st

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

st.markdown("""
---
Live data is loaded from Supabase.
""")
