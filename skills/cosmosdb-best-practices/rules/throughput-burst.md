---
title: Understand Burst Capacity
impact: MEDIUM
impactDescription: handles short traffic spikes
tags: throughput, burst, capacity, spikes
---

## Understand Burst Capacity

Cosmos DB provides burst capacity to handle short traffic spikes above provisioned throughput. Understand how it works to avoid unexpected throttling.

**Incorrect (relying on burst for sustained load):**

```csharp
// Provisioned 1,000 RU/s but regularly need 1,500 RU/s
var container = await database.CreateContainerAsync(props, throughput: 1000);

// Hoping burst will cover:
// - Hour 1: Burst bucket fills from overnight

```

**Correct (provision for actual sustained needs):**


```csharp
// Option 1: Provision for peak sustained load
await database.CreateContainerAsync(props, throughput: 1500);

// Option 2: Use autoscale for variable loads
await database.CreateContainerAsync(
    props,
```

```csharp
// Monitor burst usage
// Azure Monitor metric: "Normalized RU Consumption"

// Detect burst usage in code
var response = await container.ReadItemAsync<Order>(id, pk);
// Check if operation used more than provisioned share
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
