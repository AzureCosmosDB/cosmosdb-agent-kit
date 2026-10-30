---
title: Use Semantic Reranker only after indexed candidate retrieval
impact: HIGH
impactDescription: improves top-result relevance while avoiding expensive reranker misuse
tags:
  - fts
  - full-text-search
  - semantic-reranker
  - hybrid
  - ranking
  - gen-ai
---

## Use Semantic Reranker as a Second-Stage Ranker

**Impact: HIGH (improves top-result relevance while avoiding expensive reranker misuse)**

Semantic Reranker does not retrieve documents from Cosmos DB. It reranks a candidate set that you already retrieved with indexed queries (for example, vector, full-text, or hybrid queries). Always run first-stage retrieval to produce a bounded candidate list, then rerank that list.

Keep reranker requests within service limits: up to 50 candidate documents per call, and keep each context-document pair within the supported token limit. Also ensure the caller has the **Semantic Reranker User** role on the account.

**Incorrect (treating reranker as a primary retrieval engine):**

```python
# Fetches too many documents and reranks unbounded results
candidates = list(container.query_items(
    query="SELECT * FROM c",
    enable_cross_partition_query=True
))

reranked = client.semantic_reranker.rerank(
    query="Find docs about recovery point objective",
    documents=[json.dumps(doc) for doc in candidates]  # can exceed 50-doc limit
)
```

**Correct (indexed retrieval first, then rerank top candidates):**

```sql
SELECT TOP 30 c.id, c.partitionKey, c.title, c.content
FROM c
WHERE FullTextContains(c.content, @q)
ORDER BY RANK FullTextScore(c.content, @q)
```

```python
candidate_query = "SELECT TOP 30 c.id, c.partitionKey, c.title, c.content " \
    "FROM c WHERE FullTextContains(c.content, @q) " \
    "ORDER BY RANK FullTextScore(c.content, @q)"

candidates = list(container.query_items(
    query=candidate_query,
    parameters=[{"name": "@q", "value": search_text}],
    enable_cross_partition_query=True
))

reranked = client.semantic_reranker.rerank(
    query=search_text,
    documents=[json.dumps(doc) for doc in candidates[:50]],
    top_k=10
)
```

Reference: [Semantic Reranker in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/gen-ai/semantic-reranker)
