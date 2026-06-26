---
title: Use Async APIs for Better Throughput
impact: HIGH
impactDescription: improves concurrency 10-100x
tags: sdk, async, throughput, performance
---

## Use Async APIs for Better Throughput

Always use async/await patterns for Cosmos DB operations. Synchronous calls block threads and severely limit throughput under load.

**Incorrect (blocking synchronous calls):**

```csharp
// Anti-pattern: Blocking async code
public Order GetOrder(string orderId, string customerId)
{
    // .Result blocks the calling thread!
    var response = _container.ReadItemAsync<Order>(
        orderId, 
```

**Correct (fully async):**


```csharp
public async Task<Order> GetOrderAsync(string orderId, string customerId)
{
    var response = await _container.ReadItemAsync<Order>(
        orderId, 
        new PartitionKey(customerId));
    
```

```csharp
// Concurrent operations with Task.WhenAll
public async Task<OrderWithItems> GetOrderWithItemsAsync(string orderId, string customerId)
{
    // Start both operations concurrently
    var orderTask = _container.ReadItemAsync<Order>(
        orderId, new PartitionKey(customerId));
```

> Cross-ref: See `query-parameterize` for parameterized queries.
