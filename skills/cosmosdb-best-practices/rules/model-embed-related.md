---
title: Embed Related Data Retrieved Together
impact: CRITICAL
impactDescription: eliminates joins, reduces RU by 50-90%
tags: model, embedding, denormalization, performance
---

## Embed Related Data Retrieved Together

Embed related data within a single document when they're always accessed together. This eliminates the need for multiple queries (Cosmos DB has no JOINs across documents).

**Incorrect (requires multiple queries):**

```csharp
// Separate documents require multiple round-trips
var order = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
var customer = await container.ReadItemAsync<Customer>(order.CustomerId, new PartitionKey(order.CustomerId));
var items = await container.GetItemQueryIterator<OrderItem>(
    $"SELECT * FROM c WHERE c.orderId = '{orderId}'").ReadNextAsync();

// 3 separate queries = 3x latency + 3x RU cost
```

**Correct (single read operation):**

```csharp
// Embedded document - single query retrieves everything
public class Order
{
    public string Id { get; set; }
    public string CustomerId { get; set; }
    
    // Embedded customer summary (not full customer document)
    public CustomerSummary Customer { get; set; }
    
    // Embedded order items
    public List<OrderItem> Items { get; set; }
    
    public decimal Total { get; set; }
    public DateTime OrderDate { get; set; }
}

// Single read gets everything needed
var order = await container.ReadItemAsync<Order>(orderId, new PartitionKey(customerId));
// 1 query = lowest latency + minimal RU
```

Embed when:
- Data is read together frequently
- Embedded data changes infrequently
- Embedded data is bounded in size

Reference: [Data modeling in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data)
