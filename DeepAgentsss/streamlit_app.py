from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
import streamlit as st

import psycopg
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from deepagents import create_deep_agent
from deepagents.backends import StateBackend, StoreBackend, FilesystemBackend
from deepagents.backends.utils import create_file_data

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from pathlib import Path
from typing import Dict, Any
import os

load_dotenv()

model = init_chat_model(
    model="openrouter:minimax/minimax-m3.1-flash:free"
)


@st.cache_resource
def load_db():
    db_uri = os.getenv("DB_URI")
    try:
        _pool = ConnectionPool(
            conninfo=db_uri,
            min_size=1,
            max_size=20,
            timeout=5.0,
            kwargs={"autocommit": True},
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

st.sidebar.header("Agent Configurations")

user_id = st.sidebar.text_input(
    "User ID",
    value="user-2",
    key="user_id_input",
).strip()

thread_id = st.sidebar.text_input(
    "Thread ID",
    value="thread-5",
    key="thread_id_input",
).strip()

if not user_id or not thread_id:
    st.sidebar.warning("User ID and Thread ID cannot be empty.")
    st.stop()

namespace = ("deepagent_system", user_id)

st.sidebar.caption(f"User ID: {user_id}")
st.sidebar.caption(f"Thread ID: {thread_id}")


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
                value=create_file_data(p.read_text(encoding="utf-8")),
            )
            print(f"Uploaded {virtual_path} directly to PostgresStore database.")


def upload_context_file_to_store(file_path: str, virtual_key: str):
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: Local file {file_path} not found!")
        return

    _store.put(
        namespace=namespace,
        key=virtual_key,
        value=create_file_data(path.read_text(encoding="utf-8")),
    )
    print(
        f"Successfully uploaded {file_path} to store as virtual path: '{virtual_key}'"
    )


