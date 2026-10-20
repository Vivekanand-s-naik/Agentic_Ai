import streamlit as st
import psycopg
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from dotenv import load_dotenv
import os
load_dotenv()

@st.cache_resource
def load_db():
    # function to get the checkpointer, store and pool
    db_uri = os.getenv("DB_URI")
    pool = ConnectionPool(
        conninfo=db_uri,
        min_size=1,
        max_size=100,
        kwargs={"autocommit": True}
    )
    store = PostgresStore(pool)
    checkpointer = PostgresSaver(pool)
    store.setup()
    checkpointer.setup()
    return pool, store, checkpointer

pool, store, checkpointer = load_db()

st.title("🧠☠️ Deepagents Chatbot")

st.write("Planning . Virtual file system . Context engineering (AGENTS.md + memory) . Skills . Subagents (incl. structured output) . Swappable backends . Thread memory via checkpointer")

# Sidebar
st.sidebar.header("Agent COnfigurations")

model_mapping = {
    "Alibaba Qwen 3.8 27B (Fast & Multimodal)": "qwen/qwen3.8-27b",
    "OpenAI GPT-OSS 20B (Standard Reasoning)": "openai/gpt-oss-20b",
    "OpenAI GPT-OSS 120B (High Reasoning)": "openai/gpt-oss-120b"
}

selected_model_name = st.sidebar.selectbox(
    label="Select Active Groq Model:",
    options=list(model_mapping.keys()),
    index=0  # Default to Qwen since it handled your raw zero-shot prompt best
)

# selected model id (name) by the user
active_model_id = model_mapping[selected_model_name]


st.sidebar.caption("Select the backend(where the data is managed)")
backend_mapping = {
    "StateBackend (Ephemeral - In-Memory conversation state)": "StateBackend",
    "StoreBackend (Persistent - Cross-thread LangGraph BaseStore)": "StoreBackend",
    "FilesystemBackend (Host Local Disk - Sandboxed IO paths)": "FilesystemBackend",
}
active_backend = st.sidebar.radio(
    label="Select the backend(where the data is stored and managed)",
    options=list(backend_mapping.keys()),
    index=0
)

active_backend_id = backend_mapping[active_backend]

st.sidebar.subheader("Features")

load_context = st.sidebar.checkbox(
    "Load AGENTS.md context (memory=)",
    value=True,
    help="Load project instructions and memory context."
)

skills = st.sidebar.checkbox(
    "Skills (/skills/)",
    value=True,
    help="Load reusable skills for the agent."
)

subagents = st.sidebar.checkbox(
    "Subagents",
    value=True,
    help="Enable specialized agents."
)

if subagents:
    st.sidebar.markdown(
        """
        - **research-agent** — in-depth research
            with web search (context quarantine)

        - **structured-researcher** — returns
            `ResearchFindings` (summary, confidence,
            sources)
        """
    )

st.sidebar.divider()

system_prompt = st.sidebar.text_area(
    "System prompt",
    placeholder="""
    You are an expert Al assistant and
    researcher. You conduct thorough
    research using your internet_search
    tool when needed, plan multi-step
    work with write_todos, offload bulky
    content to files, use your skills when a
    """,
    height=150,
    help="Define the agent's behavior and instructions."
)


















name = st.text_input("Enter your name")

if st.button("Submit"):
    st.success(f"Hello, {name}!")
st.caption(f"Selected model:{active_model_id}")