import streamlit as st

# --- Simple login demo ---
def login():
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if username == "test" and password == "test":
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.sidebar.success("Logged in!")
        else:
            st.sidebar.error("Invalid username or password")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = ""
        st.experimental_rerun()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()
else:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.get('username', '')}")
    logout()

st.set_page_config(page_title="Par Delta Dashboard", layout="wide")
st.title("📊 Par Delta Operational Dashboard")

st.markdown("""
Welcome to the central dashboard for Dunkin' operations at Par Delta.  
Use the left sidebar to navigate between modules:
- 🍩 Donut Waste & Gap
- ⏱️ Labor Punctuality
- 💼 Ideal vs Actual Labor
- 📦 Inventory Variance

Live data is loaded from Supabase.
""")
