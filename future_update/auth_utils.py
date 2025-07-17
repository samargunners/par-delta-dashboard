import streamlit as st
from supabase import create_client, Client
import requests
import jwt
import time
from urllib.parse import urlencode
import secrets

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)

def get_google_oauth_url():
    """Generate Google OAuth URL"""
    params = {
        'client_id': st.secrets["GOOGLE_CLIENT_ID"],
        'redirect_uri': st.secrets["GOOGLE_REDIRECT_URI"],
        'scope': 'openid email profile',
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': secrets.token_urlsafe(32)
    }
    
    # Store state in session for validation
    st.session_state.oauth_state = params['state']
    
    return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"

def exchange_code_for_tokens(code, state):
    """Exchange authorization code for access token"""
    # Validate state
    if state != st.session_state.get('oauth_state'):
        raise ValueError("Invalid state parameter")
    
    token_data = {
        'client_id': st.secrets["GOOGLE_CLIENT_ID"],
        'client_secret': st.secrets["GOOGLE_CLIENT_SECRET"],
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': st.secrets["GOOGLE_REDIRECT_URI"]
    }
    
    response = requests.post(
        'https://oauth2.googleapis.com/token',
        data=token_data
    )
    
    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.text}")
    
    return response.json()

def get_user_info(access_token):
    """Get user info from Google API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get user info: {response.text}")
    
    return response.json()

def create_or_update_user(supabase: Client, user_info):
    """Create or update user in Supabase"""
    try:
        # Check if user exists
        existing_user = supabase.table('users').select('*').eq('google_id', user_info['id']).execute()
        
        user_data = {
            'google_id': user_info['id'],
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'last_login': 'now()'
        }
        
        if existing_user.data:
            # Update existing user
            result = supabase.table('users').update(user_data).eq('google_id', user_info['id']).execute()
            return result.data[0]
        else:
            # Create new user with default role
            user_data['role'] = 'viewer'
            result = supabase.table('users').insert(user_data).execute()
            return result.data[0]
            
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def check_authentication():
    """Check if user is authenticated"""
    return 'user' in st.session_state and st.session_state.user is not None

def login_with_google():
    """Handle Google OAuth login"""
    # Check for OAuth callback
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        try:
            # Exchange code for tokens
            tokens = exchange_code_for_tokens(query_params['code'], query_params['state'])
            
            # Get user info
            user_info = get_user_info(tokens['access_token'])
            
            # Create/update user in database
            supabase = init_supabase()
            user_data = create_or_update_user(supabase, user_info)
            
            if user_data:
                # Store user in session
                st.session_state.user = user_data
                st.session_state.access_token = tokens['access_token']
                
                # Clear OAuth state
                if 'oauth_state' in st.session_state:
                    del st.session_state.oauth_state
                
                # Clear URL parameters
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Failed to create user account")
                
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            st.query_params.clear()

def logout_user():
    """Logout user and clear session"""
    keys_to_remove = ['user', 'access_token', 'oauth_state']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def require_role(required_roles):
    """Decorator to restrict access to certain roles"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_authentication():
                st.error("Please log in to access this page.")
                st.stop()
            
            user_role = st.session_state.user.get('role', 'viewer')
            if user_role not in required_roles:
                st.error("You don't have permission to access this page.")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def show_login_page():
    """Show login page with Google OAuth button"""
    st.title("🔐 Login Required")
    st.write("Please sign in with your Google account to continue.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔑 Sign in with Google", use_container_width=True, type="primary"):
            oauth_url = get_google_oauth_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={oauth_url}">', unsafe_allow_html=True)
            st.write("Redirecting to Google...")

def show_user_info():
    """Show user information in sidebar"""
    if check_authentication():
        user = st.session_state.user
        
        with st.sidebar:
            st.write("👤 **User Info**")
            
            # Display user picture if available
            if user.get('picture'):
                st.image(user['picture'], width=60)
            
            st.write(f"**Name:** {user.get('name', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'N/A')}")
            st.write(f"**Role:** {user.get('role', 'viewer').title()}")
            
            st.divider()
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()

def get_navigation_pages():
    """Get navigation pages based on user role"""
    if not check_authentication():
        return []
    
    user_role = st.session_state.user.get('role', 'viewer')
    
    # Define page access permissions
    pages = {
        'Home': ['admin', 'editor', 'viewer'],
        'Reports': ['admin', 'editor', 'viewer'],
        'User Management': ['admin', 'editor'],
        'Admin Dashboard': ['admin'],
        'Settings': ['admin']
    }
    
    # Filter pages based on user role
    accessible_pages = []
    for page_name, allowed_roles in pages.items():
        if user_role in allowed_roles:
            accessible_pages.append(page_name)
    
    return accessible_pages

def show_navigation():
    """Show navigation menu in sidebar"""
    if check_authentication():
        pages = get_navigation_pages()
        
        with st.sidebar:
            st.write("📋 **Navigation**")
            
            for page in pages:
                # Convert page name to file name
                file_name = page.lower().replace(' ', '_')
                
                if page == 'Home':
                    if st.button(f"🏠 {page}", use_container_width=True):
                        st.switch_page("app.py")
                else:
                    page_file = f"pages/{file_name}.py"
                    if st.button(f"📄 {page}", use_container_width=True):
                        st.switch_page(page_file)