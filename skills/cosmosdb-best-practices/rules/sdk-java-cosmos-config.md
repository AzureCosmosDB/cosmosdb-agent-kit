---
title: Use dependent @Bean methods for Cosmos DB initialization in Spring Boot
impact: HIGH
impactDescription: prevents circular dependency, startup failures, class name collisions, and compile errors
tags: sdk, java, spring-boot, configuration, cosmos-config, bean, postconstruct, AbstractCosmosConfiguration
---

## Use dependent @Bean methods for Cosmos DB initialization in Spring Boot

Use dependent `@Bean` methods with parameter injection instead of `@PostConstruct`. Calling a `@Bean` method from `@PostConstruct` creates a circular dependency crash.

**Incorrect (@PostConstruct calling @Bean — circular dependency):**

```java
@Configuration
public class CosmosDbConfig {
    @Bean
    public CosmosClient cosmosClient() { return new CosmosClientBuilder()...; }

    @PostConstruct  // ❌ Calls cosmosClient() which is a @Bean — circular!
```

**Correct (dependent @Bean chain):**


```java
@Configuration
public class CosmosDbConfig {
    @Value("${azure.cosmos.endpoint}") private String endpoint;
    @Value("${azure.cosmos.key}") private String key;
    @Value("${azure.cosmos.database}") private String databaseName;

```

```java
@Configuration
@EnableCosmosRepositories
public class CosmosDbConfig extends AbstractCosmosConfiguration {
    @Bean  // ✅ Not @Override — declare as a bean
    public CosmosClientBuilder cosmosClientBuilder() {
        return new CosmosClientBuilder().endpoint(endpoint).key(key)
```
