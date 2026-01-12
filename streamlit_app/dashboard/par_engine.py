
"""
Par Engine: Centralized logic for Par Level calculations
Calculates everything on-the-fly from variance_report_summary data.
"""
import pandas as pd
import numpy as np
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

def _get_supabase_client():
    """Initialize and return Supabase client."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=3600)
def _load_variance_data():
    """Load variance report data from Supabase."""
    supabase = _get_supabase_client()
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table("variance_report_summary").select("*").range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    return pd.DataFrame(all_data)

# --- Par Calculation Methods ---
def get_par_methods():
    """Return available par calculation methods (hardcoded, no table needed)."""
    methods = [
        {
            'method_key': 'DAILY_USAGE',
            'method_name': 'Daily Usage Method',
            'description': 'Par = Daily Usage Rate × Coverage Days × (1 + Safety %)'
        },
        {
            'method_key': 'ORDER_FREQ',
            'method_name': 'Order Frequency Method',
            'description': 'Par = Average Order Qty × (1 + Safety %)'
        },
        {
            'method_key': 'REORDER_POINT',
            'method_name': 'Reorder Point Method',
            'description': 'Par = (Daily Usage × Lead Time) + Safety Stock'
        }
    ]
    return pd.DataFrame(methods)

def calculate_inventory_metrics(df, window_days=90):
    """
    Calculate inventory metrics from variance data.
    Returns: DataFrame with item-level metrics per store.
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure required columns exist
    required_cols = ['pc_number', 'product_name', 'theoretical_qty', 'units_sold', 'reporting_period']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.warning(f"Missing columns for metrics calculation: {missing}")
        return pd.DataFrame()
    
    # Group by store and item
    metrics = df.groupby(['pc_number', 'product_name']).agg({
        'theoretical_qty': 'mean',
        'units_sold': ['mean', 'sum', 'count'],
        'reporting_period': ['min', 'max']
    }).reset_index()
    
    # Flatten column names
    metrics.columns = ['pc_number', 'item_name', 'avg_theoretical_qty', 
                       'avg_units_sold', 'total_units_sold', 'num_periods',
                       'first_period', 'last_period']
    
    # Calculate daily usage rate (assuming monthly periods, divide by 30)
    metrics['daily_usage_rate'] = metrics['avg_units_sold'] / 30
    
    # Calculate days in window
    metrics['days_in_window'] = metrics['num_periods'] * 30
    
    return metrics

def calculate_par_levels(method_key='DAILY_USAGE', coverage_days=14, safety_percent=20):
    """
    Calculate par levels using selected method.
    
    Args:
        method_key: Calculation method to use
        coverage_days: Number of days of inventory to maintain
        safety_percent: Safety buffer percentage
    
    Returns:
        DataFrame with par quantities per item × store
    """
    df = _load_variance_data()
    
    if df.empty:
        return pd.DataFrame()
    
    # Calculate base metrics
    metrics = calculate_inventory_metrics(df)
    
    if metrics.empty:
        return pd.DataFrame()
    
    # Apply calculation method
    if method_key == 'DAILY_USAGE':
        metrics['par_quantity'] = (
            metrics['daily_usage_rate'] * coverage_days * (1 + safety_percent / 100)
        )
    
    elif method_key == 'ORDER_FREQ':
        metrics['par_quantity'] = (
            metrics['avg_theoretical_qty'] * (1 + safety_percent / 100)
        )
    
    elif method_key == 'REORDER_POINT':
        # Assume lead time = 7 days
        lead_time_days = 7
        safety_stock = metrics['daily_usage_rate'] * (coverage_days * safety_percent / 100)
        metrics['par_quantity'] = (
            (metrics['daily_usage_rate'] * lead_time_days) + safety_stock
        )
    
    # Round and ensure non-negative
    metrics['par_quantity'] = metrics['par_quantity'].fillna(0).round(0).clip(lower=0)
    
    # Add metadata
    metrics['method_key'] = method_key
    metrics['coverage_days'] = coverage_days
    metrics['safety_percent'] = safety_percent
    metrics['calculated_at'] = datetime.now().isoformat()
    
    return metrics

def get_par_results(method_key='DAILY_USAGE', coverage_days=14, safety_percent=20):
    """Calculate and return par results for selected method."""
    return calculate_par_levels(method_key, coverage_days, safety_percent)

def get_inventory_metrics(item_name=None, pc_number=None):
    """Get detailed metrics for specific item/store."""
    df = _load_variance_data()
    metrics = calculate_inventory_metrics(df)
    
    if item_name:
        metrics = metrics[metrics['item_name'] == item_name]
    if pc_number:
        metrics = metrics[metrics['pc_number'] == pc_number]
    
    return metrics

# Add more functions for settings, recalculation, etc. as needed
