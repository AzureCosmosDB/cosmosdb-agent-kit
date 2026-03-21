---
title: Handle JSON serialization correctly for Cosmos DB documents
impact: HIGH
impactDescription: prevents data loss, null constructor errors, and serialization failures
tags: model, serialization, json, jackson, jsonignore, jsonproperty, bigdecimal, jsonignoreproperties, change-feed
---

## Handle JSON Serialization Correctly for Cosmos DB

Cosmos DB stores documents as JSON. Every field on an entity that must be persisted needs to be serializable. Incorrect use of `@JsonIgnore`, missing constructors, or incompatible field types (like `BigDecimal` on JDK 17+) cause silent data loss or runtime failures.

**Incorrect (common serialization mistakes):**

```java
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
    private String partitionKey = "user";

    private String login;

    @JsonIgnore  // ❌ WRONG: Password will NOT be saved to Cosmos DB
    private String password;

    @JsonIgnore  // ❌ WRONG: Authorities will NOT be saved to Cosmos DB
    private Set<String> authorities = new HashSet<>();

    private BigDecimal accountBalance;  // ❌ Fails on JDK 17+ with reflection errors
}
```

**Correct (proper serialization for Cosmos DB):**

```java
@Container(containerName = "users")
public class User {

    @Id
    private String id;

    @PartitionKey
    private String partitionKey = "user";

    private String login;

    // ✅ No @JsonIgnore — field is persisted to Cosmos DB
    private String password;

    // ✅ Use @JsonProperty for explicit field naming, NOT @JsonIgnore
    @JsonProperty("authorities")
    private Set<String> authorities = new HashSet<>();

    // ✅ Use Double instead of BigDecimal for JDK 17+ compatibility
    private Double accountBalance;
}
```

**Rule 1: Never `@JsonIgnore` persisted fields**

`@JsonIgnore` prevents a field from being written to Cosmos DB. This is the #1 cause of "Cannot pass null or empty values to constructor" errors after reading a document back:

```java
// ❌ Data loss: field is not stored in Cosmos
@JsonIgnore
private String password;

// ✅ Field is stored in Cosmos
private String password;

// ✅ Rename in JSON but still store
@JsonProperty("pwd")
private String password;
```

**Only use `@JsonIgnore` on transient/computed fields** that should NOT be stored in Cosmos DB (e.g., hydrated relationship objects — see `model-relationship-references`).

**Rule 2: BigDecimal fails on JDK 17+**

Java 17+ module system restricts reflection access to `BigDecimal` internal fields during Jackson serialization:

```
Unable to make field private final java.math.BigInteger
java.math.BigDecimal.intVal accessible
```

**Solutions (in order of preference):**

1. **Replace with `Double`** — sufficient for most use cases:
   ```java
   private Double amount; // Instead of BigDecimal
   ```

2. **Replace with `String`** — for high-precision requirements:
   ```java
   private String amount; // Store "1500.00"

   public BigDecimal getAmountAsBigDecimal() {
       return new BigDecimal(amount);
   }
   ```

3. **Add JVM argument** — if BigDecimal must be kept:
   ```
   --add-opens java.base/java.math=ALL-UNNAMED
   ```

**Rule 3: Provide a default constructor**

Cosmos DB deserialization requires a no-arg constructor. If you add parameterized constructors, always keep the default:

```java
@Container(containerName = "items")
public class Item {
    // ✅ Default constructor required for deserialization
    public Item() {}

    public Item(String name, Double price) {
        this.name = name;
        this.price = price;
    }
}
```

**Rule 4: Store complex objects as simple types**

For complex Cosmos DB compatibility, prefer simple types over JPA entity references:

```java
// ❌ Complex nested entity — may cause serialization issues
private Set<Authority> authorities;

// ✅ Simple string set — reliable serialization
private Set<String> authorities;
```

Convert between simple and complex types in the service layer, not in the entity.

**Rule 5: Always add `@JsonIgnoreProperties(ignoreUnknown = true)` to entity classes**

Cosmos DB documents contain system metadata fields (`_rid`, `_self`, `_etag`, `_ts`, `_lsn`) that are not part of your entity model. Without this annotation, Jackson throws `UnrecognizedPropertyException` when deserializing documents — especially during Change Feed processing where these fields are always present:

```
com.fasterxml.jackson.databind.exc.UnrecognizedPropertyException:
  Unrecognized field "_lsn" (class PlayerProfile), not marked as ignorable
```

```java
// ❌ Fails on system metadata fields from Cosmos DB
@Container(containerName = "players")
public class PlayerProfile {
    @Id
    private String id;
    private String playerId;
    private int score;
}

// ✅ Ignores unknown fields — safe for Cosmos DB system metadata
@JsonIgnoreProperties(ignoreUnknown = true)
@Container(containerName = "players")
public class PlayerProfile {
    @Id
    private String id;
    private String playerId;
    private int score;
}
```

This is critical for Change Feed consumers where system metadata fields are always included in the document payload.

Reference: [Jackson annotations guide](https://github.com/FasterXML/jackson-annotations/wiki/Jackson-Annotations)
