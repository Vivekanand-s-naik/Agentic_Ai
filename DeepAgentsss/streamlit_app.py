from langchain_groq import ChatGroq
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

# subagents constructs
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any
import os
load_dotenv()

model = init_chat_model(
    model="openrouter:minimax/minimax-m3.1-flash:free"
)
model
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
user_id = "user-2"
thread_id = "thread-3"
namespace = ("deepagent_system", user_id)

# utility function to upload skills to store 
def upload_skills_to_store(skills_dir: str):
    base_path = Path(skills_dir)
    if not base_path.exists() or not base_path.is_dir():
        print("Skills directory not found!")
        return

    for p in base_path.rglob("*"):
        if p.is_file() and p.name.lower() == "skill.md":
            skill_folder = p.parent.relative_to(base_path).as_posix()
            virtual_path = f"/skills/{skill_folder}/SKILL.md"

            _store.put(
                namespace=namespace,
                key=virtual_path,
                value=create_file_data(
                    p.read_text(encoding="utf-8")
                )
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
        value=create_file_data(
            path.read_text(encoding="utf-8")
        )
    )
    print(f"Successfully uploaded {file_path} to store as virtual path: '{virtual_key}'")

st.title("🧠☠️ Deepagents Chatbot")

st.write("Planning . Virtual file system . Context engineering (AGENTS.md + memory) . Skills . Subagents (incl. structured output) . Swappable backends . Thread memory via checkpointer")

# Sidebar
st.sidebar.header("Agent COnfigurations")
st.sidebar.caption(f"user-Id : {user_id}")
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
    options=list(backend_mapping.keys())
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
    You are an assistant. For 'research' requests, call Research Subagent with ONLY the topic. Keep replies short.
    """,
    height=150,
    help="Define the agent's behavior and instructions."
)


# load subagents if selected
def web_search(query: str, max_results: int = 1, include_raw_content: bool = False) -> Dict[str, Any]:
    """A Web searching tool that fetches the content from web network"""
    return TavilySearch(
        max_results=min(max_results, 1),
        include_raw_content=False
    ).invoke(input=query)
    
research_subagent = {
    "name": "Research Subagent",
    "description": "Search the web and summarize results in under 100 words. Return only the summary, no raw results.",
    "system_prompt": "You are a great Research Assistant",
    "tools": [web_search],
    "model": model
}
subagents_list = [research_subagent]

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
                namespace= lambda _rt:namespace,
                store=_store
            )
        case "FilesystemBackend":
            backend = FilesystemBackend(
                root_dir=".",
                virtual_mode=True
            )
    groq_model = ChatGroq(
        model=curr_model_id,
        max_tokens=400
    )
    agent = create_deep_agent(
        model= groq_model, #f"groq:{curr_model_id}",
        backend=backend,
        subagents= subagents_list if use_subagents else None,
        skills=["/skills/"] if load_skills else None,
        memory=["/projects/AGENTS.md"] if load_agent_contxt else None,
        system_prompt=system_prompt,
        checkpointer=_checkpointer,
    
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


# Rendering helpers 

def extract_text(content) -> str:
    """Extract readable text from a message."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)

    return str(content)


def render_steps(messages):
    """Render planning, web searches, subagents and tool results."""

    for msg in messages:
        msg_type = getattr(msg, "type", "")

        # Tool calls made by the assistant
        if msg_type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                name = tc["name"]
                args = tc.get("args", {})

                if name == "write_todos":
                    with st.expander("📋 Planning — write_todos"):
                        for todo in args.get("todos", []):
                            status = todo.get("status", "pending")
                            icon = {
                                "pending": "⬜",
                                "in_progress": "🔄",
                                "completed": "✅",
                            }.get(status, "⬜")

                            description = (
                                todo.get("content", str(todo))
                                if isinstance(todo, dict)
                                else str(todo)
                            )
                            st.markdown(f"{icon} {description}")

                elif name in ("web_search", "internet_search"):
                    query_text = args.get("query", str(args))

                    with st.expander(f"🔎 Web search — {query_text}"):
                        st.json(args)

                elif name == "task":
                    with st.expander("🤖 Subagent — task"):
                        st.json(args)

                elif name in (
                    "write_file", "edit_file", "read_file",
                    "ls", "glob", "grep"
                ):
                    path = args.get("file_path") or args.get("path", "")

                    with st.expander(f"📁 File system — {name} {path}"):
                        st.json(args)

                else:
                    with st.expander(f"🛠️ Tool — {name}"):
                        st.json(args)

        # Results returned by tools
        elif msg_type == "tool":
            content = extract_text(msg.content)

            if len(content) > 2000:
                content = content[:2000] + " …(truncated)"

            with st.expander(
                f"↩️ Result — {getattr(msg, 'name', 'tool')}"
            ):
                st.code(content)


