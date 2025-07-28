# streamlit_app/pages/AI_QA_Bot.py
import streamlit as st
import pandas as pd
import traceback
from supabase import create_client
from langchain.chains import RetrievalQA
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFaceHub  # Free LLM from Hugging Face

# --- Streamlit Page Config ---
st.set_page_config(page_title="AI Chatbot - Inventory QA", layout="wide")
st.title("🤖 Ask AI About Inventory")

# --- Supabase Setup ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- Load Data from Multiple Supabase Tables ---
@st.cache_data(ttl=3600)
def fetch_all_data():
    tables = {
        "donut_sales_hourly": ["date", "product_name", "quantity"],
        "employee_clockin": ["employee_name", "employee_id", "time_in", "time_out", "total_time"],
        "variance_report_summary": ["reporting_period", "product_name", "qty_variance", "variance"],
        "actual_table_labor": ["pc_number", "date", "hour_range", "actual_hours", "actual_labor"],
        "ideal_table_labor": ["pc_number", "date", "hour_range", "ideal_hours"],
        "schedule_table_labor": ["pc_number", "date", "hour_range", "scheduled_hours"],
        "employee_profile": ["employee_number", "first_name", "last_name", "primary_position", "primary_location", "status"],
        "employee_schedules": ["employee_id", "date", "start_time", "end_time"],
        "usage_overview": ["date", "product_type", "ordered_qty", "wasted_qty", "waste_percent"],
        "stores": ["pc_number", "store_name", "address"]
    }
    data_chunks = []
    for table, columns in tables.items():
        try:
            response = supabase.table(table).select(", ".join(columns)).limit(1000).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                for _, row in df.iterrows():
                    chunk = f"TABLE: {table} | " + " | ".join([f"{col}: {row[col]}" for col in columns if col in row and pd.notnull(row[col])])
                    data_chunks.append(chunk[:500])
        except Exception as e:
            st.error(f"⚠️ Failed to load data from {table}: {e}")
    return data_chunks

chunks = fetch_all_data()

# --- Use HuggingFace Embeddings (Free and Local) ---
try:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_texts(chunks, embeddings)
    retriever = vectorstore.as_retriever()
except Exception as e:
    st.error(f"❌ Failed to embed documents: {e}")
    st.text(traceback.format_exc())
    retriever = None

# --- QA Chain Using HuggingFace LLM (Free) ---
if retriever:
    try:
        # ✅ Using a free open-source model via HuggingFace Hub
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-base",
            huggingfacehub_api_token=st.secrets["HUGGINGFACEHUB_API_TOKEN"],
            model_kwargs={"temperature": 0, "max_length": 512}
        )

        qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

        # --- Ask a Question ---
        query = st.text_input("Ask a question about donuts, waste, labor, or employees:")
        if query:
            with st.spinner("Thinking..."):
                response = qa_chain.run(query)
                st.success(response)
    except Exception as e:
        st.error(f"❌ Error in QA chain: {e}")
        st.text(traceback.format_exc())
else:
    st.warning("🔄 Waiting for retriever to be ready.")
