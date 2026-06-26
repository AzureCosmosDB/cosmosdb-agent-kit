---
title: Use VectorDistance for Similarity Search
impact: HIGH
impactDescription: Enables semantic search and RAG patterns
tags: vector, query, vectordistance, similarity, rag
---

## Use VectorDistance for Similarity Search

**Impact: HIGH (Enables semantic search and RAG patterns)**

Use the VectorDistance() system function to perform vector similarity searches. This function computes the distance between a query vector and stored vectors using the distance function specified in the vector embedding policy.

**Incorrect (missing ORDER BY or parameterization):**

```csharp
// .NET - Not parameterized, no ORDER BY
var query = "SELECT c.title FROM c WHERE VectorDistance(c.embedding, [0.1, 0.2, ...]) < 0.5";
// Issues: 
// 1. Hard-coded embedding array (query plan cache misses)
// 2. No ORDER BY (doesn't return most similar first)
// 3. Using WHERE instead of ORDER BY (less efficient)
```

**Correct (parameterized with ORDER BY):**


```csharp
// .NET - SDK 3.45.0+
float[] queryEmbedding = await GetEmbeddingAsync("search query");

var queryDef = new QueryDefinition(
    query: "SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore " +
           "FROM c ORDER BY VectorDistance(c.embedding, @embedding)"
).WithParameter("@embedding", queryEmbedding);
```

```python
# Python
query_embedding = get_embedding("search query")  # Returns list of floats

for item in container.query_items( 
    query='SELECT TOP 10 c.title, VectorDistance(c.embedding, @embedding) AS SimilarityScore ' +
          'FROM c ORDER BY VectorDistance(c.embedding, @embedding)', 
    parameters=[
```

> Cross-ref: See `monitoring-ru-consumption` for RU tracking.
> Cross-ref: See `query-parameterize` for parameterized queries.
