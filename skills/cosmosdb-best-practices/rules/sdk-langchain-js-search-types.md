---
title: Choose the Correct Search Type for JS/TS LangChain Vector Store
impact: HIGH
impactDescription: selecting wrong search type returns irrelevant results or causes errors
tags: sdk, javascript, typescript, langchain, vector-search, full-text-search, hybrid
---

## Choose the Correct Search Type for JS/TS LangChain Vector Store

**Impact: HIGH (selecting wrong search type returns irrelevant results or causes errors)**

The `@langchain/azure-cosmosdb` package supports multiple search types via `AzureCosmosDBNoSQLVectorStore`. Choose the appropriate type based on your retrieval needs.

**Incorrect (using hybrid search without full-text configuration):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
```

**Correct (vector search — no special container config needed):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
  databaseName: "mydb",
```

```typescript
// Container must have fullTextPolicy and fullTextIndexes configured FIRST
const results = await store.similaritySearch("keyword and semantic query", 10, {
  searchType: "Hybrid",
});
```
