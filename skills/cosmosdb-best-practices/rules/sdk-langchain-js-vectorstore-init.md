---
title: Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript
impact: HIGH
impactDescription: prevents runtime connection failures and misconfigured vector stores
tags: sdk, javascript, typescript, langchain, vector-search, initialization
---

## Correctly Initialize AzureCosmosDBNoSQLVectorStore

Initialize `AzureCosmosDBNoSQLVectorStore` with an embedding model instance and either a connection string (dev) or endpoint + `DefaultAzureCredential` (prod). Database/container must exist when using RBAC.

**Incorrect (missing embedding model, relying on auto-create with RBAC):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";

// ❌ No embedding model — store cannot generate vectors
const store = new AzureCosmosDBNoSQLVectorStore({
  connectionString: process.env.COSMOS_CONNECTION_STRING,
  databaseName: "mydb",
  containerName: "vectors",
  // Missing: embedding model!
});
```

**Correct (embedding model + proper initialization):**

```typescript
import { AzureCosmosDBNoSQLVectorStore } from "@langchain/azure-cosmosdb";
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

// ✅ Development — connection string
const store = new AzureCosmosDBNoSQLVectorStore(
  new AzureOpenAIEmbeddings({ azureOpenAIApiDeploymentName: "text-embedding-ada-002" }),
  {
    connectionString: process.env.COSMOS_CONNECTION_STRING,
    databaseName: "mydb",
    containerName: "vectors",
  }
);

// ✅ Production — RBAC with DefaultAzureCredential (database must pre-exist)
const prodStore = new AzureCosmosDBNoSQLVectorStore(
  new AzureOpenAIEmbeddings({ azureOpenAIApiDeploymentName: "text-embedding-ada-002" }),
  {
    endpoint: process.env.COSMOS_ENDPOINT,
    credential: new DefaultAzureCredential(),
    databaseName: "mydb",
    containerName: "vectors",
  }
);

await store.initialize(); // Required before first use
```

**Key points:**
- Always pass embedding model as first argument
- Call `await store.initialize()` before first operation
- With RBAC, pre-create database/container (SDK won't auto-create)
- Connection string for local dev, DefaultAzureCredential for production
