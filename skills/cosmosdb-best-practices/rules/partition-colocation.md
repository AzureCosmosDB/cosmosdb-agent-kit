---
title: Collocate Related Items in the Same Partition
impact: CRITICAL
impactDescription: enables transactional batch operations and single-partition reads
tags: partition, colocation, transactional-batch, modeling
---

## Collocate Related Items in the Same Partition

Model items that are frequently read or written together so they share the same partition key value. Colocation keeps related operations inside one logical partition, which enables transactional batch writes and avoids expensive fan-out reads.

**Incorrect (related items spread across partitions):**

```csharp
// Orders and order lines use different partition keys.
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }  // Partition key
}

public class OrderLine
{
    public string Id { get; set; }
    public string OrderId { get; set; }     // Different partition key
    public string ProductId { get; set; }
}

// Updating an order and its lines now crosses partitions.
// You cannot use a single TransactionalBatch for the whole change.
```

**Correct (related items share a partition key):**

```csharp
// Orders and order lines share the same partition key value.
public class Order
{
    public string Id { get; set; }
    public string OrderId { get; set; }     // Partition key
    public string CustomerId { get; set; }
}

public class OrderLine
{
    public string Id { get; set; }
    public string OrderId { get; set; }     // Same partition key
    public string ProductId { get; set; }
}

var partitionKey = new PartitionKey(orderId);

var batch = container.CreateTransactionalBatch(partitionKey)
    .CreateItem(order)
    .CreateItem(orderLine);

TransactionalBatchResponse response = await batch.ExecuteAsync();
```

Use this pattern for aggregates that need atomic updates or low-latency reads, such as an order with its lines, a conversation with its messages, or a tenant-scoped workflow with its steps. If related items can grow beyond a logical partition limit, split the aggregate deliberately and use a documented consistency boundary.

Reference: [Model and partition data on Azure Cosmos DB using a real-world example](https://learn.microsoft.com/azure/cosmos-db/nosql/model-partition-example)
