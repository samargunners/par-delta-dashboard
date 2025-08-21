import streamlit as st
import pandas as pd
import traceback
import time
from datetime import datetime

# --- Streamlit Page Config ---
st.set_page_config(page_title="AI Business Data Assistant", layout="wide")
st.title("🤖 AI Business Intelligence Assistant")
st.markdown("Ask questions about your business data using natural language. The AI will search through your labor, sales, inventory, and employee data to provide insights.")

# --- Startup Safety Check ---
startup_error = False

try:
    from supabase import create_client
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain.chains import RetrievalQA
    from langchain_community.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain_community.embeddings import HuggingFaceEmbeddings
except ImportError as e:
    st.error(f"❌ Import error: {e}")
    st.error("Please check that all required packages are installed correctly.")
    st.info("Try running: pip install -r requirements.txt")
    startup_error = True

if startup_error:
    st.stop()

# --- Display System Status ---
with st.expander("🔧 System Status", expanded=False):
    st.info("✅ RAG (Retrieval-Augmented Generation) System Active")
    st.write("- **Data Sources**: Supabase database tables")
    st.write("- **Embedding Model**: OpenAI text-embedding-3-small (with HuggingFace fallback)")
    st.write("- **Vector Store**: FAISS for similarity search")
    st.write("- **LLM**: OpenAI GPT-3.5 Turbo")
    st.write("- **Enhancement**: Custom prompts, source tracking, intelligent document chunking")

# --- Supabase Setup ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"❌ Supabase connection error: {e}")
    st.error("Please check your Supabase credentials in secrets.toml")
    st.stop()

# --- Load Data from Supabase ---
@st.cache_data(ttl=3600)
def fetch_all_data():
    tables_data = {}
    table_names = [
        "actual_table_labor",
        "donut_sales_hourly", 
        "employee_clockin",
        "employee_profile",
        "employee_schedules",
        "hourly_labor_summary",
        "ideal_table_labor",
        "schedule_table_labor",
        "stores",
        "usage_overview",
        "variance_report_summary"
    ]
    
    for table_name in table_names:
        try:
            response = supabase.table(table_name).select("*").execute()
            tables_data[table_name] = pd.DataFrame(response.data)
        except Exception as e:
            st.warning(f"⚠️ Could not load {table_name}: {e}")
            tables_data[table_name] = pd.DataFrame()
    
    return tables_data

try:
    all_data = fetch_all_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# --- Enhanced Document Processing with Better Chunking ---
def create_enhanced_documents(all_data):
    """Create well-structured documents with metadata for better RAG performance"""
    documents = []
    
    for table_name, df in all_data.items():
        if not df.empty:
            # Create table summary as context
            table_summary = f"This is data from table '{table_name}' with {len(df)} records. "
            table_summary += f"Columns: {', '.join(df.columns.tolist())}."
            
            # Add table summary as a document
            documents.append(Document(
                page_content=table_summary,
                metadata={
                    "table_name": table_name,
                    "type": "table_summary",
                    "record_count": len(df)
                }
            ))
            
            # Process each row with enhanced context
            for idx, row in df.iterrows():
                # Create meaningful row content
                row_content = f"Record from {table_name}: "
                row_data = []
                
                for col, val in row.items():
                    if pd.notna(val) and str(val).strip():
                        # Add semantic context to values
                        if 'date' in col.lower() or 'time' in col.lower():
                            row_data.append(f"The {col} is {val}")
                        elif 'name' in col.lower() or 'id' in col.lower():
                            row_data.append(f"The {col} is {val}")
                        elif 'amount' in col.lower() or 'cost' in col.lower() or 'price' in col.lower():
                            row_data.append(f"The {col} is ${val}" if isinstance(val, (int, float)) else f"The {col} is {val}")
                        else:
                            row_data.append(f"The {col} is {val}")
                
                if row_data:
                    row_content += ". ".join(row_data) + "."
                    
                    documents.append(Document(
                        page_content=row_content,
                        metadata={
                            "table_name": table_name,
                            "type": "record",
                            "row_index": idx,
                            "columns": list(row.index[pd.notna(row)].tolist())
                        }
                    ))
    
    return documents

