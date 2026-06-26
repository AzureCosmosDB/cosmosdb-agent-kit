---
title: Enable Vector Search Feature on Account
impact: CRITICAL
impactDescription: Required before using vector search
tags: vector, configuration, feature, setup
---

## Enable Vector Search Feature on Account

**Impact: CRITICAL (Required before using vector search)**

Vector search must be explicitly enabled on the Azure Cosmos DB account before creating containers with vector policies. The feature can be enabled via Azure Portal or Azure CLI.

**Incorrect (attempting to use vectors without enabling feature):**

```csharp
// .NET - This will FAIL if feature not enabled
var embeddings = new List<Embedding>() { /* ... */ };
var properties = new ContainerProperties("docs", "/id")
{
    VectorEmbeddingPolicy = new(new Collection<Embedding>(embeddings))
};
```

**Correct (enable feature first, wait, then create):**


```bash
# Step 1: Enable feature
az cosmosdb update \
    --resource-group myResourceGroup \
    --name myCosmosAccount \
    --capabilities EnableNoSQLVectorSearch

```
