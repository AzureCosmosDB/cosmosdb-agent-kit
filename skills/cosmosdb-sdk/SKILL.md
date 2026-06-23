---
name: cosmosdb-sdk
description: |
  Azure Cosmos DB SDK and developer tooling for .NET, Java, Python, Go, and Spring Boot: singleton CosmosClient, async APIs, Direct vs Gateway connection mode, retry/429 handling, preferred and excluded regions, availability strategy, circuit breaker, diagnostics, enum serialization, ETag optimistic concurrency, conditional create, patch counter increment, continuation-token guards, per-call request options, content response on write, Spring Data annotations and repositories, NuGet package setup, Python async deps, emulator SSL, and local development / VS Code tooling.
  USE FOR: reuse CosmosClient as singleton, Direct mode, handle 429 retries, preferred regions, ETag concurrency, atomic patch increment, Spring Boot config, .NET package setup, run the emulator locally, browse data in VS Code.
  DO NOT USE FOR: modeling/partition/index/query (use cosmosdb-data-and-queries); throughput, global, monitoring, security (use cosmosdb-operations); LangChain/LangGraph/vector/full-text search (use cosmosdb-ai-and-search).
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB SDK & Developer Tooling

Best practices for the Azure Cosmos DB SDK across .NET, Java, Python, Go, and Spring Boot, plus local development and emulator tooling.

## When to Apply

Reference these guidelines when configuring the Azure Cosmos DB SDK in .NET, Java, Python, Go, or Spring Boot, or setting up local development tooling.

## Rules

### SDK Best Practices

- [sdk-async-api](rules/sdk-async-api.md) - Use Async APIs for Better Throughput
- [sdk-availability-strategy](rules/sdk-availability-strategy.md) - Configure Threshold-Based Availability Strategy (Hedging)
- [sdk-circuit-breaker](rules/sdk-circuit-breaker.md) - Configure Partition-Level Circuit Breaker
- [sdk-conditional-create-etag](rules/sdk-conditional-create-etag.md) - Use IfNoneMatchETag("*") for conditional creates to prevent duplicates
- [sdk-connection-mode](rules/sdk-connection-mode.md) - Use Direct Connection Mode for Production
- [sdk-continuation-token-null-guard](rules/sdk-continuation-token-null-guard.md) - Guard against empty continuation tokens before calling byPage
- [sdk-diagnostics](rules/sdk-diagnostics.md) - Log Diagnostics for Troubleshooting
- [sdk-dotnet-cosmos-package-id](rules/sdk-dotnet-cosmos-package-id.md) - Use Microsoft.Azure.Cosmos package, not abandoned Azure.Cosmos
- [sdk-dotnet-namespace-collision](rules/sdk-dotnet-namespace-collision.md) - Avoid Microsoft.Azure.Cosmos namespace collisions with domain models
- [sdk-emulator-ssl](rules/sdk-emulator-ssl.md) - Configure SSL and connection mode for Cosmos DB Emulator
- [sdk-etag-concurrency](rules/sdk-etag-concurrency.md) - Use ETags for optimistic concurrency on read-modify-write operations
- [sdk-excluded-regions](rules/sdk-excluded-regions.md) - Configure Excluded Regions for Dynamic Failover
- [sdk-go-partition-key-metadata](rules/sdk-go-partition-key-metadata.md) - Use current Go Cosmos DB SDK versions and explicit partition-key metadata
- [sdk-java-content-response](rules/sdk-java-content-response.md) - Unwrap CosmosItemResponse and enable content response in Java SDK
- [sdk-java-cosmos-config](rules/sdk-java-cosmos-config.md) - Use dependent @Bean methods for Cosmos DB initialization in Spring Boot
- [sdk-java-spring-boot-versions](rules/sdk-java-spring-boot-versions.md) - Spring Boot and Java version compatibility for Cosmos DB SDK
- [sdk-local-dev-config](rules/sdk-local-dev-config.md) - Configure local development environment to avoid cloud connection conflicts
- [sdk-newtonsoft-dependency](rules/sdk-newtonsoft-dependency.md) - Explicitly reference Newtonsoft.Json package
- [sdk-patch-counter-increment](rules/sdk-patch-counter-increment.md) - Use the Patch API for atomic counter increments
- [sdk-preferred-regions](rules/sdk-preferred-regions.md) - Configure Preferred Regions for Availability
- [sdk-python-async-deps](rules/sdk-python-async-deps.md) - Include aiohttp When Using Python Async SDK
- [sdk-request-options-per-call](rules/sdk-request-options-per-call.md) - Never share a single CosmosItemRequestOptions instance across multiple createItem calls
- [sdk-retry-429](rules/sdk-retry-429.md) - Handle 429 Errors with Retry-After
- [sdk-serialization-enums](rules/sdk-serialization-enums.md) - Use consistent enum serialization between Cosmos SDK and application layer
- [sdk-singleton-client](rules/sdk-singleton-client.md) - Reuse CosmosClient as Singleton
- [sdk-spring-data-annotations](rules/sdk-spring-data-annotations.md) - Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs
- [sdk-spring-data-repository](rules/sdk-spring-data-repository.md) - Use CosmosRepository correctly and handle Iterable return types

### Developer Tooling

- [tooling-emulator-setup](rules/tooling-emulator-setup.md) - Use Azure Cosmos DB Emulator for local development and testing
- [tooling-vscode-extension](rules/tooling-vscode-extension.md) - Use Azure Cosmos DB VS Code extension for routine inspection and management
