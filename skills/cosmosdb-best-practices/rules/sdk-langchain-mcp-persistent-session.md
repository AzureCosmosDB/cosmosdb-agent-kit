---
title: Use Persistent MCP Client Sessions for Multi-Agent Applications
impact: HIGH
impactDescription: prevents session initialization overhead and connection churn
tags: sdk, python, mcp, session, langchain
---

## Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH (prevents session initialization overhead and connection churn)**

When using `MultiServerMCPClient` with LangGraph agents, avoid creating a new client instance per request. MCP sessions involve transport negotiation, tool discovery, and server handshakes.

**Incorrect (new client per request — high overhead, applies to all versions):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async def handle_request(user_input):
    # BAD: Creates a new client (and underlying sessions) for every single request
    client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": "http://localhost:8080/mcp"}
```

**Correct (>= 0.2.0 — single client instance, get_tools() manages sessions internally):**


```python
from langchain_mcp_adapters.client import MultiServerMCPClient

_mcp_client: MultiServerMCPClient | None = None

async def setup_mcp():
    """Call once during application startup."""
```

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

_mcp_client = None
_session_context = None
_persistent_session = None
```
