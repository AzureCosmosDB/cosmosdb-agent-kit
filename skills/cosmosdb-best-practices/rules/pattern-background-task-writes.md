---
title: Use Background Tasks for Non-Blocking Chat History Storage
impact: MEDIUM
impactDescription: reduces API response latency by 50-200ms per request
tags: pattern, fastapi, cosmos-db, background-tasks, latency
---

## Use Background Tasks for Non-Blocking Chat History Storage

**Impact: MEDIUM (reduces API response latency by 50-200ms per request)**

After a LangGraph agent produces a response, storing chat history and debug logs in Cosmos DB is important for the UI but not for the immediate API response. Use FastAPI's `BackgroundTasks` to defer these writes, returning the agent response to the user immediately.

**Incorrect (blocking writes before returning response):**

```python
from fastapi import FastAPI

@app.post("/chat/{session_id}")
async def chat(session_id: str, user_message: str):
    response = await graph.ainvoke(state, config, stream_mode="updates")
    messages = extract_response(response)
```

**Correct (defer writes with BackgroundTasks):**


```python
from fastapi import FastAPI, BackgroundTasks

def process_post_response(messages, session_id, tenant_id, user_id, active_agent):
    """Runs after the response is sent to the client."""
    for msg in messages:
        store_chat_history(msg)
```
