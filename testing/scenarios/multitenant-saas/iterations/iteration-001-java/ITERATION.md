# Iteration 001 - Java Multi-tenant SaaS

## Metadata
- **Date**: 2026-02-18
- **Language/SDK**: Java 17 / Spring Boot 3.2.1 / azure-cosmos 4.52.0
- **Skill Version**: pre-release (post iteration-002 gaming-leaderboard)
- **Agent**: GitHub Copilot (Claude Opus 4.5)
- **Tester**: automated

## ⚠️ Skills Verification

**Were skills loaded before building?** ✅ Yes

**How were skills loaded?**
- [x] Read `skills/cosmosdb-best-practices/AGENTS.md` directly
- [ ] Skills auto-loaded from workspace
- [x] Explicit instruction to follow skills
- [ ] Other: [describe]

Additionally loaded specific Java rules:
- `sdk-java-content-response.md` (Rule 4.9)
- `sdk-java-spring-boot-versions.md` (Rule 4.10)
- `sdk-emulator-ssl.md` (Rule 4.6)
- `sdk-local-dev-config.md` (Rule 4.11)
- `sdk-connection-mode.md` (Rule 4.4)
- `partition-hierarchical.md` (Rule 2.3)

**Verification question asked?** Multiple verifications performed:
- "What connection mode for emulator?" → Gateway mode (Rule 4.6) ✅
- "What Java version for Spring Boot 3?" → Java 17+ (Rule 4.10) ✅
- "contentResponseOnWriteEnabled?" → true (Rule 4.9) ✅
- "Hierarchical partition keys?" → /tenantId, /type, /projectId (Rule 2.3) ✅

## Prompt Used

```
I need to build a Spring Boot 3 REST API for a multi-tenant SaaS project management system using Azure Cosmos DB (NoSQL API).

Requirements:
1. Support multiple tenants (companies) with complete data isolation
2. Each tenant has users, projects, and tasks
3. Tasks belong to projects and can be assigned to users
4. Query tasks by project, by assignee, or by status
5. Users can see all their tasks across all projects in their tenant
6. Tenant-level analytics (task counts by status)

Expected scale:
- ~1,000 tenants (companies)
- Tenant sizes vary: 10 to 10,000 users
- ~50 projects per tenant, ~500 tasks per project
- Largest tenants have millions of tasks

Please create:
1. The data model with proper multi-tenant design
2. The Cosmos DB container configuration (consider hierarchical partition keys)
3. A repository layer that enforces tenant isolation
4. REST API endpoints for the required operations

Use best practices for Cosmos DB throughout, especially for multi-tenant patterns and hierarchical partition keys.
```

## What the Agent Produced

### Data Model
- ✅ Single container design with type discriminators (tenant, user, project, task) — Rule 1.9
- ✅ Schema versioning field on all entities — Rule 1.8
- ✅ Denormalized assigneeName on tasks — Rule 1.2
- ✅ Denormalized ownerName on projects — Rule 1.2
- ✅ Denormalized task counts (total/open/inProgress/completed) on projects — Rule 1.2
- ✅ Embedded comments on tasks with bounded max (20) — Rule 1.3, Rule 1.7
- ✅ ETag field on base entity — Rule 4.7
- ⚠️ ETag field present but not used for optimistic concurrency in update operations

### Container Configuration
- ✅ Hierarchical partition keys: /tenantId, /type, /projectId — Rule 2.3
- ✅ MULTI_HASH PartitionKind with V2 — Rule 2.3
- ✅ Autoscale throughput at 4000 RU — Rule 6.1
- ❌ No custom indexing policy defined — default index everything policy
- ❌ No composite indexes for common query patterns (status+createdAt, assigneeId+dueDate)

### Repository Layer
- ✅ Parameterized queries throughout — Rule 3.5
- ✅ Partition key scoped queries where possible — Rule 3.1
- ✅ PartitionKeyBuilder for hierarchical keys
- ✅ Field projections on list queries (tasks by assignee/status) — Rule 3.6
- ✅ Tenant isolation enforced on ALL operations
- ✅ Denormalized count update after task CRUD operations
- ⚠️ No continuation token support for pagination — Rule 3.4
- ⚠️ Cross-partition queries for getProjectsByTenant (spans projectId values)

### SDK Usage
- ✅ Singleton CosmosClient via Spring @Bean — Rule 4.16
- ✅ Gateway mode for emulator, Direct mode for production — Rule 4.4, 4.6
- ✅ contentResponseOnWriteEnabled(true) — Rule 4.9
- ✅ Session consistency level
- ✅ Custom truststore for emulator SSL certificate — Rule 4.6
- ✅ @PreDestroy cleanup of client
- ✅ RU charge logging on write operations
- ❌ No preferred regions configured — Rule 4.8
- ❌ No availability strategy — Rule 4.12
- ❌ No SDK diagnostics beyond debug-level RU logging — Rule 4.5

## Build Status
- **Initial Build**: ❌ Failed (circular dependency in CosmosConfig — @PostConstruct calling @Bean method)
- **After Fixes**: ✅ Succeeded (refactored to use dependent @Bean methods instead of @PostConstruct)
- **Runtime Test**: ✅ Performed (all endpoints verified against Cosmos DB emulator)

## Runtime Test Results

