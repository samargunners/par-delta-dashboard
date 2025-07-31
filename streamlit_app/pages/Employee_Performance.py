import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client
import plotly.express as px

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Employee Performance Overview", layout="wide")
st.title("👥 Employee Performance Overview")

# --- Load Data with Pagination ---
@st.cache_data(ttl=3600)
def load_all_rows(table):
    all_data = []
    chunk_size = 1000
    offset = 0
    while True:
        response = supabase.table(table).select("*").range(offset, offset + chunk_size - 1).execute()
        data_chunk = response.data
        if not data_chunk:
            break
        all_data.extend(data_chunk)
        offset += chunk_size
    df = pd.DataFrame(all_data)
    if not df.empty:
        df.columns = [str(col).strip().lower() for col in df.columns]
    return df

# --- Load Tables ---
employee_profile_df = load_all_rows("employee_profile")
employee_clockin_df = load_all_rows("employee_clockin")
employee_schedules_df = load_all_rows("employee_schedules")

if employee_profile_df.empty:
    st.error("❌ Employee profile data is not available. Please upload employee data first.")
    st.stop()

# --- Data Preprocessing ---
# Convert date columns
if not employee_clockin_df.empty:
    employee_clockin_df["date"] = pd.to_datetime(employee_clockin_df["date"], errors="coerce")
    employee_clockin_df["employee_id"] = employee_clockin_df["employee_id"].astype(str)

if not employee_schedules_df.empty:
    employee_schedules_df["date"] = pd.to_datetime(employee_schedules_df["date"], errors="coerce")
    employee_schedules_df["employee_id"] = employee_schedules_df["employee_id"].astype(str)

# Convert employee profile data
employee_profile_df["hired_date"] = pd.to_datetime(employee_profile_df["hired_date"], errors="coerce")

# --- Date Range Filter ---
st.sidebar.header("📅 Filter Options")

# Get date range from employee clockin data
if not employee_clockin_df.empty:
    min_date = employee_clockin_df["date"].min().date()
    max_date = employee_clockin_df["date"].max().date()
elif not employee_schedules_df.empty:
    # Fallback to schedules if no clockin data
    min_date = employee_schedules_df["date"].min().date()
    max_date = employee_schedules_df["date"].max().date()
else:
    min_date = None
    max_date = None

if min_date and max_date:
    # Default to all available dates (start from donut data min, end at last Saturday)
    default_start = min_date
    default_end = max_date
    
    date_range = st.sidebar.date_input(
        "Select Date Range for Attendance Analysis",
        value=[default_start, default_end],
        min_value=min_date,
        max_value=max_date
    )
else:
    date_range = None
    st.warning("⚠️ No date data available for filtering from donut sales or employee attendance.")

# Location filter
location_options = ["All Locations"] + sorted(employee_profile_df["primary_location"].dropna().unique().tolist())
selected_location = st.sidebar.selectbox("Filter by Location", location_options)

