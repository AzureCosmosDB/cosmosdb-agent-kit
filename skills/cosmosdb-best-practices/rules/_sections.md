---
sections:
  - prefix: "model-"
    name: Data Modeling
    number: 1
    impact: CRITICAL
  - prefix: "partition-"
    name: Partition Key Design
    number: 2
    impact: CRITICAL
  - prefix: "query-"
    name: Query Optimization
    number: 3
    impact: HIGH
  - prefix: "sdk-"
    name: SDK Best Practices
    number: 4
    impact: HIGH
  - prefix: "index-"
    name: Indexing Strategies
    number: 5
    impact: MEDIUM-HIGH
  - prefix: "throughput-"
    name: Throughput & Scaling
    number: 6
    impact: MEDIUM
  - prefix: "global-"
    name: Global Distribution
    number: 7
    impact: MEDIUM
  - prefix: "monitoring-"
    name: Monitoring & Diagnostics
    number: 8
    impact: LOW-MEDIUM
  - prefix: "pattern-"
    name: Design Patterns
    number: 9
    impact: HIGH
  - prefix: "tooling-"
    name: Developer Tooling
    number: 10
    impact: MEDIUM
  - prefix: "vector-"
    name: Vector Search
    number: 11
    impact: HIGH
  - prefix: "fts-"
    name: Full-Text Search
    number: 12
    impact: HIGH
  - prefix: "security-"
    name: Security
    number: 13
    impact: HIGH
---

# 1. Data Modeling (model)

**Impact:** CRITICAL  
Proper data modeling is foundational to Cosmos DB performance.

# 2. Partition Key Design (partition)

**Impact:** CRITICAL  
Partition key choice determines data distribution and scalability.

# 3. Query Optimization (query)

**Impact:** HIGH  
Optimized queries minimize RU consumption and latency.

# 4. SDK Best Practices (sdk)

**Impact:** HIGH  
Proper SDK usage ensures connection efficiency and retry handling.

# 5. Indexing Strategies (index)

**Impact:** MEDIUM-HIGH  
Strategic indexing reduces query costs while minimizing write overhead.

# 6. Throughput & Scaling (throughput)

**Impact:** MEDIUM  
Right-sizing throughput balances cost and performance.

# 7. Global Distribution (global)

**Impact:** MEDIUM  
Multi-region configuration for low-latency reads and disaster recovery.

# 8. Monitoring & Diagnostics (monitoring)

**Impact:** LOW-MEDIUM  
Proactive monitoring catches issues before they impact users.

# 9. Design Patterns (pattern)

**Impact:** HIGH  
Architecture patterns for common Cosmos DB scenarios.

# 10. Developer Tooling (tooling)

**Impact:** MEDIUM  
Tooling for local development and developer productivity.

# 11. Vector Search (vector)

**Impact:** HIGH  
Vector search for AI-powered semantic search and RAG patterns.

# 12. Full-Text Search (fts)

**Impact:** HIGH  
Native FTS with inverted indexes, BM25 ranking, and language-aware tokenization.

# 13. Security (security)

**Impact:** HIGH  
Secure auth, network isolation, least-privilege RBAC, and data protection.
