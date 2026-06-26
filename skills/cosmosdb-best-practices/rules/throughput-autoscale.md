---
title: Use Autoscale for Variable Workloads
impact: HIGH
impactDescription: handles traffic spikes, optimizes cost
tags: throughput, autoscale, scaling, cost
---

## Use Autoscale for Variable Workloads

Use autoscale throughput for workloads with variable or unpredictable traffic patterns. It automatically scales between 10% and 100% of max RU/s.

**Incorrect (fixed throughput for variable workload):**

```csharp
// Fixed provisioned throughput
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};
```

**Correct (autoscale for variable workloads):**


```csharp
// Autoscale with max 10,000 RU/s
var containerProperties = new ContainerProperties
{
    Id = "orders",
    PartitionKeyPath = "/customerId"
};
```

```csharp
// Check current autoscale settings
var throughputResponse = await container.ReadThroughputAsync(new RequestOptions());
var autoscaleSettings = throughputResponse.Resource.AutoscaleMaxThroughput;
Console.WriteLine($"Autoscale max: {autoscaleSettings} RU/s");
Console.WriteLine($"Current: {throughputResponse.Resource.Throughput} RU/s");
```
