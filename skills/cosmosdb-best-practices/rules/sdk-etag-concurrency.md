---
title: Use ETags for optimistic concurrency on read-modify-write operations
impact: HIGH
impactDescription: prevents lost updates in concurrent write scenarios
tags: sdk, concurrency, etag, consistency, read-modify-write
---

## Use ETags for optimistic concurrency on read-modify-write operations

For read-modify-write operations, use ETags to prevent lost updates. Without them, the last writer silently overwrites concurrent changes.

**Incorrect (no concurrency control — lost updates):**

```csharp
// Two concurrent requests both read bestScore: 100
// Thread A writes 150, Thread B writes 200
var response = await _container.ReadItemAsync<Player>(playerId, new PartitionKey(playerId));
var player = response.Resource;
player.BestScore = Math.Max(player.BestScore, newScore);
await _container.UpsertItemAsync(player, new PartitionKey(playerId)); // No ETag check!
```

**Correct (ETag-based optimistic concurrency with retry):**


```csharp
for (int attempt = 0; attempt < 3; attempt++)
{
    var response = await _container.ReadItemAsync<Player>(playerId, new PartitionKey(playerId));
    var player = response.Resource;
    var etag = response.ETag;

```

```python
# Python — use MatchConditions enum (NOT a string)
from azure.core import MatchConditions

response = container.read_item(item=player_id, partition_key=player_id)
etag = response.get('_etag')
# ... modify response ...
```
