# LangGraph Best Practices

- Keep state minimal; avoid storing large blobs in state
- Use reducers for list/accumulating fields
- Idempotent nodes; handle retries gracefully
- Always set thread_id in config for checkpointed runs
- Add max iterations to prevent infinite loops
- Log node entry/exit; use LangSmith
- Test graphs with fixed inputs and assert final state
