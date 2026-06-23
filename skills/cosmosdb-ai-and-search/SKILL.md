---
name: cosmosdb-ai-and-search
description: |
  Azure Cosmos DB for AI, RAG, and search: vector search (vector index types, embeddings container setup, similarity / nearest-neighbor queries), full-text search (enable FTS, BM25 relevance ranking, hybrid keyword + vector), LangChain and LangGraph integration (CosmosDB checkpoint saver, async checkpointer init, MCP persistent sessions, MCP tool content and filtering, LangChain JS vectorstore, chat history, embedding model, semantic cache), and AI-agent design patterns (multi-agent routing, chat-history separation, resume from checkpoint, grounding access, background-task writes).
  USE FOR: store embeddings and run similarity search, choose a vector index, enable full-text/BM25 search, hybrid search, build a RAG app, persist LangGraph checkpoints, multi-agent state, MCP tools, semantic cache.
  DO NOT USE FOR: core modeling/partition/index/query (use cosmosdb-data-and-queries); throughput/global/monitoring/security (use cosmosdb-operations); non-AI SDK client setup (use cosmosdb-sdk).
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB for AI, RAG & Search

Best practices for AI, RAG, and search on Azure Cosmos DB: vector search, full-text search, LangChain/LangGraph integration, and AI-agent design patterns.

## When to Apply

Reference these guidelines when building RAG or AI-agent applications on Azure Cosmos DB with vector search, full-text search, or LangChain/LangGraph.

## Rules

### Vector Search

- [vector-distance-query](rules/vector-distance-query.md) - Use VectorDistance for Similarity Search
- [vector-embedding-policy](rules/vector-embedding-policy.md) - Define Vector Embedding Policy
- [vector-enable-feature](rules/vector-enable-feature.md) - Enable Vector Search Feature on Account
- [vector-index-type](rules/vector-index-type.md) - Configure Vector Indexes in Indexing Policy
- [vector-normalize-embeddings](rules/vector-normalize-embeddings.md) - Normalize Embeddings for Cosine Similarity
- [vector-repository-pattern](rules/vector-repository-pattern.md) - Implement Repository Pattern for Vector Search

### Full-Text Search

- [fts-add-index](rules/fts-add-index.md) - Add Full-Text Index in the Indexing Policy
- [fts-define-policy](rules/fts-define-policy.md) - Define Full-Text Policy on the Container
- [fts-enable-capability](rules/fts-enable-capability.md) - Enable Full-Text Search Capability on Account
- [fts-hybrid-queries](rules/fts-hybrid-queries.md) - Combine FTS predicates with range or equality filters for hybrid queries
- [fts-keyword-matching](rules/fts-keyword-matching.md) - Use FullTextContains for keyword matching on indexed text fields
- [fts-relevance-ranking](rules/fts-relevance-ranking.md) - Use FullTextScore with ORDER BY RANK for BM25 relevance ranking

### SDK Best Practices

- [sdk-langchain-async-checkpointer](rules/sdk-langchain-async-checkpointer.md) - Initialize Async Cosmos DB Container Before CosmosDBSaver
- [sdk-langchain-cosmosdb-saver](rules/sdk-langchain-cosmosdb-saver.md) - Use CosmosDBSaver for LangGraph Checkpointing
- [sdk-langchain-js-chat-history](rules/sdk-langchain-js-chat-history.md) - Use AzureCosmosDBNoSQLChatMessageHistory for Persistent Conversations in JS/TS
- [sdk-langchain-js-embedding-model](rules/sdk-langchain-js-embedding-model.md) - Configure Azure OpenAI Embedding Deployment Name for JS/TS LangChain
- [sdk-langchain-js-filter-injection](rules/sdk-langchain-js-filter-injection.md) - Prevent Filter Injection in JS/TS LangChain Vector Store Queries
- [sdk-langchain-js-fulltext-prerequisites](rules/sdk-langchain-js-fulltext-prerequisites.md) - Configure Full-Text Prerequisites Before JS/TS LangChain Hybrid Search
- [sdk-langchain-js-managed-identity](rules/sdk-langchain-js-managed-identity.md) - Use Managed Identity for JS/TS LangChain Cosmos DB Integration
- [sdk-langchain-js-search-types](rules/sdk-langchain-js-search-types.md) - Choose the Correct Search Type for JS/TS LangChain Vector Store
- [sdk-langchain-js-semantic-cache](rules/sdk-langchain-js-semantic-cache.md) - Use AzureCosmosDBNoSQLSemanticCache for LLM Cost Reduction in JS/TS
- [sdk-langchain-js-vectorstore-init](rules/sdk-langchain-js-vectorstore-init.md) - Correctly Initialize AzureCosmosDBNoSQLVectorStore in JavaScript/TypeScript
- [sdk-langchain-mcp-persistent-session](rules/sdk-langchain-mcp-persistent-session.md) - Use Persistent MCP Client Sessions for Multi-Agent Applications
- [sdk-langchain-mcp-tool-content-format](rules/sdk-langchain-mcp-tool-content-format.md) - Handle MCP ToolMessage Content Format Variations
- [sdk-langgraph-mcp-tool-filtering](rules/sdk-langgraph-mcp-tool-filtering.md) - Filter MCP Tools by Name Prefix for Agent Assignment

### Design Patterns

- [pattern-ai-grounding-access](rules/pattern-ai-grounding-access.md) - Use Point Reads for AI-Grounding and RAG Retrieval When ID Is Known
- [pattern-background-task-writes](rules/pattern-background-task-writes.md) - Use Background Tasks for Non-Blocking Chat History Storage
- [pattern-langgraph-agent-name-attribution](rules/pattern-langgraph-agent-name-attribution.md) - Tag AI Messages with Agent Name for API Response Attribution
- [pattern-langgraph-agent-routing-cosmosdb](rules/pattern-langgraph-agent-routing-cosmosdb.md) - Persist Active Agent in Cosmos DB for Deterministic Routing
- [pattern-langgraph-async-cosmos-routing](rules/pattern-langgraph-async-cosmos-routing.md) - Wrap Cosmos DB Sync Calls in asyncio.to_thread for LangGraph Routing Functions
- [pattern-langgraph-async-cosmos-writes](rules/pattern-langgraph-async-cosmos-writes.md) - Use asyncio.to_thread for Active Agent Writes in LangGraph Node Functions
- [pattern-langgraph-chat-history-separate](rules/pattern-langgraph-chat-history-separate.md) - Store Chat History Separately from LangGraph Checkpoints
- [pattern-langgraph-fastapi-startup](rules/pattern-langgraph-fastapi-startup.md) - Initialize LangGraph Agents in FastAPI Startup with Retry
- [pattern-langgraph-interrupt-human](rules/pattern-langgraph-interrupt-human.md) - Use LangGraph Interrupt for Human-in-the-Loop Confirmation
- [pattern-langgraph-multi-agent](rules/pattern-langgraph-multi-agent.md) - Use StateGraph with Conditional Edges for Multi-Agent Routing
- [pattern-langgraph-resume-checkpoint](rules/pattern-langgraph-resume-checkpoint.md) - Resume LangGraph from Checkpoint After Interrupt
