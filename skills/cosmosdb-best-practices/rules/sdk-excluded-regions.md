---
title: Configure Excluded Regions for Dynamic Failover
impact: MEDIUM
impactDescription: enables dynamic routing control without code changes
tags: sdk, excluded-regions, high-availability, failover, routing
---

## Configure Excluded Regions for Dynamic Failover

The excluded regions feature enables fine-grained control over request routing by excluding specific regions on a per-request or client basis. This allows dynamic failover without code changes or restarts.

**Incorrect (static region configuration):**

```csharp
// Static configuration requires restart to change routing
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "West US" }
});

// If East US has issues but isn't fully down:
```

**Correct (.NET SDK - excluded regions):**


```csharp
// Configure excluded regions at request level (.NET SDK 3.37.0+)
CosmosClientOptions options = new CosmosClientOptions()
{
    ApplicationPreferredRegions = new List<string> { "West US", "Central US", "East US" }
};

CosmosClient client = new CosmosClient(connectionString, options);
```

```csharp
// Handle rate limiting by routing to alternate regions
ItemResponse<Order> response;
try
{
    response = await container.ReadItemAsync<Order>("id", partitionKey);
}
catch (CosmosException ex) when (ex.StatusCode == HttpStatusCode.TooManyRequests)
```

> Cross-ref: See `sdk-429-retry` for retry/throttle handling.
