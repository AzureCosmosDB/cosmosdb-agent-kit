---
title: Use TTL for Automatic Data Expiration
impact: MEDIUM
impactDescription: expired data is removed automatically in the background instead of through costly cleanup jobs
tags: model, ttl, expiration, retention, cleanup
---

Cosmos DB can delete expired items for you. Enable Time-to-Live on the container and items past their expiry are removed by a background process that uses leftover request units, so you pay nothing extra in RUs and write no cleanup code. Scheduled cleanup jobs that query for old items and delete them one by one burn RUs on every run and compete with your live traffic.

The most flexible setup is a container default of `-1` (items never expire on their own) combined with a per-item `ttl` property in seconds. Items that set `ttl` expire on their own schedule, items that omit it stick around forever. You can also set a positive container default so everything expires unless an item overrides it.

Typical fits: session tokens, event logs, temporary caches, OTP codes, telemetry with a fixed retention window.

**Incorrect (scheduled cleanup job):**

```csharp
// Timer-triggered job that scans for expired sessions and deletes them
public async Task CleanupExpiredSessions()
{
    var cutoff = DateTimeOffset.UtcNow.AddHours(-24).ToUnixTimeSeconds();
    var query = new QueryDefinition(
        "SELECT c.id, c.userId FROM c WHERE c._ts < @cutoff")
        .WithParameter("@cutoff", cutoff);

    // Cross-partition query plus a delete per item, every single run
    using var iterator = container.GetItemQueryIterator<SessionRef>(query);
    while (iterator.HasMoreResults)
    {
        foreach (var session in await iterator.ReadNextAsync())
        {
            await container.DeleteItemAsync<SessionRef>(
                session.Id, new PartitionKey(session.UserId));
        }
    }
}
```

**Correct (TTL on the container, per-item overrides):**

```csharp
// Enable TTL with no default expiry; items opt in via their ttl property
var properties = new ContainerProperties("sessions", "/userId")
{
    DefaultTimeToLive = -1
};
await database.CreateContainerIfNotExistsAsync(properties);

public class Session
{
    [JsonProperty("id")]
    public string Id { get; set; }

    [JsonProperty("userId")]
    public string UserId { get; set; }

    // Expires 24 hours after the last write to this item
    [JsonProperty("ttl")]
    public int Ttl { get; set; } = 86400;
}

public class AuditRecord
{
    [JsonProperty("id")]
    public string Id { get; set; }

    [JsonProperty("userId")]
    public string UserId { get; set; }

    // No ttl property: with a -1 container default this never expires
}
```

The expiry clock is based on `_ts`, the item's last modified time, so any update resets it. That is handy for sliding expirations like sessions, but if you need a fixed retention window, avoid touching items you expect to age out, or store an absolute expiry date and compute `ttl` from it at write time.

A few things to know:

- TTL on an item does nothing unless TTL is enabled on the container. With `DefaultTimeToLive` unset, per-item `ttl` values are ignored.
- Deletion is not instant. Expired items are removed when spare RUs are available, but they stop appearing in query results as soon as they expire.
- Setting `ttl` to `-1` on an item makes that item never expire, even when the container has a positive default.

Reference: [Time to Live in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/time-to-live)
