import streamlit as st
from sqlalchemy import create_engine
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import create_sql_agent
from langchain.chat_models import ChatOpenAI
from urllib.parse import quote_plus

# --- Streamlit page setup ---
st.set_page_config(page_title="Inventory Q&A", layout="wide")
st.title("📦 Inventory Q&A")

# --- Load from secrets.toml ---
openai_api_key = st.secrets["OPENAI_API_KEY"]
supabase_url = st.secrets["SUPABASE_URL"]       # e.g. https://ertcdieopoecjddamgkx.supabase.co
supabase_key = st.secrets["SUPABASE_KEY"]       # You are using this as the actual DB password

# --- Dynamically build DB URL without changing secret format ---
host = supabase_url.replace("https://", "db.")  # → db.ertcdieopoecjddamgkx.supabase.co
encoded_pw = quote_plus(supabase_key)
db_url = f"postgresql://postgres:{encoded_pw}@{host}:5432/postgres"

# --- Connect to Supabase DB ---
engine = create_engine(db_url)
db = SQLDatabase(engine=engine)

# --- Initialize LLM + LangChain Agent ---
llm = ChatOpenAI(temperature=0, model="gpt-4", openai_api_key=openai_api_key)
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True)

# --- Chat UI ---
query = st.text_input("Ask a question about inventory:")
if query:
    with st.spinner("Thinking..."):
        try:
            response = agent_executor.run(query)
            st.success(response)
        except Exception as e:
            st.error(f"❌ Error: {e}")
