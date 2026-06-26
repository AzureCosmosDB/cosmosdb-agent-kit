---
title: Use ID references with transient hydration for document relationships
impact: HIGH
impactDescription: enables correct relationship handling without JOINs while preserving UI/API object access
tags: model, relationships, references, transient, hydration, jsonignore
---

## Use ID references with transient hydration for document relationships

Cosmos DB has no cross-document JOINs. When entities need to reference each other, store relationship IDs as persistent fields and use transient (`@JsonIgnore`) properties for hydrated object access.

**Incorrect (JPA relationship annotations — no Cosmos equivalent):**

```java
@Entity
public class Vet {
    @Id
    private Integer id;

    @ManyToMany
```

**Correct (ID references + transient hydration):**


```java
@Container(containerName = "vets")
public class Vet {

    @Id
    @GeneratedValue
    private String id;
```
