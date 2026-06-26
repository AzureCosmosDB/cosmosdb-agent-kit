---
title: Filter MCP Tools by Name Prefix for Agent Assignment
impact: MEDIUM
impactDescription: reduces agent confusion and improves routing accuracy
tags: sdk, python, mcp, langchain, multi-agent
---

## Filter MCP Tools by Name Prefix for Agent Assignment

**Impact: MEDIUM (reduces agent confusion and improves routing accuracy)**

When a single MCP server exposes tools for multiple domains, assign each LangGraph agent only the subset of tools it needs. Use a name-prefix convention on the server side (e.g., `get_transaction_history`, `get_offer_information`, `transfer_to_sales_agent`) and filter client-side by prefix.

**Incorrect (all agents receive all tools):**

```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

# BAD: Every agent sees every tool — leads to wrong tool calls
```

**Correct (filter tools by prefix per agent):**


```python
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

all_tools = await load_mcp_tools(session)

def filter_tools_by_prefix(tools, prefixes):
```
