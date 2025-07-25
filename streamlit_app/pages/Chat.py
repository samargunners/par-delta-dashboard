# streamlit_app/pages/AI_QA_Bot.py
import streamlit as st
import pandas as pd
from supabase import create_client
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores.faiss import FAISS
import traceback

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

# --- Embeddings + FAISS Vector Store ---
vectorstore = None
retriever = None
try:
    embeddings = OpenAIEmbeddings(
        openai_api_key=st.secrets["OPENAI_API_KEY"],
        model="text-embedding-3-small"
    )

    # Batching embeddings to avoid overload
    def embed_in_batches(texts, batch_size=100):
        embedded_chunks = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embedded_chunks.extend(embeddings.embed_documents(batch))
        return FAISS.from_embeddings(embedded_chunks, texts, embeddings)

    vectorstore = FAISS.from_texts(chunks, embeddings)  # Or use embed_in_batches if needed
    retriever = vectorstore.as_retriever()
except Exception as e:
    st.error(f"❌ Error during embedding/vectorstore creation: {e}")
    st.text(traceback.format_exc())

# --- QA Chain ---
if retriever:
    try:
        llm = ChatOpenAI(temperature=0, openai_api_key=st.secrets["OPENAI_API_KEY"])
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