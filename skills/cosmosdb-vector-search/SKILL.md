---
name: cosmosdb-vector-search
description: |
  Azure Cosmos DB vector search best practices: enabling the feature, defining
  embedding policies, configuring vector indexes (flat, quantizedFlat, diskANN),
  normalizing embeddings, VectorDistance queries, repository patterns for RAG, and FastAPI RAG API integration.
  USE FOR: Cosmos DB vector search, vector embedding policy, vector index,
  flat index, quantizedFlat, diskANN, VectorDistance, cosine similarity,
  embedding normalization, RAG, retrieval augmented generation, semantic search,
  vector repository pattern, AI search, FastAPI RAG API, hybrid metadata filters.
  DO NOT USE FOR: full-text search (use cosmosdb-full-text-search),
  LangChain integration (use cosmosdb-sdk or cosmosdb-design-patterns).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Vector Search

Best practices for configuring and using vector search in Azure Cosmos DB for AI-powered semantic search and RAG.

## When to Apply

Reference these guidelines when:
- Enabling vector search on a Cosmos DB account
- Defining vector embedding policies
- Choosing vector index types (flat, quantizedFlat, diskANN)
- Writing vector similarity queries
- Implementing RAG patterns with Cosmos DB
- Building FastAPI or REST APIs that combine vector search with session/message storage; also use cosmosdb-sdk and cosmosdb-design-patterns for SDK writes and response DTOs

## Rules

- [vector-enable-feature](rules/vector-enable-feature.md) - Enable vector search on the account
- [vector-embedding-policy](rules/vector-embedding-policy.md) - Define vector embedding policy
- [vector-index-type](rules/vector-index-type.md) - Configure vector indexes in indexing policy
- [vector-normalize-embeddings](rules/vector-normalize-embeddings.md) - Normalize embeddings for cosine similarity
- [vector-distance-query](rules/vector-distance-query.md) - Use VectorDistance for similarity search
- [vector-repository-pattern](rules/vector-repository-pattern.md) - Implement repository pattern for vector search

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
