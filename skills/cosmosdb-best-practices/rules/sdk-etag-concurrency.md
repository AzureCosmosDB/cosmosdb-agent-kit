---
title: Use ETags for optimistic concurrency on read-modify-write operations
impact: HIGH
impactDescription: prevents lost updates in concurrent write scenarios
tags: sdk, concurrency, etag, consistency, read-modify-write
---

## Use ETags for Optimistic Concurrency

When performing read-modify-write operations (read a document, update a field, write it back), always use ETags to prevent lost updates from concurrent writes. Without ETags, the last writer silently overwrites changes from other operations.

**Problem: Lost updates without ETag checks**

```csharp
// Anti-pattern: Read-modify-write without concurrency control
// If two requests run concurrently, one update is silently lost
public async Task UpdatePlayerStatsAsync(string playerId, int newScore)
{
    // Thread A reads player (bestScore: 100)
    var response = await _container.ReadItemAsync<Player>(
        playerId, new PartitionKey(playerId));
    var player = response.Resource;

    // Thread B also reads player (bestScore: 100)
    // Thread B updates bestScore to 200 and writes

    // Thread A updates bestScore to 150 and writes
    // Thread A's write OVERWRITES Thread B's update!
    player.BestScore = Math.Max(player.BestScore, newScore);
    player.TotalGamesPlayed++;
    player.TotalScore += newScore;
    player.AverageScore = player.TotalScore / player.TotalGamesPlayed;

    await _container.UpsertItemAsync(player,  // Overwrites without checking!
        new PartitionKey(playerId));
}
```

**Solution: ETag-based optimistic concurrency with retry**

```csharp
// Correct: Use ETag to detect concurrent modifications and retry
public async Task UpdatePlayerStatsAsync(string playerId, int newScore)
{
    const int maxRetries = 3;

    for (int attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            // Read current state (includes ETag in response headers)
            var response = await _container.ReadItemAsync<Player>(
                playerId, new PartitionKey(playerId));
            var player = response.Resource;
            var etag = response.ETag;  // Capture the ETag

            // Modify the document
            player.BestScore = Math.Max(player.BestScore, newScore);
            player.TotalGamesPlayed++;
            player.TotalScore += newScore;
            player.AverageScore = player.TotalScore / player.TotalGamesPlayed;
            player.LastPlayedAt = DateTime.UtcNow;

            // Write with ETag condition — fails if document changed since read
            await _container.UpsertItemAsync(player,
                new PartitionKey(playerId),
                new ItemRequestOptions
                {
                    IfMatchEtag = etag  // Only succeeds if ETag matches
                });

            return; // Success
        }
        catch (CosmosException ex) when (ex.StatusCode == System.Net.HttpStatusCode.PreconditionFailed)
        {
            // HTTP 412: Document was modified by another request
            // Retry by re-reading the latest version
            if (attempt == maxRetries - 1)
            {
                throw new InvalidOperationException(
                    $"Failed to update player {playerId} after {maxRetries} attempts due to concurrent modifications.", ex);
            }
            // Loop back to re-read and retry
        }
    }
}
```

**Java equivalent:**

```java
// Java SDK: Use ETag with ifMatchETag option
CosmosItemResponse<Player> response = container.readItem(
    playerId, new PartitionKey(playerId), Player.class);
Player player = response.getItem();
String etag = response.getETag();

// Modify player...

CosmosItemRequestOptions options = new CosmosItemRequestOptions();
options.setIfMatchETag(etag);  // Conditional write

try {
    container.upsertItem(player, new PartitionKey(playerId), options);
} catch (CosmosException ex) {
    if (ex.getStatusCode() == 412) {
        // Retry: document was modified concurrently
    }
}
```

**Python equivalent:**

```python
# Python SDK: Use ETag with match_condition
response = container.read_item(item=player_id, partition_key=player_id)
etag = response.get('_etag')

# Modify response...

container.upsert_item(
    body=response,
    match_condition=etag,      # If-Match header
    etag=etag
)
# Raises CosmosHttpResponseError with status_code=412 on conflict
```

**When to use ETags:**
- **Always use** for read-modify-write patterns (counters, aggregates, status updates)
- **Always use** when multiple users/services can modify the same document
- **Skip** for append-only operations (new document creation with unique IDs)
- **Skip** for idempotent overwrites where last-writer-wins is acceptable

**Key Points:**
- Every Cosmos DB document has a system-managed `_etag` property that changes on every write
- Pass `IfMatchEtag` (or `setIfMatchETag` in Java) to get HTTP 412 on conflicts
- Always implement retry logic (typically 3 attempts) for ETag conflicts
- ETag checks add no extra RU cost — it's a header comparison, not an additional read
- For high-contention scenarios (thousands of concurrent updates to same document), consider a different data model (e.g., append scores as separate documents, aggregate periodically)

Reference: [Optimistic concurrency control in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency#optimistic-concurrency-control)
