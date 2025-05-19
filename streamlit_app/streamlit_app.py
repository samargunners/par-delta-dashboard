
import streamlit as st

st.set_page_config(page_title="Par Delta Dashboard", layout="wide")
st.title("📊 Par Delta Operational Dashboard")

st.markdown("""
Welcome to the central dashboard for Dunkin' operations at Par Delta.  
Use the left sidebar to navigate between modules:
- 🍩 Donut Waste & Gap
- ⏱️ Labor Punctuality
- 💼 Ideal vs Actual Labor
- 📦 Inventory Variance

Live data is loaded from Supabase.
""")
