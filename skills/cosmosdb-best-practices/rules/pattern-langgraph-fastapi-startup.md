---
title: Initialize LangGraph Agents in FastAPI Startup with Retry
impact: HIGH
impactDescription: prevents request failures when dependent services are not yet ready
tags: pattern, fastapi, langgraph, startup, async
---

## Initialize LangGraph Agents in FastAPI Startup with Retry

**Impact: HIGH (prevents request failures when dependent services are not yet ready)**

LangGraph agents that depend on external services (MCP servers, Cosmos DB, Azure OpenAI) must be initialized asynchronously during application startup, not at module import time or on first request. Use FastAPI's startup event (or lifespan) with retry logic to handle cases where dependent services take time to become available (e.g., in container orchestration environments where services start in parallel).

**Incorrect (initialize at module level — blocks import, no retry):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# BAD: Runs at import time, fails if MCP server isn't ready yet
client = MultiServerMCPClient({"server": {"transport": "streamable_http", "url": mcp_url}})
tools = asyncio.run(load_tools(client))  # Blocks and may fail
```

**Correct (startup event with retry and fallback):**


```python
import asyncio
from fastapi import FastAPI, HTTPException

app = FastAPI()
_agents_ready = False

```