# Status filter
status_options = ["All Statuses"] + sorted(employee_profile_df["status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Filter by Status", status_options)

# Late threshold setting
late_threshold = st.sidebar.slider("Late threshold (minutes)", min_value=1, max_value=15, value=5)

# --- Apply Date Range Filter ---
if date_range and len(date_range) == 2 and not employee_schedules_df.empty and not employee_clockin_df.empty:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    employee_schedules_filtered = employee_schedules_df[
        (employee_schedules_df["date"] >= start_date) & 
        (employee_schedules_df["date"] <= end_date)
    ].copy()
    employee_clockin_filtered = employee_clockin_df[
        (employee_clockin_df["date"] >= start_date) & 
        (employee_clockin_df["date"] <= end_date)
    ].copy()
else:
    employee_schedules_filtered = employee_schedules_df.copy() if not employee_schedules_df.empty else pd.DataFrame()
    employee_clockin_filtered = employee_clockin_df.copy() if not employee_clockin_df.empty else pd.DataFrame()

# --- Calculate Attendance Metrics ---
def calculate_attendance_metrics():
    """Calculate attendance metrics for each employee"""
    
    if employee_schedules_filtered.empty:
        # Return empty metrics if no schedule data
        return pd.DataFrame(columns=[
            'employee_id', 'days_scheduled', 'days_on_time', 
            'days_early', 'days_late', 'days_absent'
        ])
    
    # Get unique scheduled days per employee
    schedule_summary = employee_schedules_filtered.groupby('employee_id').agg({
        'date': 'nunique'  # Count unique dates scheduled
    }).rename(columns={'date': 'days_scheduled'}).reset_index()
    
    if employee_clockin_filtered.empty:
        # If no clockin data, all scheduled days are absent
        schedule_summary['days_on_time'] = 0
        schedule_summary['days_early'] = 0
        schedule_summary['days_late'] = 0
        schedule_summary['days_absent'] = schedule_summary['days_scheduled']
        return schedule_summary
    
    # Keep earliest clock-in per employee/date (handles multiple shifts per day)
    clockin_clean = employee_clockin_filtered.sort_values(['employee_id', 'date', 'time_in']).drop_duplicates(
        subset=['employee_id', 'date'], keep='first'
    )
    
    # Also get earliest schedule time per employee/date (in case of multiple shifts)
    schedule_clean = employee_schedules_filtered.sort_values(['employee_id', 'date', 'start_time']).drop_duplicates(
        subset=['employee_id', 'date'], keep='first'
    )
    
    # Merge schedule with clockin data (using cleaned data with earliest times)
    merged_data = pd.merge(
        schedule_clean,
        clockin_clean[['employee_id', 'date', 'time_in']],
        on=['employee_id', 'date'],
        how='left'
    )
    
    # Evaluate punctuality
    def evaluate_punctuality(row):
        if pd.isna(row['time_in']):
            return 'absent'
        if pd.isna(row['start_time']):
            return 'on_call'
        
        try:
            # Convert times to datetime for comparison
            start_dt = datetime.combine(datetime.today(), pd.to_datetime(row['start_time']).time())
            timein_dt = datetime.combine(datetime.today(), pd.to_datetime(row['time_in']).time())
            delta_minutes = (timein_dt - start_dt).total_seconds() / 60
            
            if abs(delta_minutes) <= late_threshold:
                return 'on_time'
            elif delta_minutes > late_threshold:
                return 'late'
            else:
                return 'early'
        except:
            return 'invalid'
    
    merged_data['punctuality_status'] = merged_data.apply(evaluate_punctuality, axis=1)
    
    # Calculate metrics per employee
    attendance_metrics = merged_data.groupby('employee_id')['punctuality_status'].value_counts().unstack(fill_value=0)
    
    # Ensure all columns exist
    for col in ['on_time', 'early', 'late', 'absent']:
        if col not in attendance_metrics.columns:
            attendance_metrics[col] = 0
    
    attendance_metrics = attendance_metrics.rename(columns={
        'on_time': 'days_on_time',
        'early': 'days_early', 
        'late': 'days_late',
        'absent': 'days_absent'
    }).reset_index()
    
    # Merge with schedule summary to get total days scheduled
    final_metrics = pd.merge(schedule_summary, attendance_metrics, on='employee_id', how='left').fillna(0)
    
    # Convert to integers
    metric_cols = ['days_scheduled', 'days_on_time', 'days_early', 'days_late', 'days_absent']
    final_metrics[metric_cols] = final_metrics[metric_cols].astype(int)
    
    return final_metrics

# Calculate attendance metrics
attendance_metrics = calculate_attendance_metrics()

# --- Build Final Employee Report ---
# Start with employee profile data
employee_report = employee_profile_df.copy()

# Create full name
employee_report['full_name'] = (
    employee_report['first_name'].fillna('') + ' ' + 
    employee_report['last_name'].fillna('')
).str.strip()

# Merge with attendance metrics
if not attendance_metrics.empty:
    employee_report = pd.merge(
        employee_report,
        attendance_metrics,
        left_on='employee_number',
        right_on='employee_id',
        how='left'
    )
    # Fill missing attendance data with zeros
    metric_cols = ['days_scheduled', 'days_on_time', 'days_early', 'days_late', 'days_absent']
    employee_report[metric_cols] = employee_report[metric_cols].fillna(0).astype(int)
else:
    # No attendance data available
    employee_report['days_scheduled'] = 0
    employee_report['days_on_time'] = 0
    employee_report['days_early'] = 0
    employee_report['days_late'] = 0
    employee_report['days_absent'] = 0

# --- Apply Filters ---
filtered_report = employee_report.copy()

# Filter out employees with specific names that should be excluded
exclude_names = ['zzz', 'yyy', 'USD', 'Test', 'Parth', 'Kunal', 'rita']
# Create a mask that excludes any employee whose full_name contains any of the excluded terms (case-insensitive)
name_mask = ~filtered_report['full_name'].str.lower().str.contains('|'.join([name.lower() for name in exclude_names]), na=False)
filtered_report = filtered_report[name_mask]

if selected_location != "All Locations":
    filtered_report = filtered_report[filtered_report['primary_location'] == selected_location]

if selected_status != "All Statuses":
    filtered_report = filtered_report[filtered_report['status'] == selected_status]

# --- Display Results ---
st.subheader("📋 Employee Performance Summary")

if filtered_report.empty:
    st.warning("⚠️ No employees match the selected filters.")
else:
    # Calculate punctuality percentage
    filtered_report['punctuality_percentage'] = filtered_report.apply(
        lambda row: round(
            (row['days_on_time'] + row['days_early']) / max(row['days_scheduled'], 1) * 100, 1
        ) if row['days_scheduled'] > 0 else 0,
        axis=1
    )
    
    # Prepare display dataframe
    display_columns = [
        'employee_number', 'full_name', 'primary_position', 'primary_location',
        'hired_date', 'days_scheduled', 'days_on_time', 'days_early', 
        'days_late', 'days_absent', 'punctuality_percentage', 'status'
    ]
    
    display_df = filtered_report[display_columns].copy()
    
    # Rename columns for display
    display_df = display_df.rename(columns={
        'employee_number': 'Employee #',
        'full_name': 'Name',
        'primary_position': 'Position',
        'primary_location': 'Location',
        'hired_date': 'Hired Date',
        'days_scheduled': 'Days Scheduled',
        'days_on_time': 'Days On Time',
        'days_early': 'Days Early',
        'days_late': 'Days Late',
        'days_absent': 'Days Absent',
        'punctuality_percentage': 'Punctuality %',
        'status': 'Status'
    })
    
    # Format hired date
    display_df['Hired Date'] = pd.to_datetime(display_df['Hired Date']).dt.strftime('%Y-%m-%d')
    
    # Sort by punctuality percentage (best first)
    display_df = display_df.sort_values('Punctuality %', ascending=False)
    
    # Style function for punctuality (applies to both punctuality column and name column)
    def style_punctuality(val):
        if val >= 95:
            return 'background-color: #28a745; color: white'
        elif val >= 90:
            return 'background-color: #5cb85c; color: white'
        elif val >= 85:
            return 'background-color: #f0ad4e; color: white'
        elif val >= 80:
            return 'background-color: #fd7e14; color: white'
        elif val >= 75:
            return 'background-color: #e67e22; color: white'
        elif val >= 70:
            return 'background-color: #d35400; color: white'
        else:
            return 'background-color: #dc3545; color: white'
    
    # Function to apply name highlighting based on punctuality percentage
    def highlight_name_by_punctuality(row):
        punctuality = row['Punctuality %']
        name_style = style_punctuality(punctuality)
        punctuality_style = style_punctuality(punctuality)
        
        # Create style for each column
        styles = [''] * len(row)
        
        # Apply style to Name column (index 1) and Punctuality % column
        name_idx = row.index.get_loc('Name')
        punctuality_idx = row.index.get_loc('Punctuality %')
        
        styles[name_idx] = name_style
        styles[punctuality_idx] = punctuality_style
        
        return styles
    
    # Apply styling
    styled_df = display_df.style.apply(
        highlight_name_by_punctuality, 
        axis=1
    ).format({
        'Punctuality %': '{:.1f}%'
    })
    
    st.dataframe(styled_df, use_container_width=True)

# --- Labor Turnover Analysis ---
st.subheader("📊 Labor Turnover Analysis (2025)")

# Calculate turnover metrics
def calculate_turnover_metrics():
    
    # Convert last_edit_date to datetime for filtering
    employee_profile_df['last_edit_date'] = pd.to_datetime(employee_profile_df['last_edit_date'], errors='coerce')
    
    # Create full name for filtering
    employee_profile_df['full_name_temp'] = (
        employee_profile_df['first_name'].fillna('') + ' ' + 
        employee_profile_df['last_name'].fillna('')
    ).str.strip()
    
    # Filter out employees with specific names that should be excluded
    exclude_names = ['zzz', 'yyy', 'USD', 'Test', 'Parth', 'Kunal', 'rita']
    name_mask = ~employee_profile_df['full_name_temp'].str.lower().str.contains('|'.join([name.lower() for name in exclude_names]), na=False)
    filtered_employee_df = employee_profile_df[name_mask]
    
    # Active employees (status = 'active')
    active_employees = filtered_employee_df[filtered_employee_df['status'].str.lower() == 'active']
    active_count = len(active_employees)
    
    # Terminated employees (status = 'terminated' AND last_edit_date in 2025)
    terminated_2025 = filtered_employee_df[
        (filtered_employee_df['status'].str.lower() == 'terminated') & 
        (filtered_employee_df['last_edit_date'].dt.year == 2025)
    ]
    terminated_count = len(terminated_2025)
    
    # Calculate turnover ratio
    total_employees = active_count + terminated_count
    if total_employees > 0:
        turnover_ratio = (terminated_count / total_employees) * 100
    else:
        turnover_ratio = 0
        
    return active_count, terminated_count, total_employees, turnover_ratio, terminated_2025

active_count, terminated_count, total_employees_turnover, turnover_ratio, terminated_2025 = calculate_turnover_metrics()

# Display turnover metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Employees", active_count)

with col2:
    st.metric("Terminated (2025)", terminated_count)

with col3:
    st.metric("Total for Calculation", total_employees_turnover)

with col4:
    st.metric("Turnover Ratio", f"{turnover_ratio:.1f}%")

# Color-coded interpretation
if turnover_ratio > 20:
    st.error(f"🔴 **High Turnover Risk**: {turnover_ratio:.1f}% turnover ratio indicates significant employee retention issues.")
elif turnover_ratio > 15:
    st.warning(f"🟡 **Moderate Turnover**: {turnover_ratio:.1f}% turnover ratio suggests some retention concerns.")
elif turnover_ratio > 10:
    st.info(f"🟠 **Acceptable Turnover**: {turnover_ratio:.1f}% turnover ratio is within normal range but worth monitoring.")
else:
    st.success(f"🟢 **Low Turnover**: {turnover_ratio:.1f}% turnover ratio indicates good employee retention.")

# Show terminated employees details if any
if not terminated_2025.empty:
    st.subheader("📋 Terminated Employees (2025)")
    
    # Check which columns are available for display
    available_cols = ['employee_number', 'first_name', 'last_name', 'primary_position', 'primary_location', 'hired_date']
    if 'last_edit_date' in terminated_2025.columns:
        available_cols.append('last_edit_date')
    
    terminated_display = terminated_2025[available_cols].copy()
    terminated_display['full_name'] = (terminated_display['first_name'].fillna('') + ' ' + terminated_display['last_name'].fillna('')).str.strip()
    
    # Only calculate days employed if last_edit_date is available
    if 'last_edit_date' in terminated_2025.columns:
        terminated_display['days_employed'] = (terminated_display['last_edit_date'] - pd.to_datetime(terminated_display['hired_date'])).dt.days
        
        # Rename columns for display
        terminated_display = terminated_display.rename(columns={
            'employee_number': 'Employee #',
            'full_name': 'Name',
            'primary_position': 'Position',
            'primary_location': 'Location',
            'hired_date': 'Hired Date',
            'last_edit_date': 'Termination Date',
            'days_employed': 'Days Employed'
        })
        
        # Format dates
        terminated_display['Hired Date'] = pd.to_datetime(terminated_display['Hired Date']).dt.strftime('%Y-%m-%d')
        terminated_display['Termination Date'] = pd.to_datetime(terminated_display['Termination Date']).dt.strftime('%Y-%m-%d')
        
        # Sort by termination date (most recent first)
        terminated_display = terminated_display.sort_values('Termination Date', ascending=False)
        
        st.dataframe(terminated_display[['Employee #', 'Name', 'Position', 'Location', 'Hired Date', 'Termination Date', 'Days Employed']], use_container_width=True)
    else:
        # Rename columns for display (without termination date)
        terminated_display = terminated_display.rename(columns={
            'employee_number': 'Employee #',
            'full_name': 'Name',
            'primary_position': 'Position',
            'primary_location': 'Location',
            'hired_date': 'Hired Date'
        })
        
        # Format hired date
        terminated_display['Hired Date'] = pd.to_datetime(terminated_display['Hired Date']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(terminated_display[['Employee #', 'Name', 'Position', 'Location', 'Hired Date']], use_container_width=True)
    
    # Turnover trend chart (only if last_edit_date is available)
    if len(terminated_2025) > 1 and 'last_edit_date' in terminated_2025.columns:
        st.subheader("📈 Monthly Turnover Trend (2025)")
        
        # Group terminations by month
        terminated_2025['termination_month'] = terminated_2025['last_edit_date'].dt.to_period('M')
        monthly_terminations = terminated_2025.groupby('termination_month').size().reset_index(name='terminations')
        monthly_terminations['month'] = monthly_terminations['termination_month'].astype(str)
        
        # Create trend chart
        fig_trend = px.line(
            monthly_terminations,
            x='month',
            y='terminations',
            title='Monthly Employee Terminations in 2025',
            labels={'month': 'Month', 'terminations': 'Number of Terminations'},
            markers=True
        )
        fig_trend.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Position-wise termination analysis
        if len(terminated_2025['primary_position'].dropna().unique()) > 1:
            st.subheader("💼 Terminations by Position")
            
            position_terminations = terminated_2025.groupby('primary_position').size().reset_index(name='terminations')
            
            fig_pos_term = px.bar(
                position_terminations,
                x='primary_position',
                y='terminations',
                title='Employee Terminations by Position (2025)',
                labels={'primary_position': 'Position', 'terminations': 'Number of Terminations'}
            )
            fig_pos_term.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_pos_term, use_container_width=True)

# --- Position-wise Turnover Analysis Table ---
st.subheader("📊 Turnover Analysis by Position")

# Calculate turnover by position
def calculate_position_turnover():
    # Get the filtered employee data (excluding test names)
    employee_profile_df['last_edit_date'] = pd.to_datetime(employee_profile_df['last_edit_date'], errors='coerce')
    employee_profile_df['full_name_temp'] = (
        employee_profile_df['first_name'].fillna('') + ' ' + 
        employee_profile_df['last_name'].fillna('')
    ).str.strip()
    
    exclude_names = ['zzz', 'yyy', 'USD', 'Test', 'Parth', 'Kunal', 'rita']
    name_mask = ~employee_profile_df['full_name_temp'].str.lower().str.contains('|'.join([name.lower() for name in exclude_names]), na=False)
    filtered_employee_df = employee_profile_df[name_mask]
    
    # Group by position and calculate metrics
    position_stats = []
    
    for position in filtered_employee_df['primary_position'].dropna().unique():
        position_employees = filtered_employee_df[filtered_employee_df['primary_position'] == position]
        
        # Active employees in this position
        active_in_position = len(position_employees[position_employees['status'].str.lower() == 'active'])
        
        # Terminated employees in this position (2025)
        terminated_in_position = len(position_employees[
            (position_employees['status'].str.lower() == 'terminated') & 
            (position_employees['last_edit_date'].dt.year == 2025)
        ])
        
        # Total employees for calculation
        total_in_position = active_in_position + terminated_in_position
        
        # Calculate turnover ratio
        if total_in_position > 0:
            turnover_ratio = (terminated_in_position / total_in_position) * 100
        else:
            turnover_ratio = 0
        
        # Risk assessment
        if turnover_ratio > 20:
            risk_level = "🔴 High Risk"
        elif turnover_ratio > 15:
            risk_level = "🟡 Moderate Risk"
        elif turnover_ratio > 10:
            risk_level = "🟠 Monitor"
        else:
            risk_level = "🟢 Low Risk"
        
        position_stats.append({
            'Position': position,
            'Active Employees': active_in_position,
            'Terminated (2025)': terminated_in_position,
            'Total for Calculation': total_in_position,
            'Turnover Ratio (%)': round(turnover_ratio, 1),
            'Risk Level': risk_level
        })
    
    return pd.DataFrame(position_stats)

position_turnover_df = calculate_position_turnover()

if not position_turnover_df.empty:
    # Sort by turnover ratio (highest first)
    position_turnover_df = position_turnover_df.sort_values('Turnover Ratio (%)', ascending=False)
    
    # Style function for turnover ratio
    def style_turnover_ratio(val):
        if val > 20:
            return 'background-color: #dc3545; color: white'  # Red
        elif val > 15:
            return 'background-color: #ffc107; color: black'  # Yellow
        elif val > 10:
            return 'background-color: #fd7e14; color: white'  # Orange
        else:
            return 'background-color: #28a745; color: white'  # Green
    
    # Function to apply styling to turnover ratio column
    def highlight_turnover_column(row):
        turnover_ratio = row['Turnover Ratio (%)']
        style = style_turnover_ratio(turnover_ratio)
        
        styles = [''] * len(row)
        turnover_idx = row.index.get_loc('Turnover Ratio (%)')
        styles[turnover_idx] = style
        
        return styles
    
    # Apply styling
    styled_position_df = position_turnover_df.style.apply(
        highlight_turnover_column, 
        axis=1
    ).format({
        'Turnover Ratio (%)': '{:.1f}%'
    })
    
    st.dataframe(styled_position_df, use_container_width=True)
    
    # Summary insights
    st.markdown("**Key Insights:**")
    
    high_risk_positions = position_turnover_df[position_turnover_df['Turnover Ratio (%)'] > 20]
    if not high_risk_positions.empty:
        st.error(f"🔴 **High Risk Positions**: {', '.join(high_risk_positions['Position'].tolist())} - Require immediate attention")
    
    moderate_risk_positions = position_turnover_df[
        (position_turnover_df['Turnover Ratio (%)'] > 15) & 
        (position_turnover_df['Turnover Ratio (%)'] <= 20)
    ]
    if not moderate_risk_positions.empty:
        st.warning(f"🟡 **Moderate Risk Positions**: {', '.join(moderate_risk_positions['Position'].tolist())} - Should be monitored closely")
    
    low_risk_positions = position_turnover_df[position_turnover_df['Turnover Ratio (%)'] <= 10]
    if not low_risk_positions.empty:
        st.success(f"🟢 **Stable Positions**: {', '.join(low_risk_positions['Position'].tolist())} - Good retention rates")
    
    # Average turnover across all positions
    avg_turnover = position_turnover_df['Turnover Ratio (%)'].mean()
    st.info(f"📊 **Average Turnover Across All Positions**: {avg_turnover:.1f}%")
    
else:
    st.warning("⚠️ No position data available for turnover analysis.")

# Continue with the rest of the content for the filtered report
if not filtered_report.empty:
    # --- Summary Statistics ---
    st.subheader("📊 Attendance Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_employees = len(filtered_report)
        st.metric("Total Employees", total_employees)
    
    with col2:
        avg_punctuality = filtered_report['punctuality_percentage'].mean()
        st.metric("Average Punctuality", f"{avg_punctuality:.1f}%")
    
    with col3:
        if not filtered_report[filtered_report['punctuality_percentage'] > 0].empty:
            best_employee = filtered_report.loc[filtered_report['punctuality_percentage'].idxmax(), 'full_name']
            best_percentage = filtered_report['punctuality_percentage'].max()
            st.metric("Best Performer", best_employee, f"{best_percentage:.1f}%")
        else:
            st.metric("Best Performer", "N/A", "No data")
    
    with col4:
        critical_count = len(filtered_report[filtered_report['punctuality_percentage'] < 70])
        st.metric("Needs Attention", f"{critical_count} employees", "< 70%")
    
    # --- Charts ---
    if not filtered_report.empty and filtered_report['days_scheduled'].sum() > 0:
        
        # Punctuality distribution
        st.subheader("📈 Punctuality Distribution")
        
        fig_hist = px.histogram(
            filtered_report[filtered_report['punctuality_percentage'] > 0],
            x='punctuality_percentage',
            nbins=20,
            title='Distribution of Employee Punctuality Percentages',
            labels={'punctuality_percentage': 'Punctuality %', 'count': 'Number of Employees'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Position-wise performance
        if len(filtered_report['primary_position'].unique()) > 1:
            st.subheader("💼 Performance by Position")
            
            position_summary = filtered_report.groupby('primary_position').agg({
                'punctuality_percentage': 'mean',
                'days_scheduled': 'sum',
                'days_late': 'sum'
            }).reset_index()
            
            fig_pos = px.bar(
                position_summary,
                x='primary_position',
                y='punctuality_percentage',
                title='Average Punctuality by Position',
                labels={'punctuality_percentage': 'Average Punctuality %', 'primary_position': 'Position'}
            )
            fig_pos.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_pos, use_container_width=True)
    
    # --- Export Option ---
    st.subheader("💾 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Employee Report as CSV"):
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="Download Employee Performance CSV",
                data=csv,
                file_name=f"employee_performance_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )
    
    with col2:
        if not terminated_2025.empty and st.button("📥 Download Turnover Report as CSV"):
            turnover_csv = terminated_display.to_csv(index=False)
            st.download_button(
                label="Download Turnover Analysis CSV",
                data=turnover_csv,
                file_name=f"turnover_analysis_2025_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv'
            )

# --- Color Legend ---
st.markdown("""
**Punctuality Color Legend:**
- 🟢 **Green (95%+)**: Excellent punctuality
- 🟢 **Medium Green (90-94%)**: Very good punctuality  
- 🟡 **Yellow-Orange (85-89%)**: Good punctuality
- 🟠 **Bright Orange (80-84%)**: Fair punctuality
- 🟠 **Deep Orange (75-79%)**: Poor punctuality
- 🟠 **Dark Orange (70-74%)**: Very poor punctuality
- 🔴 **Red (<70%)**: Critical punctuality issues

**Labor Turnover Calculation:**
- **Active Employees**: All employees with status = 'active'
- **Terminated Employees**: Employees with status = 'terminated' (filtered by 2025 last edit date if available)
- **Turnover Ratio**: (Terminated Employees / Total Employees) × 100%
- **Benchmark**: <10% Excellent, 10-15% Acceptable, 15-20% Moderate Risk, >20% High Risk

**Note**: Employees with the following names are excluded from all calculations and displays: zzz, yyy, USD, Test, Parth, Kunal, rita
""")

# Display date range info
if date_range and len(date_range) == 2:
    st.info(f"📅 Attendance data analyzed for period: {date_range[0]} to {date_range[1]}")
else:
    st.info("📅 Showing all available attendance data")

st.info("📊 Turnover analysis includes terminated employees compared to currently active employees. Date filtering applied when last_edit_date column is available.")