# --- Improved Text Splitting ---
def split_documents_intelligently(documents):
    """Split documents using intelligent chunking"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(documents)
    return split_docs

# --- Process Data into Enhanced Documents ---
try:
    documents = create_enhanced_documents(all_data)
    split_docs = split_documents_intelligently(documents)
    
    if not split_docs:
        st.warning("⚠️ No documents created from data. Please check your database connection.")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Error processing documents: {e}")
    st.text(traceback.format_exc())
    st.stop()

# --- Try OpenAI Embeddings, fallback to HuggingFace if quota exceeded ---
retriever = None

# Check if OpenAI API key is available
openai_key = st.secrets.get("OPENAI_API_KEY")
if not openai_key:
    st.warning("⚠️ OpenAI API key not found. Using HuggingFace embeddings only.")
    try:
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 5}
        )
    except Exception as e:
        st.error(f"❌ HuggingFace embedding setup failed: {e}")
        st.text(traceback.format_exc())
else:
    try:
        # ✅ Try using OpenAI's cheapest embedding model
        embeddings = OpenAIEmbeddings(
            openai_api_key=openai_key,
            model="text-embedding-3-small"  # Cheapest embedding model
        )
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 5}
        )
    except Exception as e:
        if "insufficient_quota" in str(e) or "quota" in str(e).lower():
            st.warning("⚠️ OpenAI quota exceeded. Falling back to HuggingFace local embeddings.")
            try:
                # ✅ Fallback to free local embeddings
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vectorstore = FAISS.from_documents(split_docs, embeddings)
                retriever = vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={"score_threshold": 0.5, "k": 5}
                )
            except Exception as fallback_e:
                st.error(f"❌ Fallback embedding setup failed: {fallback_e}")
                st.text(traceback.format_exc())
        else:
            st.error(f"❌ OpenAI embedding setup failed: {e}")
            st.text(traceback.format_exc())

# --- Enhanced QA Chain with Custom Prompt ---
if retriever:
    try:
        # Check if OpenAI API key is available for LLM
        if openai_key:
            # ✅ Custom prompt template for business data QA
            custom_prompt = PromptTemplate(
                template="""You are an expert business analyst assistant. Use the following context to answer the question about business operations, labor, sales, inventory, or employee data.

Context information:
{context}

Question: {question}

Instructions:
1. Answer based only on the provided context
2. If you can't find specific information in the context, say so clearly
3. Provide specific numbers, dates, and details when available
4. Format your response in a clear, professional manner
5. If relevant, mention which data table(s) the information comes from

Answer:""",
                input_variables=["context", "question"]
            )
            
            # ✅ Use GPT-3.5 Turbo for lowest cost LLM interaction
            llm = ChatOpenAI(
                temperature=0,
                openai_api_key=openai_key,
                model="gpt-4o"  # More powerful, still reasonably priced OpenAI model
            )
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm, 
                retriever=retriever,
                chain_type_kwargs={"prompt": custom_prompt},
                return_source_documents=True
            )

            # --- Enhanced Chat Interface ---
            col1, col2 = st.columns([3, 1])
            
            with col1:
                query = st.text_input("Ask a question about labor, sales, employees, schedules, inventory, or any business data:")
            
            with col2:
                show_sources = st.checkbox("Show source data", value=False)
            
            if query:
                with st.spinner("Analyzing your data..."):
                    try:
                        result = qa_chain(query)
                        response = result["result"]
                        source_docs = result["source_documents"]
                        
                        # Display the answer
                        st.success("📊 **Analysis Result:**")
                        st.write(response)
                        
                        # Optionally show source documents
                        if show_sources and source_docs:
                            st.expander_label = f"📋 Source Data ({len(source_docs)} documents)"
                            with st.expander(st.expander_label):
                                for i, doc in enumerate(source_docs):
                                    st.write(f"**Source {i+1}** (Table: {doc.metadata.get('table_name', 'Unknown')}):")
                                    st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                                    st.write("---")
                                    
                    except Exception as inner_e:
                        st.error(f"❌ Error processing your question: {inner_e}")
                        st.text(traceback.format_exc())
        else:
            st.warning("🔑 OpenAI API key required for question answering. Please add OPENAI_API_KEY to your secrets.")
            st.info("You can still browse the available data below.")
            
            # Show data summary without QA
            query = st.text_input("Search data (basic keyword search):")
            if query:
                # Simple keyword search through documents
                matching_docs = []
                for doc in split_docs:
                    if query.lower() in doc.page_content.lower():
                        matching_docs.append(doc)
                
                if matching_docs:
                    st.success(f"📋 Found {len(matching_docs)} matching records:")
                    for i, doc in enumerate(matching_docs[:5]):  # Show first 5 matches
                        with st.expander(f"Match {i+1} from {doc.metadata.get('table_name', 'Unknown')}"):
                            st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                else:
                    st.info("No matching records found.")
                    
    except Exception as e:
        st.error(f"❌ Error in QA chain: {e}")
        st.text(traceback.format_exc())
else:
    st.warning("🔄 Waiting for retriever to be ready.")

# --- Additional Features ---
st.sidebar.header("💡 Sample Questions")
sample_questions = [
    "What is the total labor cost for this week?",
    "Which employees worked overtime recently?",
    "What are the top-selling donut flavors?",
    "Show me variance in labor costs vs targets",
    "Which store locations have inventory issues?",
    "What are the peak sales hours?",
    "How many employees are scheduled for tomorrow?",
    "What's the average hourly labor cost?"
]

for question in sample_questions:
    if st.sidebar.button(f"💬 {question}", key=f"sample_{question}"):
        st.session_state.sample_query = question

# Auto-fill sample question if clicked
if "sample_query" in st.session_state:
    st.text_input("Ask a question about labor, sales, employees, schedules, inventory, or any business data:", 
                  value=st.session_state.sample_query, key="auto_query")
    del st.session_state.sample_query
