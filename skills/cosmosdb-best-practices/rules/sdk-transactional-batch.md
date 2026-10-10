---
title: Use Transactional Batch for Atomic Multi-Item Operations
impact: HIGH
impactDescription: provides atomic writes within one logical partition
tags: sdk, transactional-batch, atomicity, partition
---

## Use Transactional Batch for Atomic Multi-Item Operations

Use transactional batch when multiple creates, updates, deletes, or patches must succeed or fail together within the same logical partition. This avoids custom compensation logic for operations that Azure Cosmos DB can already execute atomically.

**Incorrect (separate writes that can partially succeed):**

```csharp
await container.CreateItemAsync(order, new PartitionKey(order.OrderId));
await container.CreateItemAsync(orderLine, new PartitionKey(order.OrderId));
await container.PatchItemAsync<OrderSummary>(
    order.OrderId,
    new PartitionKey(order.OrderId),
    patchOperations);
```

If one operation fails after an earlier operation succeeds, the application must detect and repair partial state.

**Correct (batch related writes in one logical partition):**

```csharp
var partitionKey = new PartitionKey(order.OrderId);

TransactionalBatch batch = container.CreateTransactionalBatch(partitionKey)
    .CreateItem(order)
    .CreateItem(orderLine)
    .PatchItem(order.OrderId, patchOperations);

TransactionalBatchResponse response = await batch.ExecuteAsync();

if (!response.IsSuccessStatusCode)
{
    throw new InvalidOperationException(
        $"Order batch failed with status {response.StatusCode}");
}
```

All items in a transactional batch must share the same partition key value. Keep each batch within service limits, including the maximum number of operations and total request size, and split work deliberately when an aggregate crosses those boundaries.

Reference: [Transactional batch operations in Azure Cosmos DB for NoSQL](https://learn.microsoft.com/azure/cosmos-db/nosql/transactional-batch)
