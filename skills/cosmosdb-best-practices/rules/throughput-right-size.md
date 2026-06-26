---
title: Right-Size Provisioned Throughput
impact: MEDIUM
impactDescription: balances performance and cost
tags: throughput, provisioning, capacity-planning, cost
---

## Right-Size Provisioned Throughput

Provision throughput based on actual workload needs. Over-provisioning wastes money; under-provisioning causes throttling.

**Incorrect (arbitrary throughput):**

```csharp
// Guessing throughput without analysis
await database.CreateContainerAsync(containerProperties, throughput: 10000);
// "10,000 sounds like a good number"

// Results in:
// - Over-provisioned: Wasting money if actual need is 2,000 RU/s
```

**Correct (data-driven provisioning):**


```csharp
// Step 1: Calculate RU requirements

// Point read (by id + partition key): ~1 RU for 1KB item
// Point write: ~5 RU for 1KB item  

// Example calculation:
```

```csharp
// Step 2: Monitor and adjust

// Check RU consumption in code
var response = await container.ReadItemAsync<Order>(id, new PartitionKey(pk));
Console.WriteLine($"Read consumed: {response.RequestCharge} RU");

```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
