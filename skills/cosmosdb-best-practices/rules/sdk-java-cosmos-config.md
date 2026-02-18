---
title: Use dependent @Bean methods for Cosmos DB initialization in Spring Boot
impact: HIGH
impactDescription: prevents circular dependency and startup failures
tags: sdk, java, spring-boot, configuration, cosmos-config, bean, postconstruct
---

## Use Dependent @Bean Methods for Cosmos DB Initialization in Spring Boot

When configuring `CosmosClient`, `CosmosDatabase`, and `CosmosContainer` beans in a Spring Boot `@Configuration` class, use dependent `@Bean` methods with parameter injection instead of `@PostConstruct`. Calling a `@Bean` method from `@PostConstruct` in the same class creates a circular dependency that crashes the application on startup.

**Incorrect (@PostConstruct calling @Bean — circular dependency):**

```java
// ❌ Anti-pattern: @PostConstruct + @Bean in same class causes circular dependency
@Configuration
public class CosmosConfig {

    @Value("${azure.cosmos.endpoint}")
    private String endpoint;

    @Value("${azure.cosmos.key}")
    private String key;

    @Bean
    public CosmosClient cosmosClient() {
        return new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key)
            .consistencyLevel(ConsistencyLevel.SESSION)
            .buildClient();
    }

    @PostConstruct  // ❌ This calls cosmosClient() which is a @Bean — circular!
    public void initializeDatabase() {
        CosmosClient client = cosmosClient(); // Triggers proxy interception loop
        client.createDatabaseIfNotExists("mydb");
        CosmosDatabase db = client.getDatabase("mydb");
        db.createContainerIfNotExists(
            new CosmosContainerProperties("items", "/partitionKey"),
            ThroughputProperties.createAutoscaledThroughput(4000));
    }

    @Bean
    public CosmosDatabase cosmosDatabase() {
        return cosmosClient().getDatabase("mydb");
    }

    @Bean
    public CosmosContainer cosmosContainer() {
        return cosmosDatabase().getContainer("items");
    }
}
// Runtime error: BeanCurrentlyInCreationException — circular dependency detected
```

**Correct (dependent @Bean chain with parameter injection):**

```java
// ✅ Correct: Use @Bean dependency injection chain — initialization in bean methods
@Configuration
public class CosmosConfig {

    @Value("${azure.cosmos.endpoint}")
    private String endpoint;

    @Value("${azure.cosmos.key}")
    private String key;

    @Value("${azure.cosmos.database}")
    private String databaseName;

    @Value("${azure.cosmos.container}")
    private String containerName;

    @Bean(destroyMethod = "close")
    public CosmosClient cosmosClient() {
        DirectConnectionConfig directConfig = DirectConnectionConfig.getDefaultConfig();
        GatewayConnectionConfig gatewayConfig = GatewayConnectionConfig.getDefaultConfig();

        // Use Gateway for emulator, Direct for production
        CosmosClientBuilder builder = new CosmosClientBuilder()
            .endpoint(endpoint)
            .key(key)
            .consistencyLevel(ConsistencyLevel.SESSION)
            .contentResponseOnWriteEnabled(true);

        if (endpoint.contains("localhost") || endpoint.contains("127.0.0.1")) {
            builder.gatewayMode(gatewayConfig);
        } else {
            builder.directMode(directConfig);
        }

        return builder.buildClient();
    }

    @Bean  // ✅ Spring injects cosmosClient from the bean above
    public CosmosDatabase cosmosDatabase(CosmosClient cosmosClient) {
        // Database initialization happens here — no @PostConstruct needed
        cosmosClient.createDatabaseIfNotExists(databaseName);
        return cosmosClient.getDatabase(databaseName);
    }

    @Bean  // ✅ Spring injects cosmosDatabase from the bean above
    public CosmosContainer cosmosContainer(CosmosDatabase cosmosDatabase) {
        CosmosContainerProperties props = new CosmosContainerProperties(
            containerName, "/partitionKey");

        cosmosDatabase.createContainerIfNotExists(
            props,
            ThroughputProperties.createAutoscaledThroughput(4000));

        return cosmosDatabase.getContainer(containerName);
    }
}
```

**Why this works:**
- Spring resolves the dependency graph: `cosmosClient()` → `cosmosDatabase(CosmosClient)` → `cosmosContainer(CosmosDatabase)`
- Database and container creation happens naturally during bean initialization
- No circular reference because each method receives its dependency as a parameter
- `destroyMethod = "close"` ensures `CosmosClient` is properly shut down

**With Hierarchical Partition Keys:**

```java
@Bean
public CosmosContainer cosmosContainer(CosmosDatabase cosmosDatabase) {
    // Hierarchical partition key definition
    List<String> partitionKeyPaths = Arrays.asList(
        "/tenantId", "/type", "/projectId");

    CosmosContainerProperties props = new CosmosContainerProperties(
        containerName,
        partitionKeyPaths,
        PartitionKeyDefinitionVersion.V2,
        PartitionKind.MULTI_HASH);

    cosmosDatabase.createContainerIfNotExists(
        props,
        ThroughputProperties.createAutoscaledThroughput(4000));

    return cosmosDatabase.getContainer(containerName);
}
```

**Alternative: `SmartInitializingSingleton` for post-init logic:**

```java
// If you need to run logic AFTER all beans are created
@Bean
public SmartInitializingSingleton cosmosInitializer(CosmosContainer container) {
    return () -> {
        // Seed data, verify connectivity, warm up, etc.
        logger.info("Cosmos container ready: {}", container.getId());
    };
}
```

**Key Points:**
- Never call `@Bean` methods from `@PostConstruct` in the same `@Configuration` class
- Use parameter injection in `@Bean` methods to express initialization order
- Always set `destroyMethod = "close"` on `CosmosClient` bean
- Keep `CosmosClient` as a singleton `@Bean` (Rule 4.16)
- Set `contentResponseOnWriteEnabled(true)` in the builder (Rule 4.9)

Reference: [Spring Framework @Bean documentation](https://docs.spring.io/spring-framework/reference/core/beans/java/bean-annotation.html)
