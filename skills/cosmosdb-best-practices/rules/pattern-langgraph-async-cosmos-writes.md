---
title: Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions
impact: HIGH
impactDescription: prevents event loop blocking during Cosmos DB upserts in async node functions
tags: pattern, langgraph, async, cosmos-db, writes, multi-agent
---

## Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions

**Impact: HIGH (prevents event loop blocking during Cosmos DB upserts in async node functions)**

When saving the active agent after a transfer (inside a LangGraph node function), using the sync Cosmos DB SDK also blocks the event loop. Node functions in LangGraph run as coroutines.

**Incorrect (synchronous upsert blocks the event loop inside an async node):**

```python
async def call_agent(state, config):
    response = await agent.ainvoke(state)
    # BAD: Blocks the event loop during upsert
    container.upsert_item({
        "id": thread_id,
        "sessionId": thread_id,
```

**Correct (non-blocking write with asyncio.to_thread):**


```python
import asyncio
import logging

logger = logging.getLogger(__name__)

async def save_active_agent_to_db_async(
```
