import streamlit as st
import pandas as pd
from dashboard import par_engine

st.title("Par Level Calculation System")

# Fetch available par calculation methods
df_methods = par_engine.get_par_methods()
method_options = df_methods['method_name'].tolist()
method_keys = df_methods['method_key'].tolist()

selected_method = st.selectbox("Select Par Calculation Method", method_options)
selected_key = method_keys[method_options.index(selected_method)]

# Fetch par results for selected method
df_results = par_engine.get_par_results(selected_key)
st.subheader("Par Results Table")
st.dataframe(df_results)

# Optionally, show explanation/metrics for selected item
st.subheader("Item Metrics & Explanation")
if st.checkbox("Show metrics for selected item?"):
    item_number = st.text_input("Enter Item Number")
    pc_number = st.text_input("Enter Store (PC) Number")
    if item_number:
        df_metrics = par_engine.get_inventory_metrics(item_number, pc_number)
        st.dataframe(df_metrics)

# Future: Add config changes, audit, triggers, etc.