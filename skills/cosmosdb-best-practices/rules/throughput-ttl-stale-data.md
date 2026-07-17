---
title: Expire Stale Data Before It Hits Storage Limits
impact: MEDIUM
impactDescription: avoids the partition storage wall on growing data
tags: throughput, ttl, storage, growth, archival, partition-limit
---

## Expire Stale Data Before It Hits Storage Limits

Data that only ever grows will eventually hit a hard ceiling: a physical partition caps at ~50 GiB before it must split, and a single logical partition key is hard-capped at ~20 GiB, after which writes to that key fail. Time-series, telemetry, event, and audit workloads are especially prone to this. When storage on the busiest partition is trending toward the limit, expire stale records with TTL, archive cold data to cheaper storage, or re-key so growth spreads across partitions — before the wall, not after.

**Incorrect (records accumulate forever):**

```csharp
public class TelemetryEvent
{
    public string Id { get; set; } = default!;
    public string DeviceId { get; set; } = default!;   // Partition key
    public DateTime Timestamp { get; set; }
    public object Payload { get; set; } = default!;
    // No TTL: every event persists indefinitely and the partition only grows.
}

await container.CreateItemAsync(evt, new PartitionKey(evt.DeviceId));
```

**Correct (container TTL plus a per-item override for stale telemetry):**

```csharp
// Default TTL expires items after the retention window.
var props = await container.ReadContainerAsync();
props.Resource.DefaultTimeToLive = 60 * 60 * 24 * 90; // 90 days
await container.ReplaceContainerAsync(props.Resource);

public class TelemetryEvent
{
    public string Id { get; set; } = default!;
    public string DeviceId { get; set; } = default!;
    public DateTime Timestamp { get; set; }
    public int? Ttl { get; set; } = 60 * 60 * 24 * 90; // per-item override (seconds)
}

await container.UpsertItemAsync(evt, new PartitionKey(evt.DeviceId));
```

Guidance:
- Set `DefaultTimeToLive` at the container level and override per item where retention varies.
- If a *single logical key* dominates growth, TTL alone may not be enough — archive cold history by time bucket or re-key for even distribution (see `partition-high-cardinality`).
- Archival (change feed to blob or another cheaper store) preserves history while keeping the operational container small.

Reference: [Time to Live (TTL) in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/time-to-live)
