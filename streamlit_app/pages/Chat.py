# streamlit_app/pages/AI_QA_Bot.py
import streamlit as st
import pandas as pd
from supabase import create_client
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# --- Config ---
st.set_page_config(page_title="AI Chatbot - Inventory QA", layout="wide")
st.title("🤖 Ask AI About Inventory")

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Load Data from Supabase ---
@st.cache_data(ttl=3600)
def fetch_data():
    data = supabase.table("donut_sales_hourly").select("date, product_name, quantity").limit(1000).execute()
    return pd.DataFrame(data.data)

df = fetch_data()

# --- Format into Chunks for Embedding ---
chunks = [
    f"Date: {row['date']}, Product: {row['product_name']}, Quantity: {row['quantity']}"
    for _, row in df.iterrows()
]

# --- Embeddings + Vector Store ---
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])
vectorstore = FAISS.from_texts(chunks, embeddings)
retriever = vectorstore.as_retriever()

# --- QA Chain ---
llm = ChatOpenAI(temperature=0, openai_api_key=st.secrets["OPENAI_API_KEY"])
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# --- Ask a Question ---
query = st.text_input("Ask a question about donuts, waste, or inventory:")
if query:
    with st.spinner("Thinking..."):
        response = qa_chain.run(query)
        st.success(response)
