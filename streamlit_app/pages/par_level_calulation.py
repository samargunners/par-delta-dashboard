import streamlit as st
import pandas as pd
from streamlit_app.dashboard import par_engine

st.set_page_config(page_title="Par Level Calculation", layout="wide")
st.title("📊 Par Level Calculation System (Cycle-Based)")

st.markdown("""
This system calculates **cycle-based par levels** from NDCP invoice history.

**Cycle Par concept:**
- It determines the **next order day** and the **delivery date** for that order.
- Then it computes how many days that delivery must cover until the **next delivery**.
- Par = Daily Usage Rate × Cycle Days × (1 + Safety %)

Next step (later): add **On Hand** to compute **Suggested Order = Par − On Hand**.
""")

# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.header("⚙️ Settings")

window_days = st.sidebar.slider(
    "History Window (days)",
    min_value=30,
    max_value=180,
    value=90,
    help="How many days of invoice history to use for computing daily usage."
)

safety_percent = st.sidebar.slider(
    "Safety Buffer %",
    min_value=0,
    max_value=50,
    value=20,
    help="Extra buffer added on top of expected demand."
)

# ---------------------------
# Compute results
# ---------------------------
with st.spinner("Calculating cycle-based par levels..."):
    par_df, ctx_df = par_engine.get_par_for_next_order(
        pc_number=None,
        window_days=window_days,
        safety_percent=safety_percent
    )

if par_df.empty:
    st.warning("No data available for par level calculation. Please ensure ndcp_invoices table has data.")
    st.stop()

# ---------------------------
# Store filter
# ---------------------------
stores_list = ['All Stores'] + sorted(par_df['pc_number'].unique().tolist())
selected_store = st.sidebar.selectbox("Filter by Store (PC Number)", stores_list)

if selected_store != "All Stores":
    par_df = par_df[par_df["pc_number"] == selected_store].copy()
    ctx_df = ctx_df[ctx_df["pc_number"] == selected_store].copy()

# ---------------------------
# Order context display
# ---------------------------
st.subheader("🗓️ Next Order Context")

if not ctx_df.empty:
    # Context is same for all stores right now, but ctx_df supports per-store overrides later.
    c = ctx_df.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Today", str(c["today"]))
    with col2:
        st.metric("Next Order Date", str(c["next_order_date"]))
    with col3:
        st.metric("Delivery Date (for that order)", str(c["next_delivery_date_for_order"]))
    with col4:
        st.metric("Next Delivery After That", str(c["next_delivery_after_that"]))
    with col5:
        st.metric("Cycle Days", int(c["cycle_days"]))

    st.info(
        f"**Cadence:** {c['cadence_type']}  |  "
        f"**Safety Buffer:** {safety_percent}%  |  "
        f"**History Window:** {window_days} days"
    )
else:
    st.info("Context not available (unexpected).")

# ---------------------------
# Results table
# ---------------------------
st.subheader("📦 Cycle Par Results")

display_cols = [
    "pc_number",
    "item_number",
    "item_name",
    "category",
    "daily_usage_rate",
    "cycle_days",
    "par_quantity",
    "num_orders",
    "total_qty",
]
df_display = par_df[display_cols].copy()
df_display["daily_usage_rate"] = df_display["daily_usage_rate"].round(4)

st.dataframe(df_display, use_container_width=True, height=500)

# ---------------------------
# Summary stats
# ---------------------------
colA, colB, colC = st.columns(3)
with colA:
    st.metric("Total Items", len(par_df))
with colB:
    st.metric("Total Par Units", int(par_df["par_quantity"].sum()))
with colC:
    st.metric("Avg Par per Item", int(par_df["par_quantity"].mean()) if len(par_df) else 0)

# ---------------------------
# Download
# ---------------------------
st.download_button(
    label="📥 Download Cycle Par (CSV)",
    data=par_df.to_csv(index=False),
    file_name=f"cycle_par_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)
