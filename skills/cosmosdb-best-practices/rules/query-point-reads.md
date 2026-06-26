---
title: Use Point Reads Instead of Queries for Known ID and Partition Key
impact: HIGH
impactDescription: 1 RU vs ~2.5 RU per single-document lookup
tags: query, point-read, ReadItem, ReadMany, performance, optimization
---

## Use Point Reads Instead of Queries for Known ID and Partition Key

When both `id` and partition key are known, use a point read instead of a query. Point read = 1 RU for 1 KB; equivalent query = ~2.5 RU (query engine overhead).

**Incorrect (query when point read suffices):**

```csharp
// ❌ Query engine invoked for a single known document
var query = new QueryDefinition("SELECT * FROM c WHERE c.id = @id")
    .WithParameter("@id", orderId);
var iterator = container.GetItemQueryIterator<Order>(query,
    requestOptions: new QueryRequestOptions { PartitionKey = new PartitionKey(customerId) });
```

**Correct (point read — bypasses query engine):**


```csharp
// ✅ 1 RU, no query engine overhead
var response = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
```

```python
# ✅ Point read
container.read_item(item=player_id, partition_key=game_id)
```

> Cross-ref: See `query-parameterize` for parameterized queries.