### Tests Passed ✅
| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/tenants` | POST | ✅ Created tenant with type discriminator, schema version |
| `/api/tenants/{tenantId}` | GET | ✅ Retrieved by tenantId with HPK |
| `/api/tenants/{tenantId}/users` | POST | ✅ Created users with tenant isolation |
| `/api/tenants/{tenantId}/users` | GET | ✅ Listed users (single-partition query) |
| `/api/tenants/{tenantId}/projects` | POST | ✅ Created project with self-referencing projectId |
| `/api/tenants/{tenantId}/projects/{id}` | GET | ✅ Retrieved project with denormalized task counts |
| `/api/tenants/{tenantId}/projects/{id}/tasks` | POST | ✅ Created tasks, denormalized counts updated |
| `/api/tenants/{tenantId}/projects/{id}/tasks` | GET | ✅ Listed tasks by project (single-partition) |
| `/api/tenants/{tenantId}/projects/{id}/tasks/{id}` | PUT | ✅ Updated task status, counts refreshed |
| `/api/tenants/{tenantId}/projects/{id}/tasks/{id}/comments` | POST | ✅ Embedded comment added |
| `/api/tenants/{tenantId}/tasks?assigneeId=X` | GET | ✅ Cross-project assignee query with projections |
| `/api/tenants/{tenantId}/tasks?status=open` | GET | ✅ Status-based query |
| `/api/tenants/{tenantId}/analytics` | GET | ✅ Aggregated from denormalized project counts |

### Tests Failed ❌
None — all endpoints functional.

### Tenant Isolation Verified ✅
- Created tenant-beta with separate data
- Confirmed tenant-beta sees 0 users, 0 projects, 0 tasks from tenant-acme

### Bugs Found 🐛
1. **Circular dependency on startup** — `@PostConstruct` calling `cosmosClient()` `@Bean` method caused Spring context cycle. Fixed by refactoring database/container initialization into dependent `@Bean` methods.
2. **Duplicate entities on re-run** — Using `createItem` (not idempotent) means re-running create tests adds duplicates. Minor issue — should use upsert or check-before-create for production.

## Gaps Identified

### Critical Gaps (functionality issues)
None — all functional requirements from SCENARIO.md met.

### Best Practice Gaps (suboptimal but works)
1. **No custom indexing policy** — Default "index everything" wastes RU on writes. Should exclude unused paths and add composite indexes for common queries:
   - Composite: `(tenantId ASC, type ASC, status ASC, createdAt DESC)` for status queries
   - Composite: `(tenantId ASC, type ASC, assigneeId ASC, dueDate ASC)` for assignee queries
   - Exclude: `/description`, `/comments/*/text` from indexing
2. **No pagination support** — Queries return all results without continuation tokens. At scale (500 tasks/project), this wastes RU.
3. **ETag not used for concurrency** — `_etag` field exists on BaseEntity but upsert operations don't check if-match. Concurrent task updates could lose data.
4. **Cross-partition query for projects listing** — `getProjectsByTenant` spans all projectId partition values. At scale, should use a denormalized projects list or change-feed materialized view.

### Knowledge Gaps (agent didn't know/mention)
1. **Composite indexes** — Not mentioned or configured despite being critical for sorted multi-field queries at scale
2. **Change Feed for materialized views** — Rule 8.1 not applied for maintaining denormalized counts (currently done synchronously, which adds latency and RU to writes)
3. **Async API** — Used synchronous `CosmosContainer` instead of `CosmosAsyncContainer` — Rule 4.1 recommends async for Java
4. **Excluded regions / Circuit breaker** — Not relevant for emulator but should be mentioned for production readiness

## Recommendations for Skill Improvements

### High Priority — ✅ IMPLEMENTED
1. **New Rule: `sdk-java-cosmos-config.md`** — Documents `@PostConstruct` + `@Bean` circular dependency anti-pattern. Use dependent `@Bean` methods with parameter injection instead.
2. **Strengthened `index-composite.md`** — Added "Multi-Tenant Composite Index Patterns" section with composite indexes for `(type, status, createdAt)`, `(type, assigneeId, dueDate)`, `(type, priority, createdAt)`. Added Java `IndexingPolicy` example.

### Medium Priority — ✅ IMPLEMENTED
1. **Strengthened `query-pagination.md`** — Added "Unbounded Query Anti-Pattern" section with Java anti-pattern example and rule: "If a query can return more than 100 items, it must use pagination."
2. **Strengthened `sdk-etag-concurrency.md`** — Added "Critical: ETags for Denormalized Data Updates" section with Java examples of concurrent count update failure and ETag-protected fix.

### Low Priority
1. **Add rule: sync vs async API guidance for Java** — Document when to use `CosmosContainer` vs `CosmosAsyncContainer` in Spring Boot (WebFlux = async, traditional Spring MVC = sync is acceptable).

## Score Summary

| Category | Score | Notes |
|----------|-------|-------|
| Data Model | 9/10 | Excellent: type discriminators, schema versioning, bounded embeds, denormalization |
| Partition Key | 9/10 | Excellent: 3-level HPK perfectly suited for multi-tenant with project separation |
| Indexing | 3/10 | Default policy only — no composite indexes, no excluded paths |
| SDK Usage | 8/10 | Singleton client, Gateway for emulator, contentResponse enabled, custom truststore |
| Query Patterns | 7/10 | Good parameterization and projections, but no pagination, sync API |
| **Overall** | **7/10** | **Strong data model and HPK, but indexing and pagination gaps reduce production readiness** |

## Next Steps
1. ~~Add composite index examples to `index-composite.md`~~ ✅ Done
2. ~~Add Java-specific rule for `@Bean`/`@PostConstruct` anti-pattern~~ ✅ Done
3. ~~Strengthen pagination guidance in `query-pagination.md`~~ ✅ Done
4. Run iteration-002 in Java to verify improvements
