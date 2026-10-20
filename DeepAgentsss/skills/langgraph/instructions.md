# LangGraph Instructions

## Building a graph
- Define state as TypedDict with annotated reducers
- Add nodes as functions receiving state, returning partial state
- Use `add_conditional_edges` for branching on state
- Compile with checkpointer for persistence: `graph.compile(checkpointer=...)`

## Patterns
- ReAct agent: tool node + conditional edge to tools
- Human-in-the-loop: `interrupt_before=["node"]`, resume with `Command`
- Subgraphs for modularity; pass parent state explicitly
- Streaming: `graph.stream(..., stream_mode="updates")`

## Debugging
- Use LangSmith tracing; add `run_name`
- Visualize with `graph.get_graph().draw_mermaid()`
