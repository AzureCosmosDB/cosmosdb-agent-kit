---
title: Choose Container vs Database Throughput
impact: MEDIUM
impactDescription: optimizes cost and isolation
tags: throughput, container, database, allocation
---

## Choose Container vs Database Throughput

Decide between container-level (dedicated) and database-level (shared) throughput based on workload isolation needs and cost optimization.

**Incorrect (one-size-fits-all allocation):**

```csharp
// Anti-pattern: dedicated throughput for every container including low-traffic ones
var logsContainer = await database.CreateContainerAsync(
    new ContainerProperties("logs", "/date"),
    throughput: 400);  // Paying minimum 400 RU/s for rarely-used container
// 20 low-traffic containers × 400 RU/s = 8,000 RU/s wasted
```

**Correct (choose based on workload):**

```csharp
// Database-level: share RU across low-traffic containers
var database = await cosmosClient.CreateDatabaseAsync("my-db", throughput: 5000);

// Container-level: dedicate RU for critical/high-volume containers
var ordersContainer = await database.CreateContainerAsync(
    new ContainerProperties("orders", "/customerId"),
    throughput: 10000);  // Dedicated, not shared

// Other containers share database throughput pool
var productsContainer = await database.CreateContainerAsync(
    new ContainerProperties("products", "/categoryId"));  // Shared
```

**Decision guide:** Container-level for critical/predictable workloads or tenant isolation. Database-level for many low-traffic containers or dev/test. Hybrid for mixed scenarios.
