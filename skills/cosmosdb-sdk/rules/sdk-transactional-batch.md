---
title: Use Transactional Batch for Atomic Multi-Item Operations
impact: HIGH
impactDescription: provides atomic writes within one logical partition
tags: sdk, transactional-batch, atomicity, partition
---

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
    for (var index = 0; index < 3; index++)
    {
        TransactionalBatchOperationResult<object> operation =
            response.GetOperationResultAtIndex<object>(index);

        if (!operation.IsSuccessStatusCode && (int)operation.StatusCode != 424)
        {
            // Record the root operation failure; other operations may be 424.
            Console.Error.WriteLine(
                $"Batch operation {index} failed with status {operation.StatusCode}");
        }
    }

    throw new InvalidOperationException(
        $"Order batch failed with status {response.StatusCode}");
}
```

All items in a transactional batch must share the same partition key value. A batch can contain at most 100 operations and its serialized payload cannot exceed 2 MB. Keep headroom for serialization overhead and split larger aggregates into multiple batches only when the application can preserve the required consistency across those transactions.

Check `IsSuccessStatusCode` on the overall response. On failure, inspect operation results with `GetOperationResultAtIndex<T>()` before throwing; the operation that caused the rollback carries its error status while dependent operations can report 424 (Failed Dependency). Use the batch-level status as a fallback when no individual root failure is available.

References: [Transactional batch operations](https://learn.microsoft.com/azure/cosmos-db/nosql/transactional-batch), [service quotas and limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits).
