# streamlit_app/pages/AI_QA_Bot.py
import streamlit as st
import pandas as pd
import traceback
from supabase import create_client
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores.faiss import FAISS

# Try OpenAI embeddings first, fallback to HuggingFace if quota exceeded
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings

# --- Streamlit Page Config ---
st.set_page_config(page_title="AI Chatbot - Inventory QA", layout="wide")
st.title("🤖 Ask AI About Inventory")

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Load Data from Supabase ---
@st.cache_data(ttl=3600)
def fetch_data():
    try:
        response = supabase.table("donut_sales_hourly").select("date, product_name, quantity").limit(1000).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"❌ Failed to load data from Supabase: {e}")
        return pd.DataFrame()

df = fetch_data()

# --- Format into Chunks ---
def clean_and_split_chunks(df, max_len=500):
    raw_chunks = [
        f"Date: {row['date']}, Product: {row['product_name']}, Quantity: {row['quantity']}"
        for _, row in df.iterrows()
    ]
    return [chunk[:max_len] for chunk in raw_chunks]

chunks = clean_and_split_chunks(df)

# --- Try OpenAI Embeddings, fallback to HuggingFace if quota exceeded ---
retriever = None
try:
    # ✅ Try using OpenAI's cheapest embedding model
    embeddings = OpenAIEmbeddings(
        openai_api_key=st.secrets["OPENAI_API_KEY"],
        model="text-embedding-3-small"  # Cheapest embedding model
    )
    vectorstore = FAISS.from_texts(chunks, embeddings)
    retriever = vectorstore.as_retriever()
except Exception as e:
    if "insufficient_quota" in str(e):
        st.warning("⚠️ OpenAI quota exceeded. Falling back to HuggingFace local embeddings.")
        # ✅ Fallback to free local embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_texts(chunks, embeddings)
        retriever = vectorstore.as_retriever()
    else:
        st.error(f"❌ Embedding setup failed: {e}")
        st.text(traceback.format_exc())

# --- QA Chain ---
if retriever:
    try:
        # ✅ Use GPT-3.5 Turbo for lowest cost LLM interaction
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=st.secrets["OPENAI_API_KEY"],
            model="gpt-3.5-turbo"  # Cheapest OpenAI chat model
        )
        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        # --- Ask a Question ---
        query = st.text_input("Ask a question about donuts, waste, or inventory:")
        if query:
            with st.spinner("Thinking..."):
                response = qa_chain.run(query)
                st.success(response)
    except Exception as e:
        st.error(f"❌ Error in QA chain: {e}")
        st.text(traceback.format_exc())
else:
    st.warning("🔄 Waiting for retriever to be ready.")
