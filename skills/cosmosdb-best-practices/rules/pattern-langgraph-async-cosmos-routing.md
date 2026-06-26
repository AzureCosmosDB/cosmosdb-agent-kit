---
title: Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions
impact: CRITICAL
impactDescription: prevents event loop blocking that causes all concurrent requests to hang
tags: pattern, langgraph, async, cosmos-db, routing, multi-agent
---

## Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions

**Impact: CRITICAL (prevents event loop blocking that causes all concurrent requests to hang)**

LangGraph's `add_conditional_edges` routing function runs inside the async event loop. If the routing function calls `DefaultAzureCredential` or `container.read_item()` synchronously, it blocks the entire event loop — causing all concurrent requests to hang and potentially triggering timeouts.

**Incorrect (synchronous Cosmos DB call blocks the event loop):**

```python
from azure.cosmos import CosmosClient

def get_active_agent(state, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    # BAD: Blocks the event loop when called from LangGraph's async runtime
    item = container.read_item(item=thread_id, partition_key=thread_id)
```

**Correct (async wrapper with timeout and fallback):**


```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    container = get_sync_container("ChatSessions")
```
