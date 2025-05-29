import streamlit as st

st.set_page_config(page_title="Par Delta Dashboard", layout="wide")
st.title("📊 Par Delta Operational Dashboard")

st.markdown("""
Welcome to the central dashboard for Dunkin' operations at Par Delta.  
Use the left sidebar to navigate between modules:
""")

# Sidebar navigation
page = st.sidebar.selectbox(
    "Navigate to module:",
    [
        "🍩 Donut Waste & Gap",
        "⏱️ Labor Punctuality",
        "💼 Ideal vs Actual Labor",
        "📦 Inventory Variance"
    ]
)

if page == "🍩 Donut Waste & Gap":
    st.header("🍩 Donut Waste & Gap")
    st.write("Go to: [Donut Waste & Gap](Donut_Waste_and_Gap)")
elif page == "⏱️ Labor Punctuality":
    st.header("⏱️ Labor Punctuality")
    st.write("Go to: [Labor Punctuality](Labor_Punctuality)")
elif page == "💼 Ideal vs Actual Labor":
    st.header("💼 Ideal vs Actual Labor")
    st.write("Go to: [Ideal vs Actual Labor](Ideal_vs_Actual_Labor)")
elif page == "📦 Inventory Variance":
    st.header("📦 Inventory Variance")
    st.write("Go to: [Inventory Variance](Inventory_Variance)")

st.markdown("""
---
Live data is loaded from Supabase.
""")
