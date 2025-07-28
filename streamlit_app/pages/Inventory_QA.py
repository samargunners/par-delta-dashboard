import streamlit as st
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.chat_models import ChatOpenAI

# --- Streamlit page setup ---
st.set_page_config(page_title="Inventory Q&A", layout="wide")
st.title("📦 Inventory Q&A")

# --- Load secrets from Streamlit Cloud ---
openai_api_key = st.secrets["OPENAI_API_KEY"]

# --- Supabase DB connection details ---
db_user = st.secrets["SUPABASE_DB_USER"]
db_password = st.secrets["SUPABASE_DB_PASSWORD"]
db_host = st.secrets["SUPABASE_DB_HOST"]
db_port = st.secrets["SUPABASE_DB_PORT"]
db_name = st.secrets["SUPABASE_DB_NAME"]

# --- Encode password and build SQLAlchemy URL ---
encoded_pw = quote_plus(db_password)
db_url = f"postgresql://{db_user}:{encoded_pw}@{db_host}:{db_port}/{db_name}"

# --- Connect to Supabase via SQLAlchemy ---
try:
    engine = create_engine(db_url)
    db = SQLDatabase(engine=engine)
except Exception as e:
    st.error("❌ Failed to connect to the database.")
    st.stop()

# --- Initialize LLM and LangChain SQL Agent ---
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=openai_api_key)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)

# --- Streamlit chat UI ---
query = st.text_input("Ask a question about inventory (e.g. top 5 waste items):")
if query:
    with st.spinner("Thinking..."):
        try:
            response = agent_executor.run(query)
            st.success(response)
        except Exception as e:
            st.error(f"❌ Error: {e}")
