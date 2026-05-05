---
title: Use Persistent MCP Client Sessions for Multi-Agent Applications
impact: HIGH
impactDescription: prevents session initialization overhead and connection churn
tags: sdk, python, mcp, session, langchain
---

## Use Persistent MCP Client Sessions for Multi-Agent Applications

**Impact: HIGH (prevents session initialization overhead and connection churn)**

When using `MultiServerMCPClient` with LangGraph agents, maintain a single persistent session for the lifetime of your application rather than creating a new session per request. MCP sessions involve transport negotiation, tool discovery, and server handshakes. Creating a session per request adds latency and may exhaust server connection limits.

**Incorrect (new session per request — high overhead):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

async def handle_request(user_input):
    client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": "http://localhost:8080/mcp"}
    })
    # BAD: Creates and tears down a session for every single request
    async with client.session("my_server") as session:
        tools = await load_mcp_tools(session)
        # ... invoke agent ...
    # Session closed, next request pays setup cost again
```

**Correct (persistent session initialized once at startup):**

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

_mcp_client = None
_session_context = None
_persistent_session = None

async def setup_mcp():
    """Call once during application startup."""
    global _mcp_client, _session_context, _persistent_session

    _mcp_client = MultiServerMCPClient({
        "my_server": {"transport": "streamable_http", "url": mcp_server_url}
    })
    _session_context = _mcp_client.session("my_server")
    _persistent_session = await _session_context.__aenter__()

    # Load tools once — they remain valid for the session lifetime
    tools = await load_mcp_tools(_persistent_session)
    return tools

async def cleanup_mcp():
    """Call during application shutdown."""
    global _session_context, _persistent_session
    if _session_context and _persistent_session:
        await _session_context.__aexit__(None, None, None)
        _session_context = None
        _persistent_session = None
```

**Tip:** Wrap the session setup in retry logic with exponential backoff for production deployments where the MCP server may take time to become ready.

Reference: [langchain-mcp-adapters documentation](https://github.com/langchain-ai/langchain-mcp-adapters)
