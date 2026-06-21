---
title: Let Python write methods derive the partition key from the item body
impact: HIGH
impactDescription: prevents runtime 500s from passing unsupported partition_key kwargs to Python create/upsert/replace writes
tags: sdk, python, partition-key, writes, fastapi
---

## Let Python Write Methods Derive the Partition Key from the Item Body

**Impact: HIGH (prevents runtime failures in Python create/upsert/replace paths)**

In the Azure Cosmos DB Python SDK, item write methods such as `create_item`, `upsert_item`, and `replace_item` derive the partition key from the item body. Do not pass `partition_key=` to these write methods. If the document is missing the partition-key field, fix the document shape.

Use explicit `partition_key=` for operations where the SDK requires or accepts it: point reads, deletes, patches, and partition-scoped queries.

**Incorrect (passing partition_key to Python write methods):**

```python
# BAD: create_item/upsert_item/replace_item do not use partition_key= for writes.
session_doc = {
    "id": session_id,
    "sessionId": session_id,
    "userId": user_id,
    "title": title,
}
sessions_container.create_item(body=session_doc, partition_key=user_id)

document_doc = {
    "id": document_id,
    "documentId": document_id,
    "category": category,
    "content": content,
    "embedding": embedding,
}
documents_container.upsert_item(body=document_doc, partition_key=category)
```

**Correct (partition-key value is in the document body):**

```python
# GOOD: the item body contains the partition-key property.
session_doc = {
    "id": session_id,
    "sessionId": session_id,
    "userId": user_id,  # container partition key: /userId
    "title": title,
}
sessions_container.create_item(body=session_doc)

document_doc = {
    "id": document_id,
    "documentId": document_id,
    "category": category,  # container partition key: /category
    "content": content,
    "embedding": embedding,
}
documents_container.upsert_item(body=document_doc)
```

**Correct (partition_key belongs on reads, deletes, patches, and scoped queries):**

```python
session = sessions_container.read_item(item=session_id, partition_key=user_id)

sessions_container.patch_item(
    item=session_id,
    partition_key=user_id,
    patch_operations=[{"op": "replace", "path": "/title", "value": title}],
)

messages = list(messages_container.query_items(
    query="SELECT * FROM c WHERE c.sessionId = @sid ORDER BY c.createdAt",
    parameters=[{"name": "@sid", "value": session_id}],
    partition_key=session_id,
))
```

**Failure signature:** if a Python write path raises `TypeError: Session.request() got an unexpected keyword argument 'partition_key'`, inspect the nearest `create_item`, `upsert_item`, or `replace_item` call and remove the unsupported write kwarg.

Reference: [Azure Cosmos DB Python ContainerProxy API](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos.containerproxy)
