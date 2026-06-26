---
title: Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain
impact: MEDIUM
impactDescription: incorrect deployment name causes 404 errors or uses wrong model
tags: sdk, javascript, typescript, langchain, embeddings, azure-openai
---

## Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain

**Impact: MEDIUM (incorrect deployment name causes 404 errors or uses wrong model)**

When using `AzureOpenAIEmbeddings` with `@langchain/openai` in JavaScript/TypeScript, you must specify the Azure OpenAI **deployment name** (the name you chose when deploying the model in Azure AI Studio or via CLI) — not the bare model name. Azure OpenAI uses deployment names to route requests, and these can differ from the underlying model name.

**Incorrect (using bare model name or wrong property):**

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

// BAD: "model" property is for OpenAI API, not Azure OpenAI
const embeddings = new AzureOpenAIEmbeddings({
  model: "text-embedding-3-small",  // Wrong property for Azure
});
```

**Correct (explicit deployment name and API version):**


```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";

const embeddings = new AzureOpenAIEmbeddings({
  azureOpenAIApiDeploymentName: "my-embedding-deployment", // Your actual deployment name
  azureOpenAIApiVersion: "2024-06-01",
  // Endpoint and key from environment variables:
```

```typescript
import { AzureOpenAIEmbeddings } from "@langchain/openai";
import { DefaultAzureCredential } from "@azure/identity";

const credential = new DefaultAzureCredential();

const embeddings = new AzureOpenAIEmbeddings({
```
