---
title: Use CosmosRepository correctly and handle Iterable return types
impact: HIGH
impactDescription: prevents ClassCastException and query failures in Spring Data Cosmos repositories
tags: sdk, java, spring-data-cosmos, repository, iterable, pagination, query-methods
---

## Use CosmosRepository correctly and handle Iterable return types

`CosmosRepository` differs from `JpaRepository` in return types, pagination support, and query method conventions. Common pitfalls include casting `Iterable` to `List` directly and using JPA-style pagination.

**Incorrect (JPA repository patterns that fail with Cosmos):**

```java
// JpaRepository extends PagingAndSortingRepository — Cosmos does not
public interface OwnerRepository extends JpaRepository<Owner, Integer> {
    Page<Owner> findByLastNameStartingWith(String lastName, Pageable pageable);
    List<PetType> findPetTypes();
}
```

**Correct (CosmosRepository patterns):**


```java
import com.azure.spring.data.cosmos.repository.CosmosRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OwnerRepository extends CosmosRepository<Owner, String> {
    List<Owner> findByLastNameStartingWith(String lastName); // No Pageable
```

```java
// WRONG — ClassCastException: BlockingIterable cannot be cast to java.util.List
default List<Entity> findAllSorted() {
    return (List<Entity>) this.findAll();
}

// CORRECT — Use StreamSupport to convert
```
