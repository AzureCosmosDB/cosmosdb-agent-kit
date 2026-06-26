---
title: Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS
impact: MEDIUM
impactDescription: reduces LLM API costs and latency by caching semantically similar queries
tags: sdk, javascript, typescript, langchain, caching, vector-search, cost-optimization
---

## Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS

**Impact: MEDIUM (reduces LLM API costs and latency by caching semantically similar queries)**

When building LLM-powered applications with LangChain.js, use `AzureCosmosDBNoSQLSemanticCache` to cache LLM responses in Cosmos DB. Unlike exact-match caches, semantic cache uses vector similarity to return cached responses for queries that are semantically similar (not just identical).

**Incorrect (no caching — every request hits the LLM):**

```typescript
import { ChatOpenAI } from "@langchain/openai";

const model = new ChatOpenAI({
  azureOpenAIApiDeploymentName: "gpt-4o",
});

```

**Correct (semantic cache with Cosmos DB):**


```typescript
import { AzureCosmosDBNoSQLSemanticCache } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings, ChatOpenAI } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

```
