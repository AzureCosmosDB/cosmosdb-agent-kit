---
title: Denormalize for Read-Heavy Workloads
impact: HIGH
impactDescription: reduces query RU by 2-10x
tags: model, denormalization, read-optimization, performance
---

## Denormalize for Read-Heavy Workloads

In read-heavy workloads, duplicate frequently-queried data to avoid expensive lookups. Accept write overhead for faster reads.

**Incorrect (normalized requires multiple queries):**

```csharp
// N+1 query problem — separate lookup per product for category name
foreach (var product in products)
{
    var category = await container.ReadItemAsync<Category>(
        product.CategoryId, new PartitionKey(product.CategoryId));
    product.CategoryName = category.Name;
```

**Correct (denormalized for read efficiency):**


```csharp
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }
    public string CategoryName { get; set; }  // Denormalized
```

```python
# Cascade delete — remove all related documents
async def delete_player(player_id: str):
    await players_container.delete_item(item=player_id, partition_key=player_id)
    # Delete from scores container
    async for page in scores_container.query_items(
        query="SELECT c.id FROM c WHERE c.playerId = @pid",
```
