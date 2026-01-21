---
title: Use Continuation Tokens for Pagination
impact: HIGH
impactDescription: enables efficient large result sets
tags: query, pagination, continuation-token, performance
---

## Use Continuation Tokens for Pagination

Use continuation tokens to paginate through large result sets efficiently. Never use OFFSET/LIMIT for deep pagination.

**Incorrect (OFFSET/LIMIT for pagination):**

```csharp
// Anti-pattern: OFFSET increases cost linearly with page number
public async Task<List<Product>> GetProductsPage(int page, int pageSize)
{
    // Page 1: Skip 0, Page 100: Skip 9900
    var offset = (page - 1) * pageSize;
    
    // OFFSET must scan and discard all previous items!
    var query = $"SELECT * FROM c ORDER BY c.name OFFSET {offset} LIMIT {pageSize}";
    
    var results = await container.GetItemQueryIterator<Product>(query).ReadNextAsync();
    return results.ToList();
    
    // Page 1: Scans 100 items
    // Page 100: Scans 10,000 items, returns 100
    // RU cost grows linearly with page depth!
}
```

**Correct (continuation token pagination):**

```csharp
public class PagedResult<T>
{
    public List<T> Items { get; set; }
    public string ContinuationToken { get; set; }
    public bool HasMore => !string.IsNullOrEmpty(ContinuationToken);
}

public async Task<PagedResult<Product>> GetProductsPage(
    int pageSize, 
    string continuationToken = null)
{
    var query = new QueryDefinition("SELECT * FROM c ORDER BY c.name");
    
    var options = new QueryRequestOptions
    {
        MaxItemCount = pageSize  // Items per page
    };
    
    var iterator = container.GetItemQueryIterator<Product>(
        query,
        continuationToken: continuationToken,  // Resume from last position
        requestOptions: options);
    
    var response = await iterator.ReadNextAsync();
    
    return new PagedResult<Product>
    {
        Items = response.ToList(),
        ContinuationToken = response.ContinuationToken  // For next page
    };
    
    // Every page costs the same RU regardless of depth!
}

// Usage in API
[HttpGet("products")]
public async Task<IActionResult> GetProducts(
    [FromQuery] int pageSize = 20,
    [FromQuery] string continuationToken = null)
{
    // Decode token if passed as query param (URL-safe encoding)
    var token = continuationToken != null 
        ? Encoding.UTF8.GetString(Convert.FromBase64String(continuationToken))
        : null;
    
    var result = await GetProductsPage(pageSize, token);
    
    // Encode token for URL safety
    var nextToken = result.ContinuationToken != null
        ? Convert.ToBase64String(Encoding.UTF8.GetBytes(result.ContinuationToken))
        : null;
    
    return Ok(new { result.Items, NextPage = nextToken });
}
```

```csharp
// Streaming through all results
public async IAsyncEnumerable<Product> GetAllProducts()
{
    string continuationToken = null;
    
    do
    {
        var page = await GetProductsPage(100, continuationToken);
        
        foreach (var product in page.Items)
        {
            yield return product;
        }
        
        continuationToken = page.ContinuationToken;
    }
    while (continuationToken != null);
}
```

Reference: [Pagination in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/nosql/query/pagination)
