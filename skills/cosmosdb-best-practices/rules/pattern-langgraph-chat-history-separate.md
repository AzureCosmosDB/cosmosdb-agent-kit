---
title: Store Chat History Separately from LangGraph Checkpoints
impact: MEDIUM
impactDescription: enables efficient message retrieval and agent attribution
tags: pattern, cosmos-db, chat-history, checkpointing, multi-agent
---

## Store Chat History Separately from LangGraph Checkpoints

**Impact: MEDIUM (enables efficient message retrieval and agent attribution)**

LangGraph's checkpointer (CosmosDBSaver) stores full graph state for resumption, but it is not optimized for retrieving displayable chat history. Checkpoint data contains internal graph metadata, tool messages, system messages, and duplicate entries from each node execution.

**Incorrect (reading chat history from the checkpointer store):**

```python
@app.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str):
    config = {"configurable": {"thread_id": session_id, "checkpoint_ns": ""}}
    # BAD: Checkpointer stores ALL graph state — tool messages, system messages,
    # intermediate states, duplicates from each node. Expensive to scan and filter.
    checkpoints = [cp async for cp in checkpointer.alist(config)]
```

**Correct (store displayable history in a dedicated container):**


```python
from azure.cosmos import CosmosClient

# Dedicated container with partition key /sessionId for efficient retrieval
history_container = database.get_container_client("ChatHistory")

def store_chat_message(session_id: str, tenant_id: str, user_id: str, 
```
