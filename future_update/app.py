import streamlit as st
from auth_utils import (
    check_authentication, 
    login_with_google, 
    show_login_page,
    show_user_info,
    show_navigation
)

# Page configuration
st.set_page_config(
    page_title="Your App",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Handle OAuth callback
login_with_google()

def main():
    # Check authentication
    if not check_authentication():
        show_login_page()
        return
    
    # Show user info and navigation
    show_user_info()
    show_navigation()
    
    # Main content
    st.title("🏠 Welcome to Your App")
    st.write("You are successfully logged in!")
    
    user = st.session_state.user
    
    # Dashboard content based on role
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Your Dashboard")
        st.metric("Your Role", user.get('role', 'viewer').title())
        st.metric("Last Login", user.get('last_login', 'N/A'))
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        role = user.get('role', 'viewer')
        
        if role == 'admin':
            st.success("🔧 You have admin access to all features")
            if st.button("👥 Manage Users"):
                st.switch_page("pages/user_management.py")
            if st.button("📊 Admin Dashboard"):
                st.switch_page("pages/admin_dashboard.py")
        
        elif role == 'editor':
            st.info("✏️ You have editor access")
            if st.button("👥 Manage Users"):
                st.switch_page("pages/user_management.py")
        
        else:
            st.warning("👀 You have viewer access")
        
        if st.button("📈 View Reports"):
            st.switch_page("pages/reports.py")

if __name__ == "__main__":
    main()