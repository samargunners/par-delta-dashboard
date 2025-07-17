import streamlit as st
from auth_utils import (
    require_role, 
    check_authentication, 
    show_user_info, 
    show_navigation
)

# Page configuration
st.set_page_config(
    page_title="Reports",
    page_icon="📊",
    layout="wide"
)

@require_role(['admin', 'editor', 'viewer'])
def reports_page():
    # Show user info and navigation
    show_user_info()
    show_navigation()
    
    st.title("📊 Reports")
    st.write("This page is accessible to all authenticated users.")
    
    user_role = st.session_state.user.get('role', 'viewer')
    
    # Role-based content
    if user_role == 'admin':
        st.success("🔧 Admin View: You can see all reports and analytics.")
        
        # Admin-specific reports
        tab1, tab2, tab3 = st.tabs(["📈 Analytics", "👥 User Reports", "⚙️ System Reports"])
        
        with tab1:
            st.subheader("📈 Analytics Dashboard")
            st.info("Full analytics dashboard for admins")
            
            # Sample metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Revenue", "$10,000", "5%")
            with col2:
                st.metric("Active Users", "1,234", "12%")
            with col3:
                st.metric("Conversion Rate", "3.2%", "0.5%")
        
        with tab2:
            st.subheader("👥 User Activity Reports")
            st.info("Detailed user activity and engagement metrics")
            
            # Sample user data
            import pandas as pd
            sample_data = pd.DataFrame({
                'Date': pd.date_range('2024-01-01', periods=10),
                'Active Users': [100, 120, 130, 115, 140, 160, 150, 170, 180, 200],
                'New Signups': [10, 15, 12, 8, 20, 25, 18, 22, 28, 30]
            })
            
            st.line_chart(sample_data.set_index('Date'))
        
        with tab3:
            st.subheader("⚙️ System Performance")
            st.info("System health and performance metrics")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Server Uptime", "99.9%", "0.1%")
                st.metric("Response Time", "120ms", "-5ms")
            with col2:
                st.metric("Database Performance", "Excellent", "")
                st.metric("Error Rate", "0.01%", "-0.005%")
    
    elif user_role == 'editor':
        st.info("✏️ Editor View: You can see user reports and basic analytics.")
        
        # Editor-specific reports
        tab1, tab2 = st.tabs(["📈 Basic Analytics", "👥 User Reports"])
        
        with tab1:
            st.subheader("📈 Basic Analytics")
            st.info("Key metrics and performance indicators")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Active Users", "1,234", "12%")
            with col2:
                st.metric("Engagement Rate", "65%", "3%")
        
        with tab2:
            st.subheader("👥 User Engagement")
            st.info("User activity and engagement data")
            
            # Sample chart
            import pandas as pd
            sample_data = pd.DataFrame({
                'Date': pd.date_range('2024-01-01', periods=7),
                'Page Views': [500, 600, 550, 700, 800, 750, 900]
            })
            
            st.bar_chart(sample_data.set_index('Date'))
    
    else:  # viewer
        st.warning("👀 Viewer Access: You can see basic reports only.")
        
        st.subheader("📊 Basic Reports")
        st.info("Limited view of key metrics")
        
        # Basic metrics for viewers
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your Activity", "Active", "")
        with col2:
            st.metric("Last Update", "2 hours ago", "")
        
        # Simple chart
        import pandas as pd
        sample_data = pd.DataFrame({
            'Category': ['A', 'B', 'C', 'D'],
            'Values': [23, 45, 56, 78]
        })
        
        st.bar_chart(sample_data.set_index('Category'))
    
    # Common section for all users
    st.divider()
    st.subheader("📋 Recent Activity")
    
    activities = [
        "User logged in",
        "Report generated",
        "Data updated",
        "System maintenance completed"
    ]
    
    for activity in activities:
        st.write(f"• {activity}")

# Run the protected function
if check_authentication():
    reports_page()
else:
    st.error("Please log in to access this page.")
    if st.button("🔑 Login"):
        st.switch_page("app.py")