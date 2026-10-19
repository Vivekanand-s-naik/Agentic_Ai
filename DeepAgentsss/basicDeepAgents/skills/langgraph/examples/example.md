# Example: Minimal LangGraph

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict):
    messages: Annotated[list, lambda a, b: a + b]

def node(state: State) -> dict:
    return {"messages": ["hello"]}

g = StateGraph(State)
g.add_node("n", node)
g.set_entry_point("n")
g.add_edge("n", END)
app = g.compile(checkpointer=MemorySaver())
print(app.invoke({"messages": []}, config={"configurable": {"thread_id": "1"}}))
```
