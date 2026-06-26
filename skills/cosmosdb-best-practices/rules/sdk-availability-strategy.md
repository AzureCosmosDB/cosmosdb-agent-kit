---
title: Configure Threshold-Based Availability Strategy (Hedging)
impact: HIGH
impactDescription: reduces tail latency by 90%+, eliminates regional outage impact
tags: sdk, hedging, availability-strategy, high-availability, resilience, cross-region
---

## Configure Threshold-Based Availability Strategy (Hedging)

The threshold-based availability strategy (hedging) improves tail latency and availability by sending parallel read requests to secondary regions when the primary region is slow. This approach drastically reduces the impact of regional outages or high-latency conditions.

**Incorrect (no availability strategy):**

```csharp
// Without availability strategy, slow regions cause high latency for all users
var client = new CosmosClient(connectionString, new CosmosClientOptions
{
    ApplicationPreferredRegions = new List<string> { "East US", "East US 2", "West US" }
});

// If East US is experiencing high latency (e.g., 2 seconds):
```

**Correct (.NET SDK - availability strategy with hedging):**


```csharp
// Configure threshold-based availability strategy
CosmosClient client = new CosmosClientBuilder("connection string")
    .WithApplicationPreferredRegions(
        new List<string> { "East US", "East US 2", "West US" })
    .WithAvailabilityStrategy(
        AvailabilityStrategy.CrossRegionHedgingStrategy(
            threshold: TimeSpan.FromMilliseconds(500),    // Wait 500ms before hedging
```

```csharp
// Alternative: Configure via CosmosClientOptions
CosmosClientOptions options = new CosmosClientOptions()
{
    AvailabilityStrategy = AvailabilityStrategy.CrossRegionHedgingStrategy(
        threshold: TimeSpan.FromMilliseconds(500),
        thresholdStep: TimeSpan.FromMilliseconds(100)
    ),
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