# Messaging logic 

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("steps"):
            render_steps(msg["steps"])

        st.markdown(msg["content"])


query = st.chat_input(
    "Ask me anything — research, code, AWS, LangGraph..."
)

if query:
    # Save and display the user message
    st.session_state.messages.append({
        "role": "user",
        "content": query,
    })

    with st.chat_message("user"):
        st.markdown(query)

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        }
    }

    with st.chat_message("assistant"):
        with st.spinner("🧠 Planning, researching and delegating..."):
            try:
                result = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": query,
                            }
                        ],
                        "skills_metadata": None,
                    },
                    config=config,
                )

                all_msgs = result["messages"]

                # Find the latest user message for this turn
                turn_start = max(
                    (
                        i for i, msg in enumerate(all_msgs)
                        if getattr(msg, "type", "") == "human"
                    ),
                    default=-1,
                )

                new_msgs = all_msgs[turn_start + 1:]

                # Display planning, tool calls and their results
                render_steps(new_msgs)

                # Extract the final assistant response
                answer = next(
                    (
                        extract_text(msg.content)
                        for msg in reversed(new_msgs)
                        if getattr(msg, "type", "") == "ai"
                        and not getattr(msg, "tool_calls", [])
                        and extract_text(msg.content).strip()
                    ),
                    "No final text response was generated.",
                )

                # Render the final answer as Markdown
                st.markdown(answer)

                # Save the answer and intermediate steps for replay
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "steps": new_msgs,
                })

            except Exception as e:
                st.error(f"Agent error: {e}")


# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Re-render past conversation history logs every time the page scripts reload
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])


# query = st.text_input("Ask me anything - research, code, AWS, LangGraph ...")
# def stream_agent_response(agent, query, config):
#     for chunk in agent.stream(
#         {"messages": [{"role": "user", "content": query}], "skills_metadata": None},
#         config=config,
#         stream_mode="messages",
#         subgraphs=True,
#         version="v2",
#     ):
#         if isinstance(chunk, dict) and chunk.get("type") == "messages":
#             token, _ = chunk["data"]
#             if hasattr(token, "content") and token.content:
#                 yield token.content
#         elif hasattr(chunk, "content") and chunk.content:
#             yield chunk.content


# if st.button("Submit") and query:
#     st.session_state.messages.append({"role": "user", "content": query})
#     config = {"configurable": {"thread_id": "11", "user_id": user_id}}
    
#     with st.chat_message("assistant"):
#         full_response = st.write_stream(stream_agent_response(agent, query, config))
    
#     st.session_state.messages.append({"role": "assistant", "content": full_response})
#     st.rerun()
# if st.button("Submit"):
#     if query:
#         # save human message
#         st.session_state.messages.append({"role": "user", "content": query})
#         st.success(f"Thinking")
#         result = agent.invoke({
#             "messages": [
#                 {
#                 "role": "user", 
#                 "content": query
#                 }
#             ],
#             "skills_metadata": None,
#         },
#         config={"configurable": {
#             "thread_id": "11",
#             "user_id": user_id
#             }}
#         )
#         output_text = result["messages"][-1].content
#         st.session_state.messages.append({"role": "assistant", "content": output_text})
#         st.rerun()
st.caption(f"Selected model:{active_model_id}")