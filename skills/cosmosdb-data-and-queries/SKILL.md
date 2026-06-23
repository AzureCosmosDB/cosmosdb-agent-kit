---
name: cosmosdb-data-and-queries
description: |
  Azure Cosmos DB data design and querying: document modeling (embed vs reference, denormalization, schema versioning, 2MB limit, id constraints), partition key design (high cardinality, avoid hotspots, hierarchical, synthetic keys), indexing policy (composite, range vs hash, exclude unused paths, spatial), query optimization (point reads, avoid cross-partition scans, projections, pagination, parameterization, filter order), and data-access patterns (change-feed materialized views, ranking, service layer).
  USE FOR: choose partition key, embed vs reference, denormalize for reads, composite index for ORDER BY, cut write RU by excluding paths, point read by id and partition key, paginate with continuation tokens, avoid cross-partition queries, materialized views.
  DO NOT USE FOR: SDK client code (use cosmosdb-sdk); throughput, global distribution, monitoring, security (use cosmosdb-operations); vector or full-text search and LangChain/LangGraph agents (use cosmosdb-ai-and-search).
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# Azure Cosmos DB Data Modeling & Queries

Best practices for Azure Cosmos DB data design and querying: document modeling, partition key selection, indexing policy, query optimization, and data-access patterns.

## When to Apply

Reference these guidelines when designing documents, choosing partition keys, defining indexing policy, or writing and optimizing queries against Azure Cosmos DB.

## Rules

### Data Modeling

- [model-avoid-2mb-limit](rules/model-avoid-2mb-limit.md) - Keep Items Well Under 2MB Limit
- [model-denormalize-reads](rules/model-denormalize-reads.md) - Denormalize for Read-Heavy Workloads
- [model-embed-related](rules/model-embed-related.md) - Embed Related Data Retrieved Together
- [model-id-constraints](rules/model-id-constraints.md) - Follow ID Value Length and Character Constraints
- [model-json-serialization](rules/model-json-serialization.md) - Handle JSON serialization correctly for Cosmos DB documents
- [model-nesting-depth](rules/model-nesting-depth.md) - Stay Within 128-Level Nesting Depth Limit
- [model-numeric-precision](rules/model-numeric-precision.md) - Understand IEEE 754 Numeric Precision Limits
- [model-reference-large](rules/model-reference-large.md) - Reference Data When Items Grow Large
- [model-relationship-references](rules/model-relationship-references.md) - Use ID references with transient hydration for document relationships
- [model-schema-versioning](rules/model-schema-versioning.md) - Version Your Document Schemas
- [model-type-discriminator](rules/model-type-discriminator.md) - Use Type Discriminators for Polymorphic Data

### Partition Key Design

- [partition-20gb-limit](rules/partition-20gb-limit.md) - Plan for 20GB Logical Partition Limit
- [partition-avoid-hotspots](rules/partition-avoid-hotspots.md) - Distribute Writes to Avoid Hot Partitions
- [partition-hierarchical](rules/partition-hierarchical.md) - Use Hierarchical Partition Keys for Flexibility
- [partition-high-cardinality](rules/partition-high-cardinality.md) - Choose High-Cardinality Partition Keys
- [partition-immutable-key](rules/partition-immutable-key.md) - Choose Immutable Properties as Partition Keys
- [partition-key-length](rules/partition-key-length.md) - Respect Partition Key Value Length Limits
- [partition-query-patterns](rules/partition-query-patterns.md) - Align Partition Key with Query Patterns
- [partition-synthetic-keys](rules/partition-synthetic-keys.md) - Create Synthetic Partition Keys When Needed

### Indexing Strategies

- [index-composite-direction](rules/index-composite-direction.md) - Composite Index Directions Must Match ORDER BY
- [index-composite](rules/index-composite.md) - Use Composite Indexes for ORDER BY
- [index-exclude-unused](rules/index-exclude-unused.md) - Exclude Unused Index Paths
- [index-lazy-consistent](rules/index-lazy-consistent.md) - Understand Indexing Modes
- [index-path-syntax](rules/index-path-syntax.md) - Use Correct Indexing Path Syntax
- [index-range-vs-hash](rules/index-range-vs-hash.md) - Choose Appropriate Index Types
- [index-spatial](rules/index-spatial.md) - Add Spatial Indexes for Geo Queries

### Query Optimization

- [query-aggregate-single-pass](rules/query-aggregate-single-pass.md) - Compute min/max/avg with one scoped aggregate query
- [query-avoid-cross-partition](rules/query-avoid-cross-partition.md) - Minimize Cross-Partition Queries
- [query-avoid-scans](rules/query-avoid-scans.md) - Avoid Full Container Scans
- [query-distinct-keyword](rules/query-distinct-keyword.md) - Use DISTINCT keyword to eliminate duplicate results efficiently
- [query-latest-by-timestamp](rules/query-latest-by-timestamp.md) - Query "latest" documents with explicit ORDER BY and TOP 1
- [query-olap-detection](rules/query-olap-detection.md) - Detect and Redirect Analytical Queries Away from Transactional Containers
- [query-order-filters](rules/query-order-filters.md) - Order Filters by Selectivity
- [query-pagination](rules/query-pagination.md) - Use Continuation Tokens for Pagination
- [query-parameterize](rules/query-parameterize.md) - Use Parameterized Queries
- [query-point-reads](rules/query-point-reads.md) - Use Point Reads Instead of Queries for Known ID and Partition Key
- [query-top-literal](rules/query-top-literal.md) - Parameterize TOP Values Safely
- [query-use-projections](rules/query-use-projections.md) - Project Only Needed Fields

### Design Patterns

- [pattern-change-feed-materialized-views](rules/pattern-change-feed-materialized-views.md) - Use Change Feed for cross-partition query optimization with materialized views
- [pattern-efficient-ranking](rules/pattern-efficient-ranking.md) - Use count-based or cached rank approaches instead of full partition scans for ranking
- [pattern-service-layer-relationships](rules/pattern-service-layer-relationships.md) - Use a service layer to hydrate document references before rendering
