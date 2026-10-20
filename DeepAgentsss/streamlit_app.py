from langchain_tavily import TavilySearch
import streamlit as st

# Database & Storage constructs
import psycopg
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

# Deepagent constructs
from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend, FilesystemBackend
from deepagents.backends.utils import create_file_data


from dotenv import load_dotenv
from pathlib import Path
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
_pool, _store, _checkpointer = load_db()

# utility function to upload skills to store 
@st.cache_resource
def upload_skills_to_store(skills_dir: str):
    base_path = Path(skills_dir)
    if not base_path.exists() or not base_path.is_dir():
        print("Skills directory not found!")
        return

    for p in base_path.rglob("*"):
        if p.is_file() and p.name.lower() == "skill.md":
            skill_folder = p.parent.relative_to(base_path).as_posix()
            virtual_path = f"/skills/{skill_folder}/SKILL.md"
            
            # CRITICAL: StoreBackend expects values to be dictionaries containing JSON-serializable keys
            # Instead of create_file_data(), put plain text contents into the DB
            _store.put(
                namespace=namespace,
                key=virtual_path,
                value={"text": p.read_text("utf-8")} 
            )
            print(f"Uploaded {virtual_path} directly to PostgresStore database.")

# utility function to upload agents.md file (memory)
def upload_context_file_to_store(file_path: str, virtual_key: str):
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: Local file {file_path} not found!")
        return

    _store.put(
        namespace=namespace,
        key=virtual_key,
        value={"text": path.read_text("utf-8")}
    )
    print(f"Successfully uploaded {file_path} to store as virtual path: '{virtual_key}'")

st.title("🧠☠️ Deepagents Chatbot")
user_id = "1"
st.write("Planning . Virtual file system . Context engineering (AGENTS.md + memory) . Skills . Subagents (incl. structured output) . Swappable backends . Thread memory via checkpointer")

# Sidebar
st.sidebar.header("Agent COnfigurations")
st.sidebar.caption(f"user-Id : {user_id}")
model_mapping = {
    "Alibaba Qwen 3.8 27B (Fast & Multimodal)": "groq:qwen/qwen3.8-27b",
    "OpenAI GPT-OSS 20B (Standard Reasoning)": "groq:openai/gpt-oss-20b",
    "OpenAI GPT-OSS 120B (High Reasoning)": "groq:openai/gpt-oss-120b"
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
if load_context:
    upload_context_file_to_store(
        file_path="projects/AGENTS.md", 
        virtual_key="/projects/AGENTS.md"
    )

skills = st.sidebar.checkbox(
    "Skills (/skills/)",
    value=True,
    help="Load reusable skills for the agent."
)
if skills:
    upload_skills_to_store("skills")

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

# create deepagent
def get_deepagent(
    curr_backend_id: str, 
    curr_model_id: str, 
    load_skills: bool, 
    load_agent_contxt: bool, 
    use_subagents: bool, 
    system_prompt: str
    ):
    # initialize backend
    backend = None
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


query = st.text_input("Ask me anything - research, code, AWS, LangGraph ...")
if st.button("Submit"):
    st.success(f"Thinking")
    result = agent.invoke({
        "messages": [
            {
            "role": "user", 
            "content": query
            }
        ]
    },
    config={"configurable": {
        "thread_id": "10",
        "user_id": user_id
        }}
    )
    st.write(result["messages"][-1].content)
st.caption(f"Selected model:{active_model_id}")