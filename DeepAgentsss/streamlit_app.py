from langchain_tavily import TavilySearch
import streamlit as st
import psycopg
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend, FilesystemBackend
from deepagents.backends.utils import create_file_data
from dotenv import load_dotenv
from typing import Dict, Any
import os
load_dotenv()

@st.cache_resource
def load_db():
    # function to get the checkpointer, store and pool
    db_uri = os.getenv("DB_URI")
    try:
        _pool = ConnectionPool(
            conninfo=db_uri,
            min_size=1,
            max_size=20,
            timeout=5.0, 
            kwargs={"autocommit": True}
        )
        _store = PostgresStore(_pool)
        _checkpointer = PostgresSaver(_pool)
        _store.setup()
        _checkpointer.setup()
        return _pool, _store, _checkpointer
    except Exception as e:
        st.error(f" Initialization Error: {e}")
        st.stop()


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


# load subagents if selected
@st.cache_resource
def web_search(query: str, max_results: int = 1, include_raw_content: bool = False) -> Dict[str, Any]:
    """A Web searching tool that fetches the content from web network"""
    return TavilySearch(
        max_results=min(max_results, 1),
        include_raw_content=False
    ).invoke(input=query)
    
research_subagent = {
    "name": "Research Subagent",
    "description": "A subagents designed to research and provide results for a query",
    "system_prompt": "You are a great Research Assistant",
    "tools": [web_search],
    "model": "groq:Openai/gpt-oss-20b"
}
subagents = [research_subagent]

# Main agent logic and functionality
_pool, _store, _checkpointer = load_db()

# create deepagent
@st.cache_resource
def get_deepagent(
    curr_backend_id: str, 
    curr_model_id: str, 
    load_skills: bool, 
    load_agent_contxt: bool, 
    use_subagents: bool, 
    system_prompt: str
    ):
    # initialize backend
    match curr_backend_id:
        case "StateBackend":
            backend = StateBackend()
        case "StoreBackend":
            backend = StoreBackend(
                namespace= lambda rt: ("deepagent_system", rt.context.get("user_id", "default_user")),
                store=_store
            )
        case "FileSystemBackend":
            backend = FilesystemBackend(
                root_dir=".",
                virtual_mode=True
            )
    
    agent = create_deep_agent(
        model=curr_model_id,
        backend=backend,
        subagents= subagents if use_subagents else None,
        skills=["/skills/"] if load_skills else None,
        memory=["/projects/AGENTS.md"] if load_agent_contxt else None,
        system_prompt=system_prompt,
        checkpointer=_checkpointer
    )
    return agent
    

agent = get_deepagent(
    active_backend_id,
    active_model_id,
    skills,
    load_context,
    subagents,
    system_prompt
)












name = st.text_input("Ask me anything - research, code, AWS, LangGraph ...")

if st.button("Submit"):
    st.success(f"Hello, {name}!")
st.caption(f"Selected model:{active_model_id}")