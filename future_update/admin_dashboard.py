import streamlit as st
from auth_utils import (
    require_role, 
    check_authentication, 
    show_user_info, 
    show_navigation,
    init_supabase
)

# Page configuration
st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🔧",
    layout="wide"
)

@require_role(['admin'])
def admin_dashboard():
    # Show user info and navigation
    show_user_info()
    show_navigation()
    
    st.title("🔧 Admin Dashboard")
    st.write("Welcome to the admin dashboard! Only admins can see this page.")
    
    # Initialize Supabase
    supabase = init_supabase()
    
    # Admin statistics
    col1, col2, col3 = st.columns(3)
    
    try:
        # Get user statistics
        users_result = supabase.table('users').select('role').execute()
        users_data = users_result.data
        
        total_users = len(users_data)
        admin_count = len([u for u in users_data if u['role'] == 'admin'])
        editor_count = len([u for u in users_data if u['role'] == 'editor'])
        viewer_count = len([u for u in users_data if u['role'] == 'viewer'])
        
        with col1:
            st.metric("Total Users", total_users)
            st.metric("Admins", admin_count)
        
        with col2:
            st.metric("Editors", editor_count)
            st.metric("Viewers", viewer_count)
        
        with col3:
            st.info("📊 System Status: Healthy")
            
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")
    
    st.divider()
    
    # Admin actions
    st.subheader("🎛️ Admin Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👥 Manage Users", use_container_width=True):
            st.switch_page("pages/user_management.py")
        
        if st.button("⚙️ System Settings", use_container_width=True):
            st.switch_page("pages/settings.py")
    
    with col2:
        if st.button("📊 View Reports", use_container_width=True):
            st.switch_page("pages/reports.py")
        
        if st.button("🏠 Back to Home", use_container_width=True):
            st.switch_page("app.py")

# Run the protected function
if check_authentication():
    admin_dashboard()
else:
    st.error("Please log in to access this page.")
    if st.button("🔑 Login"):
        st.switch_page("app.py")