---
title: Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search
impact: HIGH
impactDescription: full-text and hybrid queries fail at runtime without container-level configuration
tags: sdk, javascript, typescript, langchain, full-text-search, hybrid, container-setup
---

## Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search

**Impact: HIGH (full-text and hybrid queries fail at runtime without container-level configuration)**

Before using `FullTextSearch`, `Hybrid`, or `HybridScoreThreshold` search types with `AzureCosmosDBNoSQLVectorStore` in JavaScript/TypeScript, you must configure three things on your Cosmos DB container: (1) enable the full-text search capability on the account, (2) define a `fullTextPolicy` specifying which properties to index and their language, and (3) add `fullTextIndexes` entries to the indexing policy. Without all three, queries will fail with opaque errors.

**Incorrect (attempting hybrid search on unconfigured container):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// Container created with only vector embedding policy — no full-text config
const store = new AzureCosmosDBNoSQLVectorStore(embeddings, {
  endpoint: process.env.COSMOS_ENDPOINT,
  credential,
```

**Correct (container configured with full-text policy and indexes):**


```json
{
  "containerProperties": {
    "id": "docs",
    "partitionKey": { "paths": ["/tenantId"], "kind": "Hash" },
    "fullTextPolicy": {
      "defaultLanguage": "en-US",
```

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
```
