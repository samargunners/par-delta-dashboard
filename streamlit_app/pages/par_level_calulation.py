import streamlit as st
import pandas as pd
from dashboard import par_engine

st.set_page_config(page_title="Par Level Calculation", layout="wide")
st.title("📊 Par Level Calculation System")

st.markdown("""
This system calculates inventory par levels using historical variance data. 
Par levels help determine optimal stock quantities to maintain for each item.
""")

# --- Configuration Section ---
st.sidebar.header("⚙️ Par Calculation Settings")

# Fetch available par calculation methods
df_methods = par_engine.get_par_methods()
method_options = df_methods['method_name'].tolist()
method_keys = df_methods['method_key'].tolist()

selected_method_name = st.sidebar.selectbox("Select Calculation Method", method_options)
selected_key = method_keys[method_options.index(selected_method_name)]

# Show method description
method_desc = df_methods[df_methods['method_key'] == selected_key]['description'].iloc[0]
st.sidebar.info(f"**Method:** {method_desc}")

# Configuration parameters
coverage_days = st.sidebar.slider("Coverage Days", min_value=7, max_value=60, value=14, 
                                   help="Number of days of inventory to maintain")
safety_percent = st.sidebar.slider("Safety Buffer %", min_value=0, max_value=50, value=20,
                                    help="Additional safety stock percentage")

# --- Calculate Par Levels ---
with st.spinner("Calculating par levels..."):
    df_results = par_engine.get_par_results(selected_key, coverage_days, safety_percent)

# --- Store Filter ---
if not df_results.empty:
    stores_list = ['All Stores'] + sorted(df_results['pc_number'].unique().tolist())
    selected_store = st.sidebar.selectbox("Filter by Store", stores_list)
    
    # Apply store filter
    if selected_store != 'All Stores':
        df_results = df_results[df_results['pc_number'] == selected_store]

# --- Display Results ---
if df_results.empty:
    st.warning("No data available for par level calculation. Please ensure variance_report_summary table has data.")
    st.stop()

st.subheader("📦 Par Level Results")
st.markdown(f"**Method:** {selected_method_name} | **Coverage:** {coverage_days} days | **Safety Buffer:** {safety_percent}%")

# Format and display results
display_cols = ['pc_number', 'item_name', 'daily_usage_rate', 'par_quantity', 
                'avg_units_sold', 'total_units_sold', 'num_periods']
df_display = df_results[display_cols].copy()

# Format numeric columns
df_display['daily_usage_rate'] = df_display['daily_usage_rate'].round(2)
df_display['par_quantity'] = df_display['par_quantity'].astype(int)
df_display['avg_units_sold'] = df_display['avg_units_sold'].round(2)

st.dataframe(df_display, use_container_width=True, height=400)

# --- Summary Stats ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Items", len(df_results))
with col2:
    st.metric("Total Par Units", int(df_results['par_quantity'].sum()))
with col3:
    st.metric("Avg Par per Item", int(df_results['par_quantity'].mean()))

# --- Item Detail Section ---
st.subheader("🔍 Item Detail & Explanation")
with st.expander("View detailed metrics for specific item"):
    col_a, col_b = st.columns(2)
    with col_a:
        stores = ['All'] + sorted(df_results['pc_number'].unique().tolist())
        selected_store = st.selectbox("Store (PC Number)", stores)
    with col_b:
        items = ['All'] + sorted(df_results['item_name'].unique().tolist())
        selected_item = st.selectbox("Item Name", items)
    
    if selected_item != 'All' or selected_store != 'All':
        item_filter = selected_item if selected_item != 'All' else None
        store_filter = selected_store if selected_store != 'All' else None
        
        df_metrics = par_engine.get_inventory_metrics(item_filter, store_filter)
        if not df_metrics.empty:
            st.dataframe(df_metrics, use_container_width=True)
        else:
            st.info("No metrics available for selected filters.")

# --- Download Results ---
st.download_button(
    label="📥 Download Par Levels (CSV)",
    data=df_results.to_csv(index=False),
    file_name=f"par_levels_{selected_key}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)