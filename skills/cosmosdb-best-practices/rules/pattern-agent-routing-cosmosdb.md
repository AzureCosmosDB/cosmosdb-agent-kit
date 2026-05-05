---
title: Persist Active Agent in Cosmos DB for Deterministic Routing
impact: HIGH
impactDescription: eliminates LLM re-classification overhead and prevents routing drift
tags: pattern, cosmos-db, multi-agent, routing, point-read
---

## Persist Active Agent in Cosmos DB for Deterministic Routing

**Impact: HIGH (eliminates LLM re-classification overhead and prevents routing drift)**

In multi-agent systems, once a user has been routed to a specialist agent, persist the active agent name in Cosmos DB alongside the conversation session. On subsequent messages, perform a point read to retrieve the active agent instead of re-invoking the coordinator LLM to classify intent. This is faster (single-digit millisecond point read vs. hundreds of milliseconds for LLM inference), deterministic, and avoids mid-conversation routing flip-flops.

**Incorrect (re-classify every message through the coordinator):**

```python
async def route_message(state, config):
    # BAD: Every user message goes through the coordinator LLM for classification
    # Adds latency and may incorrectly re-route mid-conversation
    response = await coordinator_agent.ainvoke(state)
    return determine_agent_from_response(response)
```

**Correct (point read for active agent, coordinator only for new conversations):**

```python
from azure.cosmos import CosmosClient

def get_active_agent(state, config) -> str:
    thread_id = config["configurable"]["thread_id"]
    user_id = config["configurable"]["userId"]
    tenant_id = config["configurable"]["tenantId"]

    # O(1) point read — single-digit ms latency, 1 RU cost
    try:
        item = container.read_item(
            item=thread_id,
            partition_key=[tenant_id, user_id, thread_id]
        )
        active_agent = item.get("activeAgent", "unknown")
    except Exception:
        active_agent = "unknown"

    # If an agent is already assigned, route directly — skip coordinator
    if active_agent not in [None, "unknown", "coordinator"]:
        return active_agent

    # Only invoke coordinator for new/unrouted conversations
    return "coordinator"
```

**Updating the active agent:** When a transfer tool is called (e.g., `transfer_to_sales_agent`), patch the Cosmos DB document with the new active agent name:

```python
from azure.cosmos import PartitionKey

def patch_active_agent(tenant_id, user_id, thread_id, new_agent):
    """Partial update — only modifies the activeAgent field (minimal RU cost)."""
    container.patch_item(
        item=thread_id,
        partition_key=[tenant_id, user_id, thread_id],
        patch_operations=[
            {"op": "set", "path": "/activeAgent", "value": new_agent}
        ]
    )
```

**Key design points:**
1. Use hierarchical partition key (`/tenantId`, `/userId`, `/sessionId`) for efficient multi-tenant lookups
2. The point read costs 1 RU regardless of document size
3. Use patch operations (not full replace) to update the active agent — costs fewer RUs
4. Fall back to the coordinator only when `activeAgent` is `null` or `"unknown"`

Reference: [Azure Cosmos DB point reads](https://learn.microsoft.com/azure/cosmos-db/nosql/how-to-read-item)
