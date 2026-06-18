# Azure Cosmos DB Best Practices

**Version 1.0.0**  
CosmosDB Agent Kit  
June 2026

> **Note:**  
> This document is primarily for agents and LLMs to follow when maintaining,  
> generating, or refactoring Azure Cosmos DB application code.

---

## Abstract

Best practices for Azure Cosmos DB full-text search: enabling the capability, defining full-text policies, configuring indexes, keyword matching functions, BM25 relevance ranking, and hybrid queries.

---

## Table of Contents

1. [Full-Text Search](#1-full-text-search) — **HIGH**
   - 1.1 [Add Full-Text Index in the Indexing Policy](#11-add-full-text-index-in-the-indexing-policy)
   - 1.2 [Define Full-Text Policy on the Container](#12-define-full-text-policy-on-the-container)
   - 1.3 [Enable Full-Text Search Capability on Account](#13-enable-full-text-search-capability-on-account)
   - 1.4 [Combine FTS predicates with range or equality filters for hybrid queries](#14-combine-fts-predicates-with-range-or-equality-filters-for-hybrid-queries)
   - 1.5 [Use FullTextContains for keyword matching on indexed text fields](#15-use-fulltextcontains-for-keyword-matching-on-indexed-text-fields)
   - 1.6 [Use FullTextScore with ORDER BY RANK for BM25 relevance ranking](#16-use-fulltextscore-with-order-by-rank-for-bm25-relevance-ranking)

---

## 1. Full-Text Search

**Impact: HIGH**

### 1.1 Add Full-Text Index in the Indexing Policy

**Impact: HIGH** (without the index, FTS functions fall back to a full scan)

## Add Full-Text Index in the Indexing Policy

**Impact: HIGH (without the index, FTS functions fall back to a full scan)**

The `fullTextIndexes` array in the `indexingPolicy` tells Cosmos DB to build an inverted index for the corresponding path. This is separate from the range index — a field can have both. Fields covered by a full-text index should **not** also appear in `excludedPaths`.

**Incorrect (field excluded from range index but no FTS index — slow scan):**

```bicep
excludedPaths: [
  { path: '/description/?' }   // excluded from range index...
]                               // ...but no fullTextIndexes entry → full scan
```

**Correct (Bicep):**

```bicep
indexingPolicy: {
  indexingMode: 'consistent'
  includedPaths: [
    { path: '/name/?' }
    { path: '/userid/?' }
  ]
  excludedPaths: [
    { path: '/*' }             // root wildcard
    // description NOT listed here — managed by FTS index below
  ]
  #disable-next-line BCP037
  fullTextIndexes: [
    { path: '/description' }   // inverted index — case-insensitive, tokenized
  ]
}
```

> A field under `fullTextIndexes` incurs **extra write RU** for index maintenance. Only index fields that are actually queried with `FullTextContains` or `FullTextScore`.

Reference: [Indexing policy for full-text search](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 1.2 Define Full-Text Policy on the Container

**Impact: HIGH** (required for tokenizer and stop-word configuration)

## Define Full-Text Policy on the Container

**Impact: HIGH (required for tokenizer and stop-word configuration)**

The `fullTextPolicy` declares which paths are full-text searchable and their language. Supported languages: `en-US`, `de-DE` (preview), `fr-FR` (preview), `it-IT` (preview), `pt-BR` (preview), `pt-PT` (preview), `es-ES` (preview). Language codes are **case-sensitive** — use the exact casing shown (e.g., `en-US` not `en-us`).

**Incorrect (wrong language casing causes ARM BadRequest):**

```bicep
fullTextPolicy: {
  defaultLanguage: 'en-us'       // ❌ lowercase — rejected by ARM
  fullTextPaths: [
    { path: '/description', language: 'en-us' }  // ❌
  ]
}
```

**Correct (Bicep):**

```bicep
#disable-next-line BCP037
fullTextPolicy: {
  defaultLanguage: 'en-US'       // ✅ exact casing required
  fullTextPaths: [
    {
      path: '/description'
      language: 'en-US'          // ✅
    }
  ]
}
```

**Correct — Java SDK (container creation):**

```java
FullTextPolicy ftsPolicy = new FullTextPolicy()
    .setDefaultLanguage("en-US")
    .setFullTextPaths(List.of(
        new FullTextPath().setPath("/description").setLanguage("en-US")
    ));

CosmosContainerProperties props = new CosmosContainerProperties("videos", "/videoid");
props.setFullTextPolicy(ftsPolicy);
database.createContainerIfNotExists(props).block();
```

Reference: [Configure full-text policy](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 1.3 Enable Full-Text Search Capability on Account

**Impact: HIGH** (prerequisite — FTS SQL functions fail without it)

## Enable Full-Text Search Capability on Account

**Impact: HIGH (prerequisite — FTS SQL functions fail without it)**

Full-text search is an opt-in account-level capability. The SQL functions `FullTextContains`, `FullTextContainsAll`, `FullTextContainsAny`, and `FullTextScore` all return an error if this capability is not enabled.

**Incorrect (capability absent — FTS queries fail at runtime):**

```sql
-- This query fails with "Function 'FullTextContains' is not supported"
-- when EnableNoSQLFullTextSearch capability is missing on the account
SELECT * FROM c WHERE FullTextContains(c.description, 'cosmos')
```

**Correct — enable via Azure CLI:**

```bash
az cosmosdb update \
  --resource-group <rg> \
  --name <account-name> \
  --capabilities EnableNoSQLFullTextSearch
```

**Correct — enable via Bicep (account resource):**

```bicep
resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: cosmosAccountName
  properties: {
    // ... other properties ...
    capabilities: [
      { name: 'EnableNoSQLFullTextSearch' }
    ]
  }
}
```

> **Note:** As of Bicep type library v0.41, `fullTextIndexes` and `fullTextPolicy` may emit `BCP037` warnings. Suppress with `#disable-next-line BCP037` — the properties are valid at the ARM REST API level.

Reference: [Full-text search in Azure Cosmos DB](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 1.4 Combine FTS predicates with range or equality filters for hybrid queries

**Impact: MEDIUM** (avoids full-container scans when combined with equality/range filters)

## Combine FTS with Range Filters for Hybrid Queries

**Impact: MEDIUM (avoids full-container scans when combined with equality/range filters)**

FTS predicates can be combined with standard SQL predicates. Cosmos DB uses the most selective predicate first. Put the most restrictive filter (e.g., equality on a high-cardinality property) before the FTS predicate to reduce the candidate set.

**Incorrect (FTS-only query — no range filters, scans all partitions):**

```sql
-- ❌ No equality filter — Cosmos DB must scan every partition before ranking
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

**Correct — filter by partition + FTS:**

```sql
SELECT * FROM c
WHERE c.type = 'video'
  AND c.userid = @userid
  AND FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
// Hybrid: exact field filters narrow partition, FTS ranks within results
String sql = "SELECT * FROM c " +
    "WHERE c.type = 'video' " +
    "AND FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

CosmosQueryRequestOptions opts = new CosmosQueryRequestOptions();
// enableCrossPartitionQuery is true by default for FTS ORDER BY RANK

return container.queryItems(
    new SqlQuerySpec(sql, new SqlParameter("@q", term)),
    opts, Video.class
).byPage(pageSize).next().toFuture();
```

**Fields that should NOT use FTS:**
- Short identifiers (`id`, `userid`) — use point read or range index equality
- Numeric fields — use range index with `=`, `>`, `<`
- Array elements already indexed with `[]/?` — `CONTAINS(LOWER(t), @q)` via EXISTS is fine

Reference: [Full-text search queries](https://learn.microsoft.com/azure/cosmos-db/gen-ai/full-text-search)

### 1.5 Use FullTextContains for keyword matching on indexed text fields

**Impact: HIGH** (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)

## Use FullTextContains for Keyword Matching

**Impact: HIGH (replaces expensive CONTAINS(LOWER(...)) string scans with O(log n) inverted index lookup)**

`FullTextContains(path, term)` performs a single-keyword lookup against the inverted index and is case-insensitive by design. It is dramatically faster than `CONTAINS(LOWER(c.field), @q)` on large containers because it does an `O(log n)` index lookup instead of a full document scan.

**Incorrect (scan-based — avoid for long text fields with FTS index):**

```sql
-- Full document scan, case folding at query time
SELECT * FROM c
WHERE CONTAINS(LOWER(c.description), @q)
```

```java
String sql = "SELECT * FROM c WHERE CONTAINS(LOWER(c.description), @q)";
```

**Correct:**

```sql
-- Inverted index lookup — no LOWER() needed, FTS tokenizer handles casing
SELECT * FROM c
WHERE FullTextContains(c.description, @q)
```

```java
// Java SDK — parameterized query with FullTextContains
String sql = "SELECT * FROM c WHERE c.type = 'video' " +
    "AND (CONTAINS(LOWER(c.name), @q) " +          // short field — range index OK
    "OR FullTextContains(c.description, @q) " +    // long text — FTS index
    "OR EXISTS(SELECT VALUE t FROM t IN c.tags WHERE CONTAINS(LOWER(t), @q)))";

SqlQuerySpec querySpec = new SqlQuerySpec(sql,
    new SqlParameter("@q", query.trim().toLowerCase()));

return container.queryItems(querySpec, opts, Video.class)
    .byPage(continuationToken, pageSize)
    .next()
    .map(page -> new ResultListPage<>(page.getResults(), page.getContinuationToken()))
    .toFuture();
```

**Variants:**
- `FullTextContains(path, term)` — document contains the term
- `FullTextContainsAll(path, term1, term2, ...)` — document contains ALL terms (AND)
- `FullTextContainsAny(path, term1, term2, ...)` — document contains ANY term (OR)

Reference: [FullTextContains function](https://learn.microsoft.com/azure/cosmos-db/nosql/query/fulltextcontains)

### 1.6 Use FullTextScore with ORDER BY RANK for BM25 relevance ranking

**Impact: MEDIUM-HIGH** (enables BM25-based ranked results instead of arbitrary order)

## Use FullTextScore for Relevance Ranking

**Impact: MEDIUM-HIGH (enables BM25-based ranked results instead of arbitrary order)**

`FullTextScore(path, term)` returns a BM25 relevance score. Use it in `ORDER BY` to surface the most relevant documents first. It **requires** `FullTextContains` in the WHERE clause on the same path.

**Incorrect (FullTextScore without FullTextContains — parse error):**

```sql
SELECT * FROM c
ORDER BY FullTextScore(c.description, 'cosmos')  -- ❌ missing WHERE FullTextContains
```

**Correct:**

```sql
SELECT c.name, c.description, c.addedDate
FROM c
WHERE FullTextContains(c.description, @q)
ORDER BY RANK FullTextScore(c.description, @q)
```

```java
String sql = "SELECT c.name, c.description, c.addedDate FROM c " +
    "WHERE FullTextContains(c.description, @q) " +
    "ORDER BY RANK FullTextScore(c.description, @q)";

SqlQuerySpec querySpec = new SqlQuerySpec(sql, new SqlParameter("@q", searchTerm));
```

> `RANK FullTextScore(...)` is cross-partition — Cosmos DB merges and re-ranks results from all partitions before returning the page.

Reference: [FullTextScore function](https://learn.microsoft.com/azure/cosmos-db/nosql/query/fulltextscore)

---

## References

- [Azure Cosmos DB documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Azure Cosmos DB Well-Architected Framework](https://learn.microsoft.com/azure/well-architected/service-guides/cosmos-db)
- [Performance tips for .NET SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice-dotnet)
