import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from sqlalchemy import create_engine

# --- Streamlit page setup ---
st.set_page_config(page_title="Inventory Q&A", layout="wide")
st.title("📦 Inventory Q&A")

# --- Load from secrets.toml ---
openai_api_key = st.secrets["OPENAI_API_KEY"]
db_url = st.secrets["SUPABASE_DB_URL"]

# --- Connect to Supabase PostgreSQL ---
engine = create_engine(db_url)
db = SQLDatabase(engine=engine)

# --- Initialize OpenAI LLM ---
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=openai_api_key)

# --- Create SQL Agent with LangChain ---
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)

# --- Streamlit interface ---
query = st.text_input("Ask a question about inventory:")
if query:
    with st.spinner("Thinking..."):
        try:
            response = agent_executor.run(query)
            st.success(response)
        except Exception as e:
            st.error(f"❌ Error: {e}")
