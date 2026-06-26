---
title: Resume LangGraph from Checkpoint After Interrupt
impact: HIGH
impactDescription: enables multi-turn conversations with persistent state
tags: pattern, langgraph, fastapi, checkpointing, resume
---

## Resume LangGraph from Checkpoint After Interrupt

**Impact: HIGH (enables multi-turn conversations with persistent state)**

When a LangGraph graph pauses at an `interrupt()` node, the next user message must resume from the last checkpoint rather than starting fresh. Retrieve the last checkpoint, append the new user message, inject `langgraph_triggers` to signal which node to resume, and call `ainvoke` with `stream_mode="updates"`.

**Incorrect (always starts a fresh graph invocation):**

```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id}}
    # BAD: Always starts from scratch — ignores prior conversation state
    state = {"messages": [{"role": "user", "content": user_message}]}
    response = await graph.ainvoke(state, config, stream_mode="updates")
```

**Correct (resume from last checkpoint when one exists):**


```python
@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}

    # Check for existing checkpoint (prior conversation state)
    checkpoints = [cp async for cp in checkpointer.alist(config)]
```
