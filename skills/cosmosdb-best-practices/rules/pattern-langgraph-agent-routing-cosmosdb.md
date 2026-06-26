---
title: Persist Active Agent in Cosmos DB for Deterministic Routing
impact: HIGH
impactDescription: eliminates LLM re-classification overhead and prevents routing drift
tags: pattern, cosmos-db, multi-agent, routing, point-read
---

## Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH (eliminates LLM re-classification overhead and prevents routing drift)**

In multi-agent systems, once a user has been routed to a specialist agent, persist the active agent name in Cosmos DB alongside the conversation session. On subsequent messages, perform a point read to retrieve the active agent instead of re-invoking the coordinator LLM to classify intent.

**Incorrect (re-classify every message through the coordinator):**

```python
async def route_message(state, config):
    # BAD: Every user message goes through the coordinator LLM for classification
    # Adds latency and may incorrectly re-route mid-conversation
    response = await coordinator_agent.ainvoke(state)
    return determine_agent_from_response(response)
```

**Correct (async point read for active agent, coordinator only for new conversations):**


```python
import asyncio
from azure.cosmos import CosmosClient

def _read_active_agent_from_db(tenant_id: str, user_id: str, thread_id: str) -> str:
    """Synchronous helper — runs in a thread pool."""
    try:
        item = container.read_item(
```

```python
from azure.cosmos import PartitionKey

def patch_active_agent(tenant_id, user_id, thread_id, new_agent):
    """Partial update — only modifies the activeAgent field (minimal RU cost)."""
    container.patch_item(
        item=thread_id,
        partition_key=[tenant_id, user_id, thread_id],
```
