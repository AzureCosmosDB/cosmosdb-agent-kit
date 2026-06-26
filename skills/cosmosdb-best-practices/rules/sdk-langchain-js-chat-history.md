---
title: Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS
impact: HIGH
impactDescription: enables persistent multi-turn conversations that survive restarts and scale horizontally
tags: sdk, javascript, typescript, langchain, chat-history, persistence
---

## Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS

**Impact: HIGH (enables persistent multi-turn conversations that survive restarts and scale horizontally)**

When building conversational AI applications with LangChain.js, use `AzureCosmosDBNoSQLChatMessageHistory` to persist chat messages in Cosmos DB. This ensures conversations survive process restarts, enables horizontal scaling across multiple instances, and provides a queryable audit trail.

**Incorrect (in-memory history — lost on restart, no horizontal scaling):**

```typescript
import { ChatMessageHistory } from "langchain/memory";

// BAD: Messages lost when process restarts or user hits different instance
const history = new ChatMessageHistory();
await history.addUserMessage("Hello");
await history.addAIMessage("Hi there!");
```

**Correct (persistent chat history with proper session isolation):**


```typescript
import { AzureCosmosDBNoSQLChatMessageHistory } from "@langchain/azure-cosmosdb";
import { DefaultAzureCredential } from "@azure/identity";
import { RunnableWithMessageHistory } from "@langchain/core/runnables";
import { ChatOpenAI } from "@langchain/openai";

const credential = new DefaultAzureCredential();
```
