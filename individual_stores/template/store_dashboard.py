"""
Individual Store Dashboard Template for Par Delta Dunkin' Stores
This template creates a comprehensive single-page dashboard for a specific store
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from supabase import create_client
import sys
import os

# Add the parent directory to Python path to import store_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from store_config import get_store_config

# ================================
# STORE CONFIGURATION
# ================================
# TODO: Set this to your specific store's PC number
STORE_PC_NUMBER = "357993"  # CHANGE THIS FOR EACH STORE

store_config = get_store_config(STORE_PC_NUMBER)
if not store_config:
    st.error(f"Store configuration not found for PC {STORE_PC_NUMBER}")
    st.stop()

STORE_NAME = store_config["name"]
STORE_ADDRESS = store_config["address"]

# ================================
# PAGE CONFIGURATION
# ================================
st.set_page_config(
    page_title=f"{STORE_NAME} - Par Delta Dashboard",
    page_icon="🍩",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================
# SUPABASE SETUP
# ================================
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# ================================
# DATA LOADING FUNCTIONS
# ================================
@st.cache_data(ttl=1800)  # 30 minutes cache
def load_store_data(table_name, pc_number, days_back=7):
    """Load data for specific store with date filtering"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    try:
        response = supabase.table(table_name)\
            .select("*")\
            .eq("pc_number", str(pc_number))\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error loading {table_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def load_employee_data(pc_number):
    """Load employee data for specific store"""
    try:
        response = supabase.table("employee_profile")\
            .select("*")\
            .eq("pc_number", str(pc_number))\
            .execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error loading employee data: {e}")
        return pd.DataFrame()

# ================================
# HEADER SECTION
# ================================
st.markdown(f"""
<div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #FF6B35 0%, #F7931E 100%); 
            border-radius: 10px; margin-bottom: 20px; color: white;'>
    <h1 style='margin: 0; font-size: 2.5rem;'>🍩 {STORE_NAME} Store Dashboard</h1>
    <p style='margin: 5px 0 0 0; font-size: 1.2rem; opacity: 0.9;'>Par Delta Operations • PC: {STORE_PC_NUMBER}</p>
    <p style='margin: 5px 0 0 0; font-size: 1rem; opacity: 0.8;'>{STORE_ADDRESS}</p>
</div>
""", unsafe_allow_html=True)

# ================================
# LOAD ALL DATA
# ================================
with st.spinner("Loading store data..."):
    # Load data for the past 7 days
    donut_sales = load_store_data("donut_sales_hourly", STORE_PC_NUMBER, 7)
    usage_data = load_store_data("usage_overview", STORE_PC_NUMBER, 7)
    labor_actual = load_store_data("actual_table_labor", STORE_PC_NUMBER, 7) 
    labor_scheduled = load_store_data("schedule_table_labor", STORE_PC_NUMBER, 7)
    labor_ideal = load_store_data("ideal_table_labor", STORE_PC_NUMBER, 7)
    employee_clockin = load_store_data("employee_clockin", STORE_PC_NUMBER, 7)
    employee_schedule = load_store_data("employee_schedule", STORE_PC_NUMBER, 7)
    employee_profile = load_employee_data(STORE_PC_NUMBER)
    variance_data = load_store_data("variance_report_summary", STORE_PC_NUMBER, 30)

# ================================
# KEY METRICS ROW
# ================================
st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

# Metric 1: Today's Donut Sales
with col1:
    today = datetime.now().date()
    if not donut_sales.empty:
        donut_sales['date'] = pd.to_datetime(donut_sales['date']).dt.date
        today_sales = donut_sales[donut_sales['date'] == today]['quantity'].sum()
        yesterday_sales = donut_sales[donut_sales['date'] == (today - timedelta(days=1))]['quantity'].sum()
        
        if yesterday_sales > 0:
            change = ((today_sales - yesterday_sales) / yesterday_sales) * 100
            delta = f"{change:+.1f}% vs yesterday"
        else:
            delta = "No comparison data"
    else:
        today_sales = 0
        delta = "No data"
    
    st.metric("🍩 Today's Donut Sales", f"{today_sales:,.0f} units", delta)

# Metric 2: Donut Waste Rate
with col2:
    if not usage_data.empty:
        usage_data['date'] = pd.to_datetime(usage_data['date']).dt.date
        donut_usage = usage_data[usage_data['product_type'].str.contains('donut', case=False, na=False)]
        recent_waste = donut_usage['waste_percent'].mean() if not donut_usage.empty else 0
        
        if recent_waste <= 5:
            waste_color = "normal"
        elif recent_waste <= 10:
            waste_color = "inverse" 
        else:
            waste_color = "off"
    else:
        recent_waste = 0
        waste_color = "normal"
    
    st.metric("📉 Avg Waste Rate", f"{recent_waste:.1f}%", delta_color=waste_color)

# Metric 3: Labor Efficiency
with col3:
    if not labor_actual.empty and not labor_ideal.empty:
        actual_hours = labor_actual['actual_hours'].sum()
        ideal_hours = labor_ideal['ideal_hours'].sum()
        
        if ideal_hours > 0:
            efficiency = (ideal_hours / actual_hours) * 100
            variance = efficiency - 100
            delta = f"{variance:+.1f}% vs ideal"
            color = "normal" if variance >= -10 else "inverse"
        else:
            efficiency = 0
            delta = "No ideal data"
            color = "normal"
    else:
        efficiency = 0
        delta = "No data"
        color = "normal"
    
    st.metric("💼 Labor Efficiency", f"{efficiency:.1f}%", delta, delta_color=color)

# Metric 4: Employee Punctuality  
with col4:
    if not employee_clockin.empty and not employee_schedule.empty:
        # Calculate punctuality rate
        merged = pd.merge(employee_schedule, employee_clockin, 
                         on=['employee_id', 'date'], how='left')
        
        if not merged.empty:
            # Simple punctuality calculation
            on_time = len(merged.dropna(subset=['time_in']))
            total_scheduled = len(merged)
            punctuality_rate = (on_time / total_scheduled) * 100 if total_scheduled > 0 else 0
        else:
            punctuality_rate = 0
    else:
        punctuality_rate = 0
    
    st.metric("⏰ Punctuality Rate", f"{punctuality_rate:.1f}%")

# Metric 5: Active Employees
with col5:
    if not employee_profile.empty:
        active_employees = len(employee_profile[employee_profile['status'].str.lower() == 'active'])
        total_employees = len(employee_profile)
    else:
        active_employees = 0
        total_employees = 0
    
    st.metric("👥 Active Staff", f"{active_employees}/{total_employees}")

# ================================
# CHARTS SECTION
# ================================
st.markdown("---")

# Row 1: Sales and Waste Analysis
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Daily Donut Sales Trend")
    if not donut_sales.empty:
        daily_sales = donut_sales.groupby('date')['quantity'].sum().reset_index()
        daily_sales['date'] = pd.to_datetime(daily_sales['date'])
        
        fig = px.line(daily_sales, x='date', y='quantity',
                     title="Daily Donut Sales Volume",
                     labels={'quantity': 'Units Sold', 'date': 'Date'})
        fig.update_traces(line_color='#FF6B35', line_width=3)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales data available")

with col2:
    st.subheader("🗑️ Waste Analysis")
    if not usage_data.empty:
        donut_usage = usage_data[usage_data['product_type'].str.contains('donut', case=False, na=False)]
        if not donut_usage.empty:
            waste_trend = donut_usage.groupby('date').agg({
                'wasted_qty': 'sum',
                'ordered_qty': 'sum'
            }).reset_index()
            waste_trend['waste_rate'] = (waste_trend['wasted_qty'] / waste_trend['ordered_qty']) * 100
            
            fig = px.bar(waste_trend, x='date', y='waste_rate',
                        title="Daily Waste Rate %",
                        labels={'waste_rate': 'Waste Rate %', 'date': 'Date'})
            fig.update_traces(marker_color='#F7931E')
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No waste data available")
    else:
        st.info("No usage data available")

# Row 2: Labor Analysis
st.subheader("💼 Labor Performance Analysis")

col1, col2 = st.columns(2)

with col1:
    st.write("**Scheduled vs Actual Hours**")
    if not labor_scheduled.empty and not labor_actual.empty:
        # Group by date
        scheduled_summary = labor_scheduled.groupby('date')['scheduled_hours'].sum().reset_index()
        actual_summary = labor_actual.groupby('date')['actual_hours'].sum().reset_index()
        
        labor_comparison = pd.merge(scheduled_summary, actual_summary, on='date', how='outer').fillna(0)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Scheduled', x=labor_comparison['date'], 
                            y=labor_comparison['scheduled_hours'], marker_color='lightblue'))
        fig.add_trace(go.Bar(name='Actual', x=labor_comparison['date'], 
                            y=labor_comparison['actual_hours'], marker_color='darkblue'))
        
        fig.update_layout(barmode='group', title='Daily Labor Hours Comparison', height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No labor data available")

with col2:
    st.write("**Employee Schedule Compliance**")
    if not employee_clockin.empty and not employee_schedule.empty:
        # Create a simple compliance chart
        schedule_dates = employee_schedule['date'].nunique()
        clockin_dates = employee_clockin['date'].nunique()
        
        compliance_data = pd.DataFrame({
            'Metric': ['Scheduled Days', 'Actual Clock-ins'],
            'Count': [schedule_dates, clockin_dates]
        })
        
        fig = px.bar(compliance_data, x='Metric', y='Count',
                    title='Schedule vs Actual Attendance',
                    color='Metric', color_discrete_sequence=['#FF6B35', '#F7931E'])
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No attendance data available")

# ================================
# INVENTORY VARIANCE SECTION
# ================================
if not variance_data.empty:
    st.subheader("📦 Recent Inventory Variance")
    
    # Get the most recent reporting period
    latest_period = variance_data['reporting_period'].max()
    latest_data = variance_data[variance_data['reporting_period'] == latest_period]
    
    # Show top variance items
    top_variances = latest_data.nlargest(10, 'variance')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.bar(top_variances, x='product_name', y='variance',
                    title=f'Top 10 Inventory Variances - {latest_period}',
                    labels={'variance': 'Variance $', 'product_name': 'Product'})
        fig.update_traces(marker_color='#FF6B35')
        fig.update_xaxes(tickangle=45)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Summary metrics
        total_variance = latest_data['variance'].sum()
        positive_variance = latest_data[latest_data['variance'] > 0]['variance'].sum()
        negative_variance = latest_data[latest_data['variance'] < 0]['variance'].sum()
        
        st.metric("Total Variance", f"${total_variance:,.2f}")
        st.metric("Positive Variance", f"${positive_variance:,.2f}")
        st.metric("Negative Variance", f"${negative_variance:,.2f}")

# ================================
# DATA TABLES SECTION
# ================================
with st.expander("📋 Raw Data Tables", expanded=False):
    tab1, tab2, tab3, tab4 = st.tabs(["Recent Sales", "Usage Data", "Labor Summary", "Employee Info"])
    
    with tab1:
        if not donut_sales.empty:
            st.dataframe(donut_sales.head(20), use_container_width=True)
        else:
            st.info("No sales data available")
    
    with tab2:
        if not usage_data.empty:
            st.dataframe(usage_data.head(20), use_container_width=True)
        else:
            st.info("No usage data available")
    
    with tab3:
        if not labor_actual.empty:
            st.dataframe(labor_actual.head(20), use_container_width=True)
        else:
            st.info("No labor data available")
    
    with tab4:
        if not employee_profile.empty:
            st.dataframe(employee_profile, use_container_width=True)
        else:
            st.info("No employee data available")

# ================================
# FOOTER
# ================================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; padding: 10px; color: #666;'>
    <p><strong>{STORE_NAME} Store Dashboard</strong> • Par Delta Operations</p>
    <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Data refreshes every 30 minutes</p>
</div>
""", unsafe_allow_html=True)
