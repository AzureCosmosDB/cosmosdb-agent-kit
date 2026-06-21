---
title: Map Cosmos DB documents to FastAPI response DTOs
impact: HIGH
impactDescription: prevents strict response_model failures and avoids leaking system fields, storage-only fields, or raw embeddings
tags: pattern, fastapi, response-model, dto, api-contract, rag
---

## Map Cosmos DB Documents to FastAPI Response DTOs

**Impact: HIGH (prevents API 500s and keeps storage internals out of public responses)**

Cosmos DB documents are persistence records, not public API response contracts. FastAPI `response_model` validation checks the returned value against the declared response shape. If the returned value is invalid, FastAPI treats that as an application bug and returns a server error.

Do not return raw Cosmos DB SDK documents from endpoints with a strict `response_model` or an exact API contract. Cosmos items include system fields like `_rid`, `_self`, `_etag`, `_attachments`, and `_ts`, and application storage documents often include internal fields like `type`, `schemaVersion`, synthetic ids, denormalized helper fields, or raw `embedding` vectors. Map the storage document to an explicit DTO/dict before returning it.

**Incorrect (raw Cosmos document returned through response_model):**

```python
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

app = FastAPI()

class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sessionId: str
    userId: str
    title: str
    createdAt: str

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, user_id: str):
    doc = sessions_container.read_item(item=session_id, partition_key=user_id)
    return doc  # BAD: may include id, type, _etag, _rid, _ts, etc.
```

**Correct (map to the API contract):**

```python
def to_session_response(doc: dict) -> dict:
    return {
        "sessionId": doc["sessionId"],
        "userId": doc["userId"],
        "title": doc.get("title", ""),
        "createdAt": doc["createdAt"],
    }

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, user_id: str):
    doc = sessions_container.read_item(item=session_id, partition_key=user_id)
    return to_session_response(doc)
```

**Correct (project and map vector-search results):**

```python
def to_search_result(item: dict) -> dict:
    return {
        "documentId": item.get("documentId", item["id"]),
        "content": item["content"],
        "category": item["category"],
        "metadata": item.get("metadata", {}),
        "score": item["score"],
    }

safe_limit = max(1, min(int(limit), 50))
query = f"""
SELECT TOP {safe_limit}
    c.documentId,
    c.content,
    c.category,
    c.metadata,
    VectorDistance(c.embedding, @embedding) AS score
FROM c
WHERE c.category = @category
ORDER BY VectorDistance(c.embedding, @embedding)
"""

# category is the partition key, so scope the read to one logical
# partition instead of fanning out with enable_cross_partition_query.
items = documents_container.query_items(
    query=query,
    parameters=[
        {"name": "@embedding", "value": embedding},
        {"name": "@category", "value": category},
    ],
    partition_key=category,
)
return {"results": [to_search_result(item) for item in items]}
```

**Key points:**

- Keep Cosmos system fields internal unless the API contract explicitly asks for them.
- Keep raw embeddings internal unless building an embedding export endpoint.
- Prefer SQL projections for query endpoints so extra fields do not leave the data layer.
- Do not fix contract drift by changing Pydantic models to `extra="allow"`; map the storage document to the public contract instead.

References: [FastAPI response model](https://fastapi.tiangolo.com/tutorial/response-model/) | [Azure Cosmos DB Python ContainerProxy API](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.containerproxy)
