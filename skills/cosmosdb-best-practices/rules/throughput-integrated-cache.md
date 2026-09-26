---
title: Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway
impact: MEDIUM
impactDescription: reduces RU consumption and latency for repeated reads
tags: throughput, integrated-cache, dedicated-gateway, performance, cost, read-heavy
---

## Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway

**Impact: MEDIUM (reduces RU consumption and latency for repeated reads)**

For workloads that repeatedly read the same items or execute the same queries, Azure Cosmos DB's integrated cache can significantly reduce RU consumption and improve response latency. The integrated cache is available only when using a **dedicated gateway**. Cached point reads and queries can be served without contacting backend replicas until the configured cache staleness window expires.

Use the `MaxIntegratedCacheStaleness` request option to control how stale cached results are allowed to be. Integrated cache is appropriate for read-heavy workloads where slightly stale data is acceptable, but it only applies to reads using **Session** or **Eventual** consistency.

**Incorrect (point reads without integrated cache):**

```csharp
var client = new CosmosClient(connectionString);
var container = client.GetContainer("database", "container");

var response = await container.ReadItemAsync<Product>(
    "product-1",
    new PartitionKey("electronics"));
```

Every repeated request is sent to the backend, consuming RUs even when the data has not changed.

**Correct (use dedicated gateway with integrated cache):**

```csharp
var client = new CosmosClient(
    dedicatedGatewayConnectionString,
    new CosmosClientOptions
    {
        ConnectionMode = ConnectionMode.Gateway
    });

var container = client.GetContainer("database", "container");

var options = new ItemRequestOptions
{
    DedicatedGatewayRequestOptions = new DedicatedGatewayRequestOptions
    {
        MaxIntegratedCacheStaleness = TimeSpan.FromMinutes(5)
    }
};

var response = await container.ReadItemAsync<Product>(
    "product-1",
    new PartitionKey("electronics"),
    options);
```

Guidance:

- Use integrated cache for read-heavy workloads with frequent repeated point reads or queries.
- Connect through the **dedicated gateway** endpoint to enable integrated cache.
- Configure `MaxIntegratedCacheStaleness` based on how much stale data your application can tolerate.
- Use integrated cache only when **Eventual** or **Session** consistency satisfies application requirements.
- Do not rely on integrated cache for workloads requiring **Strong**, **Bounded Staleness**, or **Consistent Prefix** consistency guarantees.

Reference: <https://learn.microsoft.com/azure/cosmos-db/integrated-cache>
