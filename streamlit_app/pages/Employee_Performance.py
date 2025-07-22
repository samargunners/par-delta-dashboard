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
    
    # --- Summary Statistics ---
    st.subheader("📊 Summary Statistics")
    
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
    
    if st.button("📥 Download Employee Report as CSV"):
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download CSV file",
            data=csv,
            file_name=f"employee_performance_report_{datetime.now().strftime('%Y%m%d')}.csv",
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
""")

# Display date range info
if date_range and len(date_range) == 2:
    st.info(f"📅 Attendance data analyzed for period: {date_range[0]} to {date_range[1]}")
else:
    st.info("📅 Showing all available attendance data")
