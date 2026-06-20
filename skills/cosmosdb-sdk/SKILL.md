---
name: cosmosdb-sdk
description: |
  Azure Cosmos DB SDK best practices for .NET, Java, Python, Spring Boot, and
  LangChain: singleton client, async APIs, connection modes, retry handling,
  diagnostics, serialization, emulator configuration, ETags, circuit breaker,
  availability strategy, and framework-specific patterns.
  USE FOR: CosmosClient singleton, async API, Direct vs Gateway mode, retry 429,
  preferred regions, excluded regions, availability strategy, circuit breaker,
  SDK diagnostics, serialization enums, emulator SSL, ETag concurrency,
  conditional create, patch increment, continuation token, content response,
  Spring Data Cosmos, Spring Boot versions, Newtonsoft dependency, namespace collision,
  Python async deps, local dev config, LangChain Cosmos DB saver, LangGraph checkpointer,
  MCP persistent session, MCP tool content format, MCP tool filtering,
  LangChain JS vectorstore, LangChain JS chat history, LangChain JS semantic cache,
  RAG API, RAG pipeline, RAG application, vector store client for RAG, embedding ingestion.
  COMPANION SKILLS: for RAG API tasks, apply this skill together with
  cosmosdb-vector-search (vector index + VectorDistance retrieval) and
  cosmosdb-design-patterns (retrieval orchestration and grounding).
  DO NOT USE FOR: data modeling (use cosmosdb-data-modeling), queries (use cosmosdb-query-optimization),
  partition keys (use cosmosdb-partition-key).

license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB SDK Best Practices

SDK usage patterns and framework-specific guidance for Azure Cosmos DB across .NET, Java, Python, Spring Boot, and LangChain.

## When to Apply

Reference these guidelines when:
- Configuring CosmosClient instances
- Choosing connection modes (Direct vs Gateway)
- Handling retries and throttling
- Setting up the Cosmos DB Emulator
- Using ETags for optimistic concurrency
- Integrating with Spring Boot or LangChain
- Configuring availability and resilience features

## Rules

- [sdk-singleton-client](rules/sdk-singleton-client.md) - Reuse CosmosClient as singleton
- [sdk-async-api](rules/sdk-async-api.md) - Use async APIs for throughput
- [sdk-retry-429](rules/sdk-retry-429.md) - Handle 429s with retry-after
- [sdk-connection-mode](rules/sdk-connection-mode.md) - Use Direct mode for production
- [sdk-preferred-regions](rules/sdk-preferred-regions.md) - Configure preferred regions
- [sdk-excluded-regions](rules/sdk-excluded-regions.md) - Exclude regions experiencing issues
- [sdk-availability-strategy](rules/sdk-availability-strategy.md) - Configure availability strategy
- [sdk-circuit-breaker](rules/sdk-circuit-breaker.md) - Use circuit breaker for fault tolerance
- [sdk-diagnostics](rules/sdk-diagnostics.md) - Log diagnostics for troubleshooting
- [sdk-serialization-enums](rules/sdk-serialization-enums.md) - Serialize enums as strings
- [sdk-emulator-ssl](rules/sdk-emulator-ssl.md) - Configure SSL for Cosmos DB Emulator
- [sdk-etag-concurrency](rules/sdk-etag-concurrency.md) - Use ETags for optimistic concurrency
- [sdk-conditional-create-etag](rules/sdk-conditional-create-etag.md) - Reject duplicates atomically
- [sdk-request-options-per-call](rules/sdk-request-options-per-call.md) - Never reuse request options
- [sdk-patch-counter-increment](rules/sdk-patch-counter-increment.md) - Use patch incr for atomic counters
- [sdk-continuation-token-null-guard](rules/sdk-continuation-token-null-guard.md) - Guard empty continuation tokens
- [sdk-java-content-response](rules/sdk-java-content-response.md) - Enable content response on writes (Java)
- [sdk-java-cosmos-config](rules/sdk-java-cosmos-config.md) - Configure Cosmos DB in Spring Boot
- [sdk-java-spring-boot-versions](rules/sdk-java-spring-boot-versions.md) - Match Java to Spring Boot versions
- [sdk-local-dev-config](rules/sdk-local-dev-config.md) - Configure local development
- [sdk-dotnet-cosmos-package-id](rules/sdk-dotnet-cosmos-package-id.md) - Use correct NuGet package
- [sdk-newtonsoft-dependency](rules/sdk-newtonsoft-dependency.md) - Reference Newtonsoft.Json explicitly
- [sdk-python-async-deps](rules/sdk-python-async-deps.md) - Include aiohttp for Python async
- [sdk-spring-data-annotations](rules/sdk-spring-data-annotations.md) - Annotate entities for Spring Data
- [sdk-spring-data-repository](rules/sdk-spring-data-repository.md) - Use CosmosRepository correctly
- [sdk-dotnet-namespace-collision](rules/sdk-dotnet-namespace-collision.md) - Avoid namespace collisions
- [sdk-langchain-cosmosdb-saver](rules/sdk-langchain-cosmosdb-saver.md) - CosmosDBSaver for LangGraph
- [sdk-langchain-async-checkpointer](rules/sdk-langchain-async-checkpointer.md) - Async container init
- [sdk-langchain-mcp-persistent-session](rules/sdk-langchain-mcp-persistent-session.md) - Persistent MCP sessions
- [sdk-langchain-mcp-tool-content-format](rules/sdk-langchain-mcp-tool-content-format.md) - MCP tool content format
- [sdk-langgraph-mcp-tool-filtering](rules/sdk-langgraph-mcp-tool-filtering.md) - Filter MCP tools by prefix
- [sdk-langchain-js-vectorstore-init](rules/sdk-langchain-js-vectorstore-init.md) - LangChain JS vectorstore init
- [sdk-langchain-js-chat-history](rules/sdk-langchain-js-chat-history.md) - LangChain JS chat history
- [sdk-langchain-js-embedding-model](rules/sdk-langchain-js-embedding-model.md) - LangChain JS embedding model
- [sdk-langchain-js-filter-injection](rules/sdk-langchain-js-filter-injection.md) - LangChain JS filter injection
- [sdk-langchain-js-fulltext-prerequisites](rules/sdk-langchain-js-fulltext-prerequisites.md) - LangChain JS FTS prerequisites
- [sdk-langchain-js-managed-identity](rules/sdk-langchain-js-managed-identity.md) - LangChain JS managed identity
- [sdk-langchain-js-search-types](rules/sdk-langchain-js-search-types.md) - LangChain JS search types
- [sdk-langchain-js-semantic-cache](rules/sdk-langchain-js-semantic-cache.md) - LangChain JS semantic cache

## Full Compiled Document

For all rules expanded: [AGENTS.md](AGENTS.md)