def delete_user_conversations(user_id: str):
    deleted_threads = 0
    deleted_store_keys = 0
    errors = []

    try:
        with _pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT thread_id
                    FROM checkpoints
                    WHERE metadata->'configurable'->>'user_id' = %s
                    """,
                    (user_id,),
                )
                thread_ids = [row[0] for row in cur.fetchall()]

                if not thread_ids:
                    cur.execute(
                        """
                        SELECT DISTINCT thread_id
                        FROM checkpoints
                        WHERE checkpoint->'channel_values'->>'user_id' = %s
                        """,
                        (user_id,),
                    )
                    thread_ids = [row[0] for row in cur.fetchall()]

                for tid in thread_ids:
                    cur.execute(
                        "DELETE FROM checkpoint_writes WHERE thread_id = %s;",
                        (tid,),
                    )
                    cur.execute(
                        "SELECT to_regclass('public.checkpoint_blobs') IS NOT NULL;"
                    )
                    if cur.fetchone()[0]:
                        cur.execute(
                            "DELETE FROM checkpoint_blobs WHERE thread_id = %s;",
                            (tid,),
                        )
                    cur.execute(
                        "DELETE FROM checkpoints WHERE thread_id = %s;",
                        (tid,),
                    )
                    deleted_threads += 1
    except Exception as e:
        errors.append(f"checkpoint cleanup: {e}")

    try:
        with _pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM store WHERE prefix LIKE %s;",
                    (f"deepagent_system.{user_id}%",),
                )
                deleted_store_keys = cur.rowcount
    except Exception as e:
        errors.append(f"store cleanup: {e}")

    if "messages_by_user" in st.session_state:
        st.session_state.messages_by_user[user_id] = []
    st.session_state.messages = []

    return {
        "threads_deleted": deleted_threads,
        "store_keys_deleted": deleted_store_keys,
        "errors": errors,
    }


def _handle_delete_click(user_id_to_delete: str):
    result = delete_user_conversations(user_id_to_delete)
    st.session_state.delete_result = result
    st.session_state.confirm_delete_conversations = False


st.title("🧠☠️ Deepagents Chatbot")

st.write(
    "Planning . Virtual file system . Context engineering (AGENTS.md + memory) . "
    "Skills . Subagents (incl. structured output) . Swappable backends . "
    "Thread memory via checkpointer"
)

st.sidebar.header("Agent Configurations")
st.sidebar.caption(f"user-Id : {user_id}")

model_mapping = {
    "Alibaba Qwen 3.8 27B (Fast & Multimodal)": "qwen/qwen3.8-27b",
    "OpenAI GPT-OSS 20B (Standard Reasoning)": "openai/gpt-oss-20b",
    "OpenAI GPT-OSS 120B (High Reasoning)": "openai/gpt-oss-120b",
}

selected_model_name = st.sidebar.selectbox(
    label="Select Active Groq Model:",
    options=list(model_mapping.keys()),
    index=0,
)

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
)

active_backend_id = backend_mapping[active_backend]

st.sidebar.subheader("Features")

load_context = st.sidebar.checkbox(
    "Load AGENTS.md context (memory=)",
    value=True,
    help="Load project instructions and memory context.",
)
if load_context:
    upload_context_file_to_store(
        file_path="projects/AGENTS.md",
        virtual_key="/projects/AGENTS.md",
    )

skills = st.sidebar.checkbox(
    "Skills (/skills/)",
    value=True,
    help="Load reusable skills for the agent.",
)
if skills:
    upload_skills_to_store("skills")

subagents = st.sidebar.checkbox(
    "Subagents",
    value=True,
    help="Enable specialized agents.",
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

if "confirm_delete_conversations" not in st.session_state:
    st.session_state.confirm_delete_conversations = False

confirm_delete = st.sidebar.checkbox(
    f"I understand this deletes everything for '{user_id}'",
    key="confirm_delete_conversations",
)

st.sidebar.button(
    "🗑️ Delete all conversations for this user",
    disabled=not confirm_delete,
    use_container_width=True,
    on_click=_handle_delete_click,
    args=(user_id,),
)

if st.session_state.get("delete_result"):
    _res = st.session_state.delete_result
    if _res["errors"]:
        st.sidebar.error(
            "Partially deleted. Errors:\n- " + "\n- ".join(_res["errors"])
        )
    else:
        st.sidebar.success(
            f"Deleted {_res['threads_deleted']} thread(s) and "
            f"{_res['store_keys_deleted']} store entries for '{user_id}'."
        )
    st.session_state.delete_result = None

st.sidebar.divider()

system_prompt = st.sidebar.text_area(
    "System prompt",
    placeholder="""
    You are an assistant. For 'research' requests, call Research Subagent with ONLY the topic. Keep replies short.
    """,
    height=150,
    help="Define the agent's behavior and instructions.",
)


def web_search(
    query: str, max_results: int = 1, include_raw_content: bool = False
) -> Dict[str, Any]:
    """Search the web for a given query and return the Tavily results.

    Args:
        query: The search query to send to the web search engine.
        max_results: Maximum number of results to return (capped at 1).
        include_raw_content: Whether to include raw page content in results.
    """
    return TavilySearch(
        max_results=min(max_results, 1),
        include_raw_content=False,
    ).invoke(input=query)


research_subagent = {
    "name": "Research Subagent",
    "description": (
        "Search the web and summarize results in under 100 words. "
        "Return only the summary, no raw results."
    ),
    "system_prompt": "You are a great Research Assistant",
    "tools": [web_search],
    "model": model,
}
subagents_list = [research_subagent]


def get_deepagent(
    curr_backend_id: str,
    curr_model_id: str,
    load_skills: bool,
    load_agent_contxt: bool,
    use_subagents: bool,
    system_prompt: str,
):
    backend = None
    match curr_backend_id:
        case "StateBackend":
            backend = StateBackend()
        case "StoreBackend":
            backend = StoreBackend(
                namespace=lambda _rt: namespace,
                store=_store,
            )
        case "FilesystemBackend":
            backend = FilesystemBackend(
                root_dir=".",
                virtual_mode=True,
            )

    groq_model = ChatGroq(
        model=curr_model_id,
        max_tokens=400,
    )

    agent = create_deep_agent(
        model=groq_model,
        backend=backend,
        subagents=subagents_list if use_subagents else None,
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
    system_prompt,
)


def extract_text(content) -> str:
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
    for msg in messages:
        msg_type = getattr(msg, "type", "")

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
                    "write_file",
                    "edit_file",
                    "read_file",
                    "ls",
                    "glob",
                    "grep",
                ):
                    path = args.get("file_path") or args.get("path", "")
                    with st.expander(f"📁 File system — {name} {path}"):
                        st.json(args)

                else:
                    with st.expander(f"🛠️ Tool — {name}"):
                        st.json(args)

        elif msg_type == "tool":
            content = extract_text(msg.content)
            if len(content) > 2000:
                content = content[:2000] + " …(truncated)"

            with st.expander(f"↩️ Result — {getattr(msg, 'name', 'tool')}"):
                st.code(content)


if "messages_by_user" not in st.session_state:
    st.session_state.messages_by_user = {}

if user_id not in st.session_state.messages_by_user:
    st.session_state.messages_by_user[user_id] = []

st.session_state.messages = st.session_state.messages_by_user[user_id]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("steps"):
            render_steps(msg["steps"])
        st.markdown(msg["content"])


query = st.chat_input(
    "Ask me anything — research, code, AWS, LangGraph..."
)

if query:
    st.session_state.messages.append({"role": "user", "content": query})

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
                            {"role": "user", "content": query}
                        ],
                        "skills_metadata": None,
                    },
                    config=config,
                )

                all_msgs = result["messages"]

                turn_start = max(
                    (
                        i
                        for i, msg in enumerate(all_msgs)
                        if getattr(msg, "type", "") == "human"
                    ),
                    default=-1,
                )

                new_msgs = all_msgs[turn_start + 1:]

                render_steps(new_msgs)

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

                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "steps": new_msgs,
                    }
                )

            except Exception as e:
                st.error(f"Agent error: {e}")


st.caption(f"Selected model:{active_model_id}")