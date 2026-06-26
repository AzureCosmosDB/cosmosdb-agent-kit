---
title: Use StateGraph with Conditional Edges for Multi-Agent Routing
impact: HIGH
impactDescription: enables deterministic agent hand-off in multi-agent LangGraph applications
tags: pattern, langgraph, multi-agent, routing, cosmos-db
---

## Use StateGraph with Conditional Edges for Multi-Agent Routing

**Impact: HIGH (enables deterministic agent hand-off in multi-agent LangGraph applications)**

When building multi-agent systems with LangGraph backed by Cosmos DB checkpointing, use `StateGraph` with `add_conditional_edges` to route between agents based on tool call results or persisted state. Each agent node should return a `Command` that updates state and directs the graph to the next node (e.g., a human-input node).

**Incorrect (linear chain — no dynamic routing between agents):**

```python
from langgraph.graph import StateGraph, START, MessagesState

builder = StateGraph(MessagesState)
builder.add_node("agent_a", call_agent_a)
builder.add_node("agent_b", call_agent_b)

# BAD: Fixed linear flow — cannot route dynamically
```

**Correct (conditional edges with dynamic routing):**


```python
from typing import Literal
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.types import Command
from langchain_azure_cosmosdb import CosmosDBSaver

async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "human"]]:
    response = await agent_a.ainvoke(state)
```

```python
async def call_agent_a(state: MessagesState, config) -> Command[Literal["agent_a", "agent_b", "human"]]:
    response = await agent_a.ainvoke(state)

    # CRITICAL: Only check NEW messages added by this invocation
    existing_count = len(state.get("messages", []))
    new_messages = response.get("messages", [])[existing_count:]

```
