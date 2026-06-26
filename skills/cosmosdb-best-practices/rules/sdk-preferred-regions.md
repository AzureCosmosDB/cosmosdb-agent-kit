---
title: Configure Preferred Regions for Availability
impact: HIGH
impactDescription: enables automatic failover, reduces latency
tags: sdk, regions, availability, failover
---

## Configure Preferred Regions for Availability

Configure preferred regions in priority order for multi-region deployments. The SDK automatically routes to available regions during outages.

**Incorrect (no region configuration):**

```csharp
// No region preference - SDK uses account's default write region
var client = new CosmosClient(connectionString);

// Problems:
// - May route to distant region (high latency)
```

**Correct (explicit region configuration):**


```csharp
// Configure preferred regions in order of preference
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationName = "MyApp",
    
    // SDK tries regions in order until one succeeds
```

```csharp
// Dynamic region based on deployment
public static CosmosClient CreateClient(string connectionString, string deploymentRegion)
{
    var preferredRegions = deploymentRegion switch
    {
        "westus" => new List<string> { Regions.WestUS2, Regions.EastUS2, Regions.WestEurope },
```

> Cross-ref: See `sdk-diagnostics` for capturing diagnostics.
