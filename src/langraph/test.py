import asyncio 
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv
load_dotenv()

# create llm or agent 
llm = init_chat_model("openai/gpt-oss-20b", model_provider="groq")
memory = MemorySaver()

# state
class State(TypedDict):
    messages: Annotated[list, add_messages]

def llm_tool_node(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# create graph builder
graph_builder = StateGraph(State)

graph_builder.add_node("llm", llm_tool_node)
graph_builder.add_edge(START, "llm")
graph_builder.add_edge("llm", END)

graph = graph_builder.compile(checkpointer=memory)


async def test():
    # 1. Fixed: Changed 'for' to 'async for' to handle the async stream generator
    # 2. Fixed: Wrapped the string input inside a list of HumanMessage objects
    async for updates in graph.astream(
        {"messages": [HumanMessage(content="what is the current rate of fire")]}, 
        {"configurable": {"thread_id": "thread_2"}}, # Best to use strings for thread IDs
        stream_mode="updates"
    ):
        print(updates, flush=True)

# Run the async environment entry point
asyncio.run(test())
