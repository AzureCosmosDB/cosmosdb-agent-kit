---
name: cosmosdb-full-text-search
description: |
  Azure Cosmos DB full-text search best practices: enabling the capability flag,
  defining fullTextPolicy, configuring fullTextIndexes, keyword matching with
  FullTextContains functions, BM25 relevance ranking, and hybrid queries.
  USE FOR: Cosmos DB full-text search, FTS, EnableNoSQLFullTextSearch,
  fullTextPolicy, fullTextIndexes, FullTextContains, FullTextContainsAll,
  FullTextContainsAny, FullTextScore, BM25 ranking, RANK, hybrid queries,
  keyword search, inverted index, language-aware tokenization.
  DO NOT USE FOR: vector search (use cosmosdb-vector-search),
  regular query optimization (use cosmosdb-query-optimization).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Full-Text Search

Best practices for configuring and using native full-text search in Azure Cosmos DB.

## When to Apply

Reference these guidelines when:
- Enabling full-text search on a Cosmos DB account
- Defining full-text policies and indexes
- Writing keyword search queries
- Implementing BM25 relevance ranking
- Combining full-text search with other filters

## Rules

- [fts-enable-capability](rules/fts-enable-capability.md) - Enable EnableNoSQLFullTextSearch capability
- [fts-define-policy](rules/fts-define-policy.md) - Define fullTextPolicy with correct language code
- [fts-add-index](rules/fts-add-index.md) - Add fullTextIndexes in the indexing policy
- [fts-keyword-matching](rules/fts-keyword-matching.md) - Use FullTextContains functions
- [fts-relevance-ranking](rules/fts-relevance-ranking.md) - Use ORDER BY RANK FullTextScore for BM25
- [fts-hybrid-queries](rules/fts-hybrid-queries.md) - Combine FTS with range/equality filters

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
