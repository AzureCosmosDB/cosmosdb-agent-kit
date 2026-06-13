---
title: Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway
impact: MEDIUM
impactDescription: Up to 100x RU reduction for repeated point reads and queries
tags: throughput, caching, performance, dedicated-gateway, read-optimization
---

## Use Integrated Cache for Read-Heavy Workloads with Dedicated Gateway

**Impact: MEDIUM (up to 100x RU reduction for repeated reads)**

The Cosmos DB integrated cache (available via the dedicated gateway) caches point reads and query results in-memory at the gateway tier. For read-heavy workloads with repeated access to the same data, this can eliminate RU charges entirely for cache hits. Developers often connect through the public endpoint by default and miss out on this optimization entirely.

Use the integrated cache when:
- Your workload is read-heavy with high repetition (e.g. product catalogs, reference data, user profiles)
- You can tolerate slight staleness (eventual or session consistency)
- You want to reduce RU consumption without scaling up provisioned throughput

**Limitations:**
- Only works with **eventual consistency** or **session consistency** reads
- Requires connecting through the **dedicated gateway endpoint**, not the public endpoint
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

// Repeated queries with the same text and parameters benefit from cache hits
FeedIterator<Product> iterator = container.GetItemQueryIterator<Product>(
    queryText: "SELECT * FROM c WHERE c.category = 'electronics'",
    requestOptions: queryOptions
);
```

Reference: [Azure Cosmos DB integrated cache](https://learn.microsoft.com/azure/cosmos-db/integrated-cache)