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
    throw new InvalidOperationException(
        $"Order batch failed with status {response.StatusCode}");
}

for (var index = 0; index < 3; index++)
{
    TransactionalBatchOperationResult<object> operation =
        response.GetOperationResultAtIndex<object>(index);

    if (!operation.IsSuccessStatusCode)
    {
        // Handle or log the specific operation failure before returning success.
        throw new InvalidOperationException(
            $"Batch operation {index} failed with status {operation.StatusCode}");
    }
}
```

All items in a transactional batch must share the same partition key value. A batch can contain at most 100 operations and its serialized payload cannot exceed 2 MB. Keep headroom for serialization overhead and split larger aggregates into multiple batches only when the application can preserve the required consistency across those transactions.

Check `IsSuccessStatusCode` on the overall response and inspect each operation result with `GetOperationResultAtIndex<T>()` when the caller needs operation-level diagnostics. A failed operation causes the transaction to roll back; the failed operation carries its error status and other operations can report 424 (Failed Dependency). Do not report success based only on the HTTP-level batch response or discard the failing operation's status.

References: [Transactional batch operations](https://learn.microsoft.com/azure/cosmos-db/nosql/transactional-batch), [service quotas and limits](https://learn.microsoft.com/azure/cosmos-db/concepts-limits).
