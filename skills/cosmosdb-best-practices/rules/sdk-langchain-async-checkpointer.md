---
title: Initialize Async Cosmos DB Container Before CosmosDBSaver
impact: HIGH
impactDescription: prevents credential and event-loop errors in async applications
tags: sdk, python, async, langchain, checkpointing
---

## Initialize Async Cosmos DB Container Before CosmosDBSaver

**Impact: HIGH (prevents credential and event-loop errors in async applications)**

When using `CosmosDBSaver` with the async Cosmos DB SDK, the container client must be created within an active async context (e.g., inside an `async def` function). Creating it at module level causes event-loop errors because the async credential and client require a running loop.

**Incorrect (module-level initialization — event loop not running):**

```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver

# BAD: No event loop running at module import time
credential = AsyncDefaultAzureCredential()
```

**Correct (initialize in async startup function):**


```python
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.identity.aio import DefaultAzureCredential as AsyncDefaultAzureCredential
from langchain_azure_cosmosdb import CosmosDBSaver
from langgraph.graph import StateGraph, MessagesState

builder = StateGraph(MessagesState)
```
