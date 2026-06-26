---
title: Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs
impact: CRITICAL
impactDescription: prevents startup failures and data access errors in Spring Data Cosmos applications
tags: sdk, java, spring-boot, spring-data-cosmos, annotations, container, partition-key, entity
---

## Annotate entities for Spring Data Cosmos with @Container, @PartitionKey, and String IDs

Spring Data Cosmos requires specific annotations on entity classes. JPA annotations (`@Entity`, `@Table`, `@Column`, `@JoinColumn`) are not recognized.

**Incorrect (JPA annotations — not recognized by Cosmos):**

```java
import jakarta.persistence.*;

@Entity
@Table(name = "owners")
public class Owner {

    @Id
```

**Correct (Spring Data Cosmos annotations):**


```java
import com.azure.spring.data.cosmos.core.mapping.Container;
import com.azure.spring.data.cosmos.core.mapping.PartitionKey;
import com.azure.spring.data.cosmos.core.mapping.GeneratedValue;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.data.annotation.Id;

@JsonIgnoreProperties(ignoreUnknown = true)
```

```java
// Wrong: Integer IDs don't work with CosmosRepository<Entity, String>
   private Integer id;

   // Correct: Always use String IDs
   @Id
   @GeneratedValue
   private String id;
```
