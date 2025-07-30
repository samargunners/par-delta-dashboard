"""
Minimal Chat.py for debugging startup issues
"""

import streamlit as st
import traceback

# --- Page Config ---
st.set_page_config(page_title="AI Business Data Assistant", layout="wide")
st.title("🤖 AI Business Intelligence Assistant - Debug Mode")

# --- Test Secrets ---
st.subheader("🔧 Configuration Check")

try:
    supabase_url = st.secrets.get("SUPABASE_URL")
    supabase_key = st.secrets.get("SUPABASE_KEY") 
    openai_key = st.secrets.get("OPENAI_API_KEY")
    
    if supabase_url:
        st.success("✅ SUPABASE_URL found")
    else:
        st.error("❌ SUPABASE_URL not found in secrets")
    
    if supabase_key:
        st.success("✅ SUPABASE_KEY found")
    else:
        st.error("❌ SUPABASE_KEY not found in secrets")
    
    if openai_key:
        st.success("✅ OPENAI_API_KEY found")
    else:
        st.warning("⚠️ OPENAI_API_KEY not found in secrets (will use HuggingFace)")
        
except Exception as e:
    st.error(f"❌ Error accessing secrets: {e}")
    st.text(traceback.format_exc())

# --- Test Imports ---
st.subheader("📦 Import Check")

try:
    from supabase import create_client
    st.success("✅ Supabase import successful")
except Exception as e:
    st.error(f"❌ Supabase import failed: {e}")

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    st.success("✅ LangChain OpenAI import successful")
except Exception as e:
    st.error(f"❌ LangChain OpenAI import failed: {e}")

try:
    from langchain_community.vectorstores import FAISS
    st.success("✅ FAISS import successful")
except Exception as e:
    st.error(f"❌ FAISS import failed: {e}")

try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    st.success("✅ HuggingFace embeddings import successful")
except Exception as e:
    st.error(f"❌ HuggingFace embeddings import failed: {e}")

# --- Test Database Connection ---
st.subheader("🗄️ Database Connection Check")

if st.button("Test Supabase Connection"):
    try:
        from supabase import create_client
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
        
        # Try to list tables
        response = supabase.table("stores").select("*").limit(1).execute()
        st.success(f"✅ Database connection successful! Found stores table with {len(response.data)} records")
        
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.text(traceback.format_exc())

st.info("If all checks pass, the main Chat.py should work correctly. If not, fix the issues shown above.")

if st.button("🚀 Load Full Chat Interface"):
    st.info("Switch to the main Chat.py file to use the full RAG interface.")
