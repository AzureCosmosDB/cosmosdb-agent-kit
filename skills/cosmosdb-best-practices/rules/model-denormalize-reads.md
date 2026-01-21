---
title: Denormalize for Read-Heavy Workloads
impact: HIGH
impactDescription: reduces query RU by 2-10x
tags: model, denormalization, read-optimization, performance
---

## Denormalize for Read-Heavy Workloads

In read-heavy workloads, denormalize frequently-queried data to avoid expensive lookups. Accept write overhead for faster reads.

**Incorrect (normalized requires multiple queries):**

```csharp
// Displaying product list with category names
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }  // Just the ID
    public decimal Price { get; set; }
}

// To display "Product Name - Category Name" requires JOIN-like pattern:
var products = await GetProductsAsync();
foreach (var product in products)
{
    // N+1 query problem!
    var category = await container.ReadItemAsync<Category>(
        product.CategoryId, new PartitionKey(product.CategoryId));
    product.CategoryName = category.Name;
}
// 1 + N queries = terrible performance
```

**Correct (denormalized for read efficiency):**

```csharp
public class Product
{
    public string Id { get; set; }
    public string Name { get; set; }
    public string CategoryId { get; set; }
    
    // Denormalized category info for display
    public string CategoryName { get; set; }
    public string CategorySlug { get; set; }
    
    public decimal Price { get; set; }
}

// Single query returns everything needed for display
var query = "SELECT c.id, c.name, c.categoryName, c.price FROM c WHERE c.type = 'product'";
var products = await container.GetItemQueryIterator<Product>(query).ReadNextAsync();
// No additional queries needed!

// When category changes, update products using Change Feed
public async Task HandleCategoryChange(Category category)
{
    var query = $"SELECT * FROM c WHERE c.categoryId = '{category.Id}'";
    await foreach (var product in container.GetItemQueryIterator<Product>(query))
    {
        product.CategoryName = category.Name;
        await container.UpsertItemAsync(product);
    }
}
```

Denormalize when:
- Read-to-write ratio is high (10:1 or more)
- Denormalized data changes infrequently
- Query patterns benefit from co-located data

Reference: [Denormalization patterns](https://learn.microsoft.com/azure/cosmos-db/nosql/modeling-data#denormalization)
