---
sections:
  - prefix: model-
    name: Data Modeling
    number: 1
    impact: CRITICAL
  - prefix: partition-
    name: Partition Key Design
    number: 2
    impact: CRITICAL
  - prefix: query-
    name: Query Optimization
    number: 3
    impact: HIGH
  - prefix: sdk-
    name: SDK Best Practices
    number: 4
    impact: HIGH
  - prefix: index-
    name: Indexing Strategies
    number: 5
    impact: MEDIUM-HIGH
  - prefix: throughput-
    name: Throughput & Scaling
    number: 6
    impact: MEDIUM
  - prefix: global-
    name: Global Distribution
    number: 7
    impact: MEDIUM
  - prefix: monitoring-
    name: Monitoring & Diagnostics
    number: 8
    impact: LOW-MEDIUM
  - prefix: pattern-
    name: Design Patterns
    number: 9
    impact: HIGH
  - prefix: tooling-
    name: Developer Tooling
    number: 10
    impact: MEDIUM
  - prefix: vector-
    name: Vector Search
    number: 11
    impact: HIGH
  - prefix: fts-
    name: Full-Text Search
    number: 12
    impact: HIGH
  - prefix: security-
    name: Security
    number: 13
    impact: HIGH
---

# 1. Data Modeling (model)

**Impact:** CRITICAL  
**Description:** Proper data modeling is foundational to Cosmos DB performance. Poor modeling leads to expensive queries, excessive RU consumption, and scalability issues that are difficult to fix later.

## 2. Partition Key Design (partition)

**Impact:** CRITICAL  
**Description:** Partition key choice determines data distribution, query efficiency, and scalability limits. A bad partition key creates hot partitions and cross-partition query overhead.

## 3. Query Optimization (query)

**Impact:** HIGH  
**Description:** Optimized queries minimize RU consumption and latency. Inefficient queries cause unnecessary cross-partition scans and index misses.

## 4. SDK Best Practices (sdk)

**Impact:** HIGH  
**Description:** Proper SDK usage ensures connection efficiency, retry handling, and optimal throughput. Common mistakes include creating multiple clients and ignoring throttling.

## 5. Indexing Strategies (index)

**Impact:** MEDIUM-HIGH  
**Description:** Strategic indexing reduces query costs while minimizing write overhead. Default indexing often includes unused paths.

## 6. Throughput & Scaling (throughput)

**Impact:** MEDIUM  
**Description:** Right-sizing throughput balances cost and performance. Over-provisioning wastes money; under-provisioning causes throttling.

## 7. Global Distribution (global)

**Impact:** MEDIUM  
**Description:** Multi-region configuration enables low-latency reads globally and disaster recovery. Consistency choices impact both.

## 8. Monitoring & Diagnostics (monitoring)

**Impact:** LOW-MEDIUM  
**Description:** Proactive monitoring catches issues before they impact users. Diagnostics enable root cause analysis.

## 9. Design Patterns (pattern)

**Impact:** HIGH  
**Description:** Architecture patterns for common scenarios like cross-partition query optimization, event sourcing, and multi-tenant designs.

## 10. Developer Tooling (tooling)

**Impact:** MEDIUM  
**Description:** Tooling guidance improves local development, inspection workflows, and developer productivity without replacing core SDK or data model guidance.

## 11. Vector Search (vector)

**Impact:** HIGH  
**Description:** Vector search configuration enables AI-powered semantic search and RAG patterns. Proper embedding storage, indexing, and query optimization are essential for performance and accuracy.

## 12. Full-Text Search (fts)

**Impact:** HIGH  
**Description:** Native full-text search (FTS) provides inverted-index-backed keyword matching, BM25 relevance ranking, and language-aware tokenization. Requires three coordinated changes: an account-level capability flag, a container fullTextPolicy, and a fullTextIndexes entry in the indexing policy.

## 13. Security (security)

**Impact:** HIGH  
**Description:** Secure authentication, network isolation, least-privilege access, and data protection for Cosmos DB accounts. Use Entra ID with managed identity instead of keys, restrict network access, assign minimum RBAC roles, and enable continuous backup for point-in-time restore.