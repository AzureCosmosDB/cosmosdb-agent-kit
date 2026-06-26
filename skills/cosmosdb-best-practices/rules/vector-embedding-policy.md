---
title: Define Vector Embedding Policy
impact: CRITICAL
impactDescription: Required for vector search functionality
tags: vector, embedding, configuration, ai, rag
---

## Define Vector Embedding Policy

**Impact: CRITICAL (Required for vector search functionality)**

The vector embedding policy provides essential information to the Azure Cosmos DB query engine about how to handle vector properties in the VectorDistance system functions. This policy is required and cannot be modified after container creation.

**Incorrect (no vector embedding policy):**

```csharp
// .NET - Missing vector embedding policy
var containerProperties = new ContainerProperties("mycontainer", "/partitionKey");
await database.CreateContainerAsync(containerProperties);
```

**Correct (with vector embedding policy):**


```csharp
// .NET - SDK 3.45.0+
List<Embedding> embeddings = new List<Embedding>()
{
    new Embedding()
    {
        Path = "/embedding",
```

```python
# Python
vector_embedding_policy = { 
    "vectorEmbeddings": [ 
        { 
            "path": "/embedding", 
            "dataType": "float32", 
```
