---
title: Use CosmosDBSaver for LangGraph Checkpointing
impact: HIGH
impactDescription: enables persistent multi-turn conversation state across restarts
tags: sdk, python, langgraph, checkpointing, langchain
---

## Use CosmosDBSaver for LangGraph Checkpointing

**Impact: HIGH (enables persistent multi-turn conversation state across restarts)**

When building LangGraph agents that require multi-turn conversation persistence, use `CosmosDBSaver` from `langchain-azure-cosmosdb` as the checkpointer. This stores graph state in Cosmos DB, enabling conversations to survive process restarts and scale across multiple instances.

**Incorrect (using in-memory checkpointer — state lost on restart):**

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
# ... add nodes and edges ...

```

**Correct (async container client with CosmosDBSaver):**


```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
```
