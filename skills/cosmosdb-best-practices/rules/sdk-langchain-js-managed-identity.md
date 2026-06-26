---
title: Use Managed Identity for JS/TS LangChain Cosmos DB Integration
impact: CRITICAL
impactDescription: zero-secret authentication eliminates credential leakage risk
tags: sdk, javascript, typescript, langchain, security, managed-identity
---

## Use Managed Identity for JS/TS LangChain Cosmos DB Integration

**Impact: CRITICAL (zero-secret authentication eliminates credential leakage risk)**

In production JavaScript/TypeScript applications using `@langchain/azure-cosmosdb`, always authenticate with `DefaultAzureCredential` from `@azure/identity` instead of connection strings. Connection strings contain master keys that grant full access — if leaked, they compromise the entire account.

**Incorrect (connection string in production):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
});
```

**Correct (endpoint + DefaultAzureCredential):**


```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "text-embedding-3-small",
```

```bash
az cosmosdb sql role assignment create \
  --account-name myaccount \
  --resource-group myrg \
  --role-definition-id 00000000-0000-0000-0000-000000000002 \
  --principal-id <managed-identity-object-id> \
  --scope "/"
```
