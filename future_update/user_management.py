import streamlit as st
from auth_utils import (
    require_role, 
    check_authentication, 
    show_user_info, 
    show_navigation,
    init_supabase
)
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="User Management",
    page_icon="👥",
    layout="wide"
)

@require_role(['admin', 'editor'])
def user_management():
    # Show user info and navigation
    show_user_info()
    show_navigation()
    
    st.title("👥 User Management")
    st.write("Manage user roles and permissions.")
    
    # Initialize Supabase
    supabase = init_supabase()
    
    # Get current user role
    current_user_role = st.session_state.user.get('role', 'viewer')
    
    try:
        # Fetch all users
        users_result = supabase.table('users').select('*').order('created_at', desc=True).execute()
        users_data = users_result.data
        
        if not users_data:
            st.info("No users found.")
            return
        
        # Create DataFrame for better display
        df = pd.DataFrame(users_data)
        
        # Display users in a nice format
        st.subheader("📋 User List")
        
        for user in users_data:
            with st.expander(f"👤 {user['name']} ({user['email']})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Google ID:** {user['google_id']}")
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Created:** {user['created_at']}")
                    st.write(f"**Last Login:** {user['last_login']}")
                
                with col2:
                    if user.get('picture'):
                        st.image(user['picture'], width=80)
                
                with col3:
                    # Role management
                    current_role = user.get('role', 'viewer')
                    
                    # Only admins can change roles to admin
                    if current_user_role == 'admin':
                        role_options = ['admin', 'editor', 'viewer']
                    else:
                        role_options = ['editor', 'viewer']
                    
                    # Don't allow users to change their own role
                    if user['google_id'] == st.session_state.user['google_id']:
                        st.info(f"Current role: **{current_role.title()}**")
                        st.write("*(Cannot change your own role)*")
                    else:
                        new_role = st.selectbox(
                            "Role:",
                            role_options,
                            index=role_options.index(current_role) if current_role in role_options else 0,
                            key=f"role_{user['id']}"
                        )
                        
                        if new_role != current_role:
                            if st.button(f"Update Role", key=f"update_{user['id']}", type="primary"):
                                try:
                                    supabase.table('users').update({
                                        'role': new_role
                                    }).eq('id', user['id']).execute()
                                    
                                    st.success(f"Role updated to {new_role.title()}!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update role: {str(e)}")
        
        # Summary statistics
        st.divider()
        st.subheader("📊 User Statistics")
        
        role_counts = df['role'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(df))
        
        with col2:
            st.metric("Admins", role_counts.get('admin', 0))
        
        with col3:
            st.metric("Editors", role_counts.get('editor', 0))
        
        with col4:
            st.metric("Viewers", role_counts.get('viewer', 0))
        
        # Show data table
        with st.expander("📊 Raw Data View"):
            st.dataframe(
                df[['name', 'email', 'role', 'created_at', 'last_login']],
                use_container_width=True
            )
        
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")

# Run the protected function
if check_authentication():
    user_management()
else:
    st.error("Please log in to access this page.")
    if st.button("🔑 Login"):
        st.switch_page("app.py")