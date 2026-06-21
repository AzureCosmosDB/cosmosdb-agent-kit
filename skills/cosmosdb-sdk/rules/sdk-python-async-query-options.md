---
title: Use Python async query options that match your azure-cosmos version
impact: HIGH
impactDescription: prevents aiohttp runtime errors from leaking unsupported kwargs through azure.cosmos.aio query calls
tags: sdk, python, async, query, aio, fastapi
---

## Use Python Async Query Options That Match Your azure-cosmos Version

**Impact: HIGH (prevents runtime 500s in Python/FastAPI async query paths)**

The synchronous `azure.cosmos.ContainerProxy.query_items` API and the asynchronous `azure.cosmos.aio.ContainerProxy.query_items` API do not expose the same named query options in all `azure-cosmos` versions. In particular, `azure-cosmos==4.9.0` supports `enable_cross_partition_query` on the sync API but not on the async API. Passing sync-only kwargs to the async pipeline can leak them down to `aiohttp` and crash requests.

Prefer partition-scoped async queries with `partition_key=`. For cross-partition async queries, either omit the legacy sync-style `enable_cross_partition_query=True` flag on older SDK pins or upgrade to a current `azure-cosmos` version whose async API/docs support the option.

**Incorrect (sync-style kwarg copied into an older async SDK):**

```python
from azure.cosmos.aio import CosmosClient

async def find_session(container, session_id: str):
    items = container.query_items(
        query="SELECT * FROM c WHERE c.sessionId = @sid",
        parameters=[{"name": "@sid", "value": session_id}],
        enable_cross_partition_query=True,  # BAD on azure-cosmos 4.9 aio
    )
    return [item async for item in items]
```

This can fail at runtime with:

```text
TypeError: ClientSession._request() got an unexpected keyword argument 'enable_cross_partition_query'
```

**Correct (single-partition async query):**

```python
async def list_messages(messages_container, session_id: str):
    items = messages_container.query_items(
        query="SELECT * FROM c WHERE c.sessionId = @sid ORDER BY c.createdAt",
        parameters=[{"name": "@sid", "value": session_id}],
        partition_key=session_id,
    )
    return [item async for item in items]
```

**Correct (cross-partition async query compatible with older pins):**

```python
async def find_session_by_id(sessions_container, session_id: str):
    # No partition key is known here, so the query fans out. On older async SDK pins,
    # omit enable_cross_partition_query=True instead of passing a sync-only kwarg.
    items = sessions_container.query_items(
        query="SELECT * FROM c WHERE c.sessionId = @sid",
        parameters=[{"name": "@sid", "value": session_id}],
    )
    results = [item async for item in items]
    return results[0] if results else None
```

**Correct (upgrade if you require current async query options):**

```text
azure-cosmos>=4.14.0
aiohttp>=3.9.0
```

Then verify the exact async method signature and docs for the version you deploy before using newer kwargs.

**Key points:**

- Do not blindly copy sync `query_items` kwargs into `azure.cosmos.aio` code.
- Use `partition_key=` for async single-partition queries whenever possible.
- If a query must fan out and you are pinned to `azure-cosmos==4.9.0`, omit `enable_cross_partition_query=True` in async code.
- If you see `ClientSession._request() got an unexpected keyword argument ...`, inspect async Cosmos SDK kwargs first.

Reference: [Azure Cosmos DB async Python ContainerProxy API](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.aio.containerproxy)
