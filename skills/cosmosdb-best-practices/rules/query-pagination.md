---
title: Use Continuation Tokens for Pagination
impact: HIGH
impactDescription: enables efficient large result sets
tags: query, pagination, continuation-token, performance
---

## Use Continuation Tokens for Pagination

Never use OFFSET/LIMIT for deep pagination — RU cost scales linearly with offset (page 100 scans 10,000 docs to return 100). Use continuation tokens instead (constant RU per page).

**Incorrect (OFFSET/LIMIT — cost grows with depth):**

```csharp
// ❌ Page 100: scans 10,000 items, returns 100. RU grows linearly!
var query = $"SELECT * FROM c ORDER BY c.name OFFSET {offset} LIMIT {pageSize}";
```

**Correct (continuation token — constant cost per page):**


```csharp
public async Task<PagedResult<Product>> GetProductsPage(int pageSize, string continuationToken = null)
{
    var query = new QueryDefinition("SELECT * FROM c ORDER BY c.name");
    var iterator = container.GetItemQueryIterator<Product>(query,
        continuationToken: continuationToken,
        requestOptions: new QueryRequestOptions { MaxItemCount = pageSize });
```

```python
# ✅ Continuation token pagination — stable RU per page
results = container.query_items(
    query=query, parameters=params,
    partition_key=player_id, max_item_count=page_size)
pager = results.by_page(continuation_token=continuation_token)
page = await pager.__anext__()
```
