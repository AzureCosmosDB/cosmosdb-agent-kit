---
title: Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway
impact: MEDIUM
impactDescription: Significant RU reduction for repeated point reads and queries — cache hits cost 0 RUs
tags: throughput, caching, performance, dedicated-gateway, read-optimization
---

## Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway

**Impact: MEDIUM (significant RU reduction for repeated reads — cache hits cost 0 RUs)**

The Cosmos DB integrated cache (available via the dedicated gateway) caches point reads and query results in-memory at the gateway tier. For read-heavy workloads with repeated access to the same data, this can eliminate RU charges entirely for cache hits. Developers often connect through the public endpoint by default and miss out on this optimization entirely.

Use the integrated cache when:
- Your workload is read-heavy with high repetition (e.g., product catalogs, reference data, user profiles)
- You can tolerate slight staleness (eventual or session consistency)
- You want to reduce RU consumption without scaling up provisioned throughput

**Do not use the integrated cache when:**
- Your workload is write-heavy or reads are rarely repeated — cache hit rate will be too low to justify the cost
- You use Change Feed — it bypasses the cache entirely
- You require strong, bounded staleness, or consistent prefix consistency — these bypass the cache
- Note: The dedicated gateway is **separately billed** (hourly, per node) — factor this into your cost analysis before provisioning

**Limitations:**
- Only works with **session** or **eventual** consistency reads — consistent prefix, bounded staleness, and strong consistency bypass the cache entirely
- Requires a **dedicated gateway** to be provisioned and requests to be routed through the **dedicated gateway endpoint** using **Gateway connection mode** (not Direct mode)
- Each gateway node has an **independent cache** — sticky sessions are not guaranteed across nodes
- Cache staleness is controlled via `MaxIntegratedCacheStaleness` — tune this to your freshness requirements

---

**Incorrect (connecting via public endpoint — integrated cache bypassed):**

```csharp
// Using the standard public endpoint — integrated cache is NOT used
CosmosClient client = new CosmosClientBuilder("AccountEndpoint=https://<account>.documents.azure.com:443/;AccountKey=<key>;")
    .WithConsistencyLevel(ConsistencyLevel.Session)
    .Build();

Container container = client.GetContainer("mydb", "mycontainer");

// This point read hits the backend every time — full RU cost on each call
ItemResponse<Product> response = await container.ReadItemAsync<Product>(
    id: "product-123",
    partitionKey: new PartitionKey("electronics")
);
```

**Correct (connecting via dedicated gateway endpoint — integrated cache enabled):**

```csharp
// Use the dedicated gateway endpoint to enable the integrated cache
// Dedicated gateway endpoint format: https://<account>.sqlx.cosmos.azure.com:443/
CosmosClient client = new CosmosClientBuilder(
        "AccountEndpoint=https://<account>.sqlx.cosmos.azure.com:443/;AccountKey=<key>;")
    .WithConnectionModeGateway()   // Required: Direct mode bypasses the dedicated gateway and cache
    .WithConsistencyLevel(ConsistencyLevel.Session)
    .Build();

Container container = client.GetContainer("mydb", "mycontainer");

// Configure staleness tolerance — cache hits within this window cost 0 RUs
ItemRequestOptions options = new ItemRequestOptions
{
    DedicatedGatewayRequestOptions = new DedicatedGatewayRequestOptions
    {
        MaxIntegratedCacheStaleness = TimeSpan.FromMinutes(5)
    }
};

// First call: cache miss — fetches from backend (normal RU cost)
// Subsequent calls within staleness window: cache hit — 0 RUs charged
ItemResponse<Product> response = await container.ReadItemAsync<Product>(
    id: "product-123",
    partitionKey: new PartitionKey("electronics"),
    requestOptions: options
);
```

**Query caching example:**

```csharp
QueryRequestOptions queryOptions = new QueryRequestOptions
{
    DedicatedGatewayRequestOptions = new DedicatedGatewayRequestOptions
    {
        MaxIntegratedCacheStaleness = TimeSpan.FromMinutes(5)
    }
};

var query = new QueryDefinition("SELECT * FROM c WHERE c.category = @category")
    .WithParameter("@category", "electronics");

// Repeated queries with the same text and parameters benefit from cache hits
FeedIterator<Product> iterator = container.GetItemQueryIterator<Product>(
    query,
    requestOptions: queryOptions
);
```

Reference: [Azure Cosmos DB integrated cache](https://learn.microsoft.com/azure/cosmos-db/integrated-cache)