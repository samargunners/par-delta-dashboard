
"""
Par Engine: Centralized logic for Par Level calculations
Calculates everything on-the-fly from NDCP invoices data.
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
def _load_ndcp_data():
    """Load NDCP invoice data from Supabase."""
    supabase = _get_supabase_client()
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table("ndcp_invoices").select("*").range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    
    df = pd.DataFrame(all_data)
    
    if df.empty:
        return df
    
    # Convert date columns (they appear to be stored as integers in YYYYMMDD format)
    if 'Invoice Date' in df.columns:
        df['invoice_date'] = pd.to_datetime(df['Invoice Date'], format='%Y%m%d', errors='coerce')
    if 'Order Date' in df.columns:
        df['order_date'] = pd.to_datetime(df['Order Date'], format='%Y%m%d', errors='coerce')
    
    # Rename columns to match expected format
    df = df.rename(columns={
        'PC Number': 'pc_number',
        'Item Description': 'product_name',
        'Qty Shipped': 'qty_shipped',
        'Qty Ordered': 'qty_ordered',
        'Category Desc': 'category',
        'Division Desc': 'division',
        'Item Number': 'item_number',
        'Price': 'unit_price',
        'Ext Price': 'total_price'
    })
    
    return df

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
    Calculate inventory metrics from NDCP invoice data.
    Returns: DataFrame with item-level metrics per store.
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure required columns exist
    required_cols = ['pc_number', 'product_name', 'qty_shipped', 'invoice_date']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.warning(f"Missing columns for metrics calculation: {missing}")
        return pd.DataFrame()
    
    # Filter to recent data (window_days)
    if 'invoice_date' in df.columns:
        cutoff_date = datetime.now() - timedelta(days=window_days)
        df = df[df['invoice_date'] >= cutoff_date]
    
    # Group by store and item
    metrics = df.groupby(['pc_number', 'product_name']).agg({
        'qty_shipped': ['mean', 'sum', 'count'],
        'qty_ordered': 'mean',
        'invoice_date': ['min', 'max']
    }).reset_index()
    
    # Flatten column names
    metrics.columns = ['pc_number', 'item_name', 
                       'avg_qty_shipped', 'total_qty_shipped', 'num_orders',
                       'avg_qty_ordered',
                       'first_order_date', 'last_order_date']
    
    # Calculate days between first and last order
    metrics['days_in_window'] = (metrics['last_order_date'] - metrics['first_order_date']).dt.days
    metrics['days_in_window'] = metrics['days_in_window'].clip(lower=1)  # Avoid division by zero
    
    # Calculate daily usage rate based on total shipped divided by days in window
    metrics['daily_usage_rate'] = metrics['total_qty_shipped'] / metrics['days_in_window']
    
    # Calculate average order quantity for ORDER_FREQ method
    metrics['avg_order_qty'] = metrics['avg_qty_shipped']
    
    # Add total units for reference (for display compatibility)
    metrics['total_units_sold'] = metrics['total_qty_shipped']
    metrics['avg_units_sold'] = metrics['avg_qty_shipped']
    metrics['num_periods'] = metrics['num_orders']
    
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
    df = _load_ndcp_data()
    
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
            metrics['avg_order_qty'] * (1 + safety_percent / 100)
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
    df = _load_ndcp_data()
    metrics = calculate_inventory_metrics(df)
    
    if item_name:
        metrics = metrics[metrics['item_name'] == item_name]
    if pc_number:
        metrics = metrics[metrics['pc_number'] == pc_number]
    
    return metrics

# Add more functions for settings, recalculation, etc. as needed
