---
title: Prevent Filter Injection in JS/TS LangChain Vector Store Queries
impact: CRITICAL
impactDescription: prevents NoSQL injection attacks that can exfiltrate or corrupt data
tags: sdk, javascript, typescript, langchain, security, injection, vector-search
---

## Prevent Filter Injection in JS/TS LangChain Vector Store Queries

**Impact: CRITICAL (prevents NoSQL injection attacks that can exfiltrate or corrupt data)**

When passing filter clauses to `AzureCosmosDBNoSQLVectorStore` similarity searches, **never** concatenate user input directly into the filter string. Cosmos DB NoSQL queries support parameterized queries with `@param` placeholders — always use these to safely inject user-provided values.

**Incorrect (string concatenation — SQL injection vulnerability):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // CRITICAL VULNERABILITY: User can inject arbitrary SQL predicates
  // e.g., userInput = "electronics' OR c.secret != '"
  const results = await store.similaritySearch("find products", 10, {
```

**Correct (parameterized queries with @param placeholders):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

async function searchByCategory(store: AzureCosmosDBNoSQLVectorStore, userInput: string) {
  // SAFE: Parameters are escaped by the SDK — no injection possible
  const results = await store.similaritySearch("find products", 10, {
    filter: "c.category = @category",
```

> Cross-ref: See `query-parameterize` for parameterized queries.
