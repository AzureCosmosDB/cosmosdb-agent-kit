# Improvements Log

This document tracks all skill improvements made as a result of testing iterations. Each entry links the improvement back to the test scenario and iteration that identified the need.

---

## Format

Each improvement entry should include:
- **Date**: When the improvement was made
- **Scenario**: Which test scenario identified the need
- **Iteration**: Which iteration discovered the issue
- **Issue**: What problem was observed
- **Improvement**: What was changed in the skills
- **Files Modified**: List of skill files changed

---

## Improvements

#### 2026-02-17: Iteration 001 - Gaming Leaderboard Scenario (.NET / ASP.NET Core)

- **Scenario**: gaming-leaderboard
- **Iteration**: 001-dotnet
- **Result**: ✅ SUCCESSFUL - All endpoints functional, data persists correctly
- **Score**: 7/10
- **Key Achievement**: Identified two significant gaps — O(N) rank lookups and missing ETag concurrency — and created new rules for both

**New Rules Created** ⭐:

1. **pattern-efficient-ranking.md** (HIGH)
   - Documents count-based, cached rank, and score bucket approaches for efficient ranking
   - Prevents O(N) full partition scan anti-pattern found in `GetPlayerRankAsync`
   - Covers three solutions: COUNT queries, Change Feed pre-computed ranks, score buckets
   - Applicable to all leaderboard/ranking scenarios across languages

2. **sdk-etag-concurrency.md** (HIGH)
   - Documents ETag-based optimistic concurrency for read-modify-write operations
   - Player stat aggregation had race condition: concurrent score submissions cause lost updates
   - Includes .NET, Java, and Python examples with retry logic
   - Covers when to use vs. skip ETag checks

**Issues Encountered & Resolved**:

1. **O(N) Rank Lookup** — ⚠️ DESIGN ISSUE → RULE CREATED
   - Problem: `GetPlayerRankAsync` reads ALL entries in a leaderboard partition to find one player's rank
   - Impact: At 500K players, this consumes thousands of RU and takes seconds
   - Solution: Created `pattern-efficient-ranking.md` with COUNT-based approach
   - Status: ✅ Rule created to prevent this in future iterations

2. **Missing Optimistic Concurrency** — ⚠️ DESIGN ISSUE → RULE CREATED
   - Problem: `Player._etag` exists but is never used in `UpdatePlayerStatsAsync`
   - Impact: Concurrent score submissions can overwrite each other's stat updates
   - Solution: Created `sdk-etag-concurrency.md` with retry pattern
   - Status: ✅ Rule created to prevent this in future iterations

3. **OFFSET/LIMIT Instead of Continuation Tokens** — ⚠️ PARTIAL
   - Problem: Used `OFFSET 0 LIMIT @limit` instead of continuation tokens
   - Impact: RU cost increases with page depth
   - Status: ⚠️ Existing `query-pagination.md` rule should be strengthened with anti-pattern warning

**Test Results**:
- ✅ POST /api/scores — Score submission with player/leaderboard updates
- ✅ GET /api/leaderboard/global — Weekly global top N
- ✅ GET /api/leaderboard/global/all-time — All-time global rankings
- ✅ GET /api/leaderboard/regional/{country} — Regional weekly rankings
- ✅ GET /api/leaderboard/regional/{country}/all-time — Regional all-time rankings
- ✅ GET /api/leaderboard/player/{playerId} — Player rank + nearby players
- ✅ GET /api/players/{playerId} — Player profile with cumulative stats
- ✅ 404 for non-existent players
- ✅ 400 for missing required fields
- ✅ Empty results for countries with no data

**Best Practices Applied Successfully**:
1. ✅ **Materialized Views** — Leaderboard container as denormalized view (excellent)
2. ✅ **Synthetic Partition Keys** — `leaderboardKey` = `"global_2026-W07"`, `"US_all-time"`
3. ✅ **Singleton CosmosClient** — DI registration, Direct mode for production
4. ✅ **Composite Index** — `(bestScore DESC, lastUpdatedAt ASC)` on leaderboards
5. ✅ **Enum Serialization** — `JsonStringEnumConverter` with System.Text.Json
6. ✅ **Parameterized Queries** — All queries use `QueryDefinition.WithParameter`
7. ✅ **Projections** — Specific field selection instead of `SELECT *`
8. ✅ **Single-Partition Queries** — All queries target a single partition key
9. ✅ **Type Discriminators** — `"player"`, `"score"`, `"leaderboardEntry"` type fields
10. ✅ **Denormalized Reads** — Player stats embedded, leaderboard entries denormalized

**Best Practices NOT Applied**:
- ❌ Preferred regions, availability strategy, circuit breaker
- ❌ Diagnostics logging (only Debug-level RU logging)
- ❌ Azure Monitor / Application Insights integration
- ❌ Throughput configuration (autoscale/provisioned)
- ❌ Custom indexing policies on players/scores containers
- ❌ Schema versioning

**Lessons Learned**:
1. **Rank computation is a non-trivial problem** — Full partition scans are a natural but incorrect first approach
2. **Skills effectiveness is visible** — Materialized views, composite indexes, enum serialization all applied correctly because skills were loaded
3. **Production hardening gap** — Skills cover these topics but agent prioritized functionality over operational readiness
4. **ETag concurrency is commonly overlooked** — Read-modify-write patterns need explicit guidance

**FILES MODIFIED**:
- ✅ `skills/cosmosdb-best-practices/rules/pattern-efficient-ranking.md` — NEW (HIGH)
- ✅ `skills/cosmosdb-best-practices/rules/sdk-etag-concurrency.md` — NEW (HIGH)
- ✅ `skills/cosmosdb-best-practices/AGENTS.md` — Recompiled (57 total rules, up from 55)
- ✅ `testing/scenarios/gaming-leaderboard/iterations/iteration-001-dotnet/ITERATION.md` — NEW

---

#### 2026-02-17: Iteration 002 - Gaming Leaderboard Scenario (Java / Spring Boot 3)

- **Scenario**: gaming-leaderboard
- **Iteration**: 002-java
- **Result**: ✅ SUCCESSFUL - All endpoints functional, data persists correctly
- **Score**: 7/10
- **Key Achievement**: Skills feedback loop validated — COUNT-based ranking (Rule 9.2) from iteration-001 applied correctly. Schema versioning (Rule 1.5) also added. Java/Spring Data Cosmos API knowledge gaps identified.

**New Rules Created**: None (iteration-001's new rules were sufficient)

**Recommended Rule Updates** 📝:

1. **sdk-emulator-ssl.md** — UPDATE RECOMMENDED (HIGH)
   - `COSMOS.EMULATOR_SSL_TRUST_ALL` system property does NOT work with Java's Netty-based Cosmos SDK
   - Netty uses OpenSSL, bypassing Java's `SSLContext` entirely
   - Correct approach: extract emulator certificate, import into JDK truststore or custom truststore
   - Run with `-Djavax.net.ssl.trustStore=<path> -Djavax.net.ssl.trustStorePassword=changeit`

2. **query-pagination.md** — STRENGTHEN RECOMMENDED (MEDIUM)
   - Same OFFSET/LIMIT gap as iteration-001
   - Add explicit anti-pattern warning: "OFFSET/LIMIT RU cost scales linearly with offset depth"

**Issues Encountered & Resolved**:

1. **Wrong `CosmosTemplate.runQuery()` Signature** — ❌ BUILD ERROR → FIXED
   - Problem: Agent used `runQuery(SqlQuerySpec, Class<T>, String containerName)` — container name as 3rd arg
   - Correct: `runQuery(SqlQuerySpec, Class<?> domainType, Class<T> returnType)` — container inferred from `@Container` annotation
   - Impact: 3 compilation errors in LeaderboardService.java
   - Status: ✅ Fixed manually. SDK API documentation/skills gap identified.

2. **`Iterable` vs Stream API** — ❌ BUILD ERROR → FIXED
   - Problem: `CosmosTemplate.runQuery()` returns `Iterable<T>`, agent called `.stream()` on it
   - Correct: `StreamSupport.stream(iterable.spliterator(), false).toList()`
   - Status: ✅ Fixed. Common Java pattern not documented in skills.

3. **Emulator SSL with Netty** — ❌ RUNTIME ERROR → FIXED
   - Problem: `COSMOS.EMULATOR_SSL_TRUST_ALL` doesn't work with Netty/OpenSSL
   - Solution: Extracted emulator cert via PowerShell TcpClient, imported into custom truststore
   - Run JAR with `-Djavax.net.ssl.trustStore` and `-Djavax.net.ssl.trustStorePassword`
   - Status: ✅ Fixed. Rule update recommended for `sdk-emulator-ssl.md`.

4. **Validation Error Returns 500** — 🐛 BUG FOUND (NOT FIXED)
   - Problem: `GlobalExceptionHandler` handles `IllegalArgumentException` → 400, but Spring's `MethodArgumentNotValidException` falls to generic `Exception` → 500
   - Impact: POST /api/players with empty body returns HTTP 500
   - Status: ⚠️ Not fixed (documentation/testing only). Spring Boot-specific knowledge gap.

5. **`partitionKey` Null in JSON** — 🐛 BUG FOUND (NOT FIXED)
   - Problem: LeaderboardEntry `partitionKey` field serializes as `null` in REST responses
   - Impact: Cosmetic — queries work correctly via Cosmos DB partition key routing
   - Status: ⚠️ Likely Jackson/Spring Data Cosmos annotation interaction issue

**Comparison with Iteration 001 (.NET)**:

| Aspect | Iter-001 (.NET) | Iter-002 (Java) | Delta |
|--------|----------------|----------------|-------|
| Rank computation | ❌ O(N) scan | ✅ COUNT-based | ✅ Improved |
| Schema versioning | ❌ Missing | ✅ Applied | ✅ Improved |
| Build success | ✅ First try | ❌ 3 fixes needed | ❌ Regression |
| Validation errors | ✅ Returns 400 | ❌ Returns 500 | ❌ Regression |
| Composite index | ✅ Declared | ❌ Not available | ❌ Spring Data limitation |
| SSL handling | ✅ Easy callback | ❌ Truststore import | ❌ Harder |
| Error handling | ❌ No global handler | ✅ GlobalExceptionHandler | ✅ Improved |

**Skills Feedback Loop Validation** ✅:
- `pattern-efficient-ranking.md` (created in iter-001) → Applied correctly as COUNT-based ranking
- `sdk-etag-concurrency.md` (created in iter-001) → Partially applied (Spring Data implicit ETags)
- Rules created from previous iterations ARE improving subsequent iterations

**Best Practices Applied**:
- ✅ Materialized views (Rule 9.1), COUNT-based ranking (Rule 9.2)
- ✅ Synthetic partition keys (Rule 2.6), high cardinality keys (Rule 2.4)
- ✅ Singleton client (Rule 4.16), Gateway/Direct auto-detect (Rule 4.6)
- ✅ Session consistency (Rule 7.2), query metrics (Rule 8.4)
- ✅ Parameterized queries (Rule 3.5), projections (Rule 3.6)
- ✅ Type discriminators (Rule 1.6), schema versioning (Rule 1.5)
- ✅ contentResponseOnWriteEnabled (Rule 4.9)
- ❌ Preferred regions, availability strategy, circuit breaker, diagnostics, custom indexing

**FILES MODIFIED**:
- ✅ `testing/scenarios/gaming-leaderboard/iterations/iteration-002-java/ITERATION.md` — NEW

---

#### 2026-02-02: Iteration 001 - Multi-Tenant SaaS Scenario (.NET / ASP.NET Core)

- **Scenario**: multitenant-saas
- **Iteration**: 001-dotnet
- **Result**: ✅ **BUILD SUCCESSFUL** / ⚠️ **PACKAGING ERROR**
- **Score**: 7/10
- **Key Achievement**: Created valid Newtonsoft.Json dependency rule based on Microsoft docs

**New Rules Created** ⭐:

1. **sdk-newtonsoft-dependency.md** (MEDIUM)
   - Documents explicit Newtonsoft.Json >= 13.0.3 requirement
   - Covers security vulnerabilities in 10.x versions
   - Explains requirement even when using System.Text.Json
   - Provides version conflict troubleshooting
   - Based on Microsoft Learn official documentation section

**Issues Encountered**:

1. **Type Name Conflict** (Build Error) - ✅ RESOLVED
   - Problem: `User` class conflicts with `Microsoft.Azure.Cosmos.User`
   - Solution: Type alias `using CosmosUser = MultiTenantSaas.Models.User;`
   - Lesson: Avoid common SDK class names

2. **Missing Newtonsoft.Json** (Build Error) - ✅ RESOLVED → RULE CREATED
   - Problem: SDK requires explicit Newtonsoft.Json >= 13.0.3
   - Solution: `dotnet add package Newtonsoft.Json`
   - **Validation**: Microsoft docs have entire section "Managing Newtonsoft.Json Dependencies"
   - **Merit**: Documented pain point, security implications, non-obvious requirement
   - **Action**: Created comprehensive rule with troubleshooting

3. **Packaging Error** (Agent Error) - ✅ IDENTIFIED
   - Problem: Created zip with files at wrong directory levels
   - Result: Duplicate Program.cs files when extracted
   - Error: `error CS8802: Only one compilation unit can have top-level statements`
   - Impact: Prevented proper archival and testing

**Agent Methodology Issues** (Learning Experience):

1. ❌ **Premature Diagnosis**
   - Initially assumed "emulator SSL issue" without evidence
   - Created incorrect rule, then removed after user review
   - Should have: Extracted zip, read compiler error, diagnosed properly

2. ❌ **Poor Packaging**
   - Created source-code.zip with incorrect directory structure
   - Didn't verify extraction and build process
   - Prevented endpoint testing

3. ✅ **Corrective Actions**
   - Removed incorrect emulator SSL rule
   - Researched Microsoft docs to validate Newtonsoft.Json issue
   - Created proper rule with security guidance

**Best Practices Applied Successfully**:

1. ✅ **Hierarchical Partition Keys** - `[/tenantId, /projectId]` (EXCELLENT design)
   - Perfect for multi-tenant isolation
   - Overcomes 20GB limit per tenant
   - Enables efficient project-scoped queries

2. ✅ **Singleton CosmosClient** - DI registration with Direct mode
3. ✅ **Parameterized Queries** - All repositories use QueryDefinition
4. ✅ **Type Discriminators** - Polymorphic data in shared container
5. ✅ **Embedded Data** - Comments embedded in Tasks

**Files Modified**:
- **New Rule**: `skills/cosmosdb-best-practices/rules/sdk-newtonsoft-dependency.md`
- **Regenerated**: `skills/cosmosdb-best-practices/AGENTS.md` (55 rules, up from 54)
- **Documented**: `testing/scenarios/multitenant-saas/iterations/iteration-001-dotnet/ITERATION.md`

**Key Lessons**:

1. **Validate with official docs** - Microsoft Learn confirmed Newtonsoft.Json is a real issue
2. **Test packaging thoroughly** - Always extract and build from zip before archiving
3. **Read error messages** - Compiler errors tell you exactly what's wrong
4. **Don't assume root causes** - Evidence-based diagnosis prevents wasted effort
5. **User review is valuable** - Caught the premature conclusion about SSL

**Positive Outcomes**:

- Discovered and documented legitimate Newtonsoft.Json dependency rule
- Excellent hierarchical partition key design for multi-tenancy
- Demonstrated proper Cosmos DB best practices in code
- Learned better packaging and testing methodology

---

#### 2026-01-29: Iteration 001 - AI Chat/RAG Scenario (.NET / ASP.NET Core)

- **Scenario**: ai-chat-rag
- **Iteration**: 001-dotnet
- **Result**: ✅ **SUCCESSFUL** - Vector search implemented with emulator, containers created successfully
- **Score**: 8/10
- **Key Achievement**: **IDENTIFIED CRITICAL GAP** - Zero vector search rules in skills, created 4 new comprehensive rules
- **Rules Applied**: VectorEmbeddingPolicy, VectorIndexes, VectorDistance queries, autoscale, singleton client

**Critical Discovery**:

**ZERO Vector Search Rules Existed**
- Problem: Agent initially used wrong SDK version (3.44.0-preview.0) lacking VectorIndexes support
- Root Cause: No vector search rules existed in AGENTS.md to guide implementation
- Impact: Agent made incorrect assumptions about SDK capabilities
- Documentation: User provided official Microsoft Learn links proving SDK 3.45.0+ supports vector search
- Outcome: Created comprehensive vector search rules covering all languages

**New Rules Created** (All with examples in .NET, Python, JavaScript, Java):

1. **vector-enable-feature.md** (CRITICAL)
   - How to enable vector search feature on account via Portal or Azure CLI
   - Requirement to wait 15 minutes for feature activation
   - SDK version requirements per language
   
2. **vector-embedding-policy.md** (CRITICAL)
   - VectorEmbeddingPolicy configuration (path, dataType, dimensions, distanceFunction)
   - Cannot be modified after container creation
   - Examples: cosine, dotProduct, euclidean distance functions

3. **vector-index-type.md** (CRITICAL)
   - VectorIndexes configuration (QuantizedFlat vs DiskANN)
   - **CRITICAL**: Must exclude vector paths from regular indexing (ExcludedPaths)
   - Index type selection guide (QuantizedFlat < 50K vectors, DiskANN for larger)
   
4. **vector-distance-query.md** (HIGH)
   - VectorDistance() system function usage for similarity search
   - Parameterization best practices (query plan caching)
   - ORDER BY VectorDistance() for ranking results
   - Hybrid search patterns (vector + filters)

**Issues Encountered & Resolved**:

1. **Wrong SDK Version** (Initial Implementation)
   - Problem: Used Microsoft.Azure.Cosmos 3.44.0-preview.0 which lacks VectorIndexes property
   - Error: Agent assumed SDK didn't support VectorIndexes
   - Solution: Updated to SDK 3.45.0 (release version) with full vector search support
   - Status: ✅ RESOLVED - proper SDK version documented in rules

2. **Missing ExcludedPaths for Vectors**
   - Problem: Initially didn't exclude vector paths from regular indexing
   - Impact: Would cause high RU consumption and latency on vector inserts
   - Solution: Added vector paths to ExcludedPaths in indexing policy
   - Status: ✅ RESOLVED - now documented as CRITICAL in vector-index-type.md

3. **Configuration Parsing Issue** (Azure vs Emulator)
   - Problem: `configuration["CosmosDb:UseKey"]` string comparison failed
   - Error: Always evaluated to false, used DefaultAzureCredential even with UseKey=true
   - Solution: Changed to `configuration.GetValue<bool>("CosmosDb:UseKey", false)`
   - Status: ✅ RESOLVED - proper boolean parsing

4. **Azure Cloud Authentication Issues**
   - Problem: DefaultAzureCredential authentication hung during container initialization
   - Observation: Worked previously, then failed silently with no error logs
   - Workaround: Reverted to emulator for testing
   - Status: ⚠️ UNRESOLVED - Azure authentication intermittent, needs investigation

**Test Results**:

✅ Database `ai-chat-rag-db` created in emulator
✅ Container `sessions` created with partition key `/userId` (embedded messages pattern)
✅ Container `documents` created with partition key `/category` and vector search:
  - VectorEmbeddingPolicy: 1536 dimensions, Cosine distance
  - VectorIndexes: QuantizedFlat type
  - ExcludedPaths: `/embedding/*` (optimized for inserts)
✅ Application started successfully on http://localhost:5054
✅ REST API endpoints tested:
  - POST /api/chat/sessions - Created session successfully
  - Session ID returned: deeb93bc-0063-44c8-8cd5-872ed245ed55
✅ Vector search configuration validated

**Lessons Learned**:

1. **CRITICAL**: Agent kits MUST have comprehensive coverage of all major features (vector search was completely missing)
2. Always verify SDK versions in documentation - preview versions may lack features
3. Official Microsoft documentation is authoritative - trust it over assumptions
4. ExcludedPaths for vector properties is critical for performance (not optional)
5. Configuration parsing in .NET requires proper type conversion (GetValue<bool>)
6. Testing iterations reveal real gaps that wouldn't be found through code review alone

**Rule Enhancement Impact**:

From **0 vector search rules** to **4 comprehensive rules** covering:
- Feature enablement and prerequisites
- Embedding policy configuration  
- Vector index types and performance optimization
- Query patterns and best practices
- All with multi-language examples (.NET, Python, JavaScript, Java)

**FILES MODIFIED**:
- ✅ `rules/_sections.md` - Added Section 10: Vector Search
- ✅ `rules/vector-enable-feature.md` - NEW (CRITICAL)
- ✅ `rules/vector-embedding-policy.md` - NEW (CRITICAL)
- ✅ `rules/vector-index-type.md` - NEW (CRITICAL)
- ✅ `rules/vector-distance-query.md` - NEW (HIGH)
- ✅ `AGENTS.md` - Recompiled with 54 total rules (was 50)

**Priority for Future Testing**:
- HIGH: Test vector search with other languages (Python, Java, JavaScript)
- HIGH: Investigate Azure DefaultAzureCredential intermittent failures
- MEDIUM: Add vector search to other scenarios (multitenant-saas, etc.)
- MEDIUM: Create rule for vector index performance tuning

---

#### 2026-01-29: Iteration 003 - IoT Telemetry Scenario (Python / FastAPI)

- **Scenario**: iot-device-telemetry
- **Iteration**: 003-python (WITH skills)
- **Result**: ✅ **SUCCESSFUL** - End-to-end tested, database and containers created in emulator
- **Score**: 9/10
- **Key Achievement**: **VALIDATED Rule 4.9** and successfully tested complete application with database creation
- **Rules Applied**: 30+ rules including hierarchical partition keys (production), TTL, autoscale, composite indexes

**Issues Encountered & Resolved**:

1. **Pydantic Dependency Issue** (Python 3.13 compatibility)
   - Problem: pydantic 2.5.3 doesn't have prebuilt wheels for Python 3.13
   - Error: "Failed building wheel for pydantic-core"
   - Solution: Updated to pydantic 2.10.0 and pydantic-core 2.27.0
   - Status: ✅ RESOLVED

2. **Environment Variable Override** (**Rule 4.9 Validated**)
   - Problem: System `COSMOS_ENDPOINT` environment variable overrode `.env` file
   - Error: "Local Authorization is disabled. Use an AAD token"
   - Solution: Added `python-dotenv` with `load_dotenv(override=True)` before pydantic-settings
   - Status: ✅ RESOLVED - Rule 4.9 accurately predicted this scenario

3. **ThroughputProperties API Usage**
   - Problem: Python SDK doesn't accept dict for autoscale throughput
   - Error: "TypeError: offer_throughput must be int or an instance of ThroughputProperties"
   - Solution: Changed from `{'maxThroughput': 1000}` to `ThroughputProperties(auto_scale_max_throughput=1000)`
   - Status: ✅ RESOLVED

4. **Emulator Hierarchical Partition Key Limitation**
   - Problem: Local emulator doesn't support `kind='MultiHash'` for hierarchical partition keys
   - Error: "The 'kind' value 'MultiHash' specified in the partition key definition is invalid"
   - Solution: Used single partition key `/deviceId` for emulator, documented production recommendation
   - Status: ✅ RESOLVED with documentation for production

**Test Results**:

✅ Database `iot-telemetry-db` created in emulator
✅ Container `devices` created with partition key `/id` (autoscale 1000 RU/s)
✅ Container `telemetry` created with partition key `/deviceId` (autoscale 4000 RU/s, TTL enabled)
✅ Application started successfully on http://0.0.0.0:8000
✅ Gateway connection mode working with emulator
✅ Environment variables loaded correctly from .env file

**Lessons Learned**:

1. Always test end-to-end with database creation verification (not just code review)
2. Python 3.13 is new - check package compatibility before using
3. Use `python-dotenv` with `override=True` to prevent system env var issues
4. Python SDK API differs from other SDKs (ThroughputProperties class vs dict)
5. Local emulator has limitations (hierarchical partition keys not supported)

**Rule Enhancement Recommendations**:

None - Rule 4.9 worked exactly as designed and helped identify/resolve the environment configuration issue.
Potential future rules:
- Python SDK-specific rule about ThroughputProperties class usage
- Emulator limitations documentation (hierarchical keys, etc.)
  - Solution: Recommend logging endpoint at startup (already in rule) + manual .env loading if override needed
  - Priority: HIGH - affects all FastAPI/Pydantic v2 projects

**Python SDK Observations**:
- ✅ Hierarchical partition key requires dict format: `{'paths': [...], 'kind': 'MultiHash', 'version': 2}`
- ⚠️ No built-in bulk executor (unlike .NET/Java)
- ⚠️ Python SDK is not truly async (HTTP is synchronous under the hood)

**Lessons Learned**:
- Rule 4.9 is critical and accurately predicts real-world issues
- Logging endpoint at startup is essential for catching config issues
- Pydantic v2 environment variable handling differs from python-dotenv
- Python 3.13 requires newer dependency versions

**FILES TO MODIFY** (Proposed):
- `rules/sdk-local-dev-config.md` (enhance with pydantic-settings example - HIGH priority)
- `rules/partition-hierarchical.md` (add Python dict format example - MEDIUM priority)

---

#### 2026-01-29: Iteration 002 - IoT Telemetry Scenario (Java / Spring Boot)

- **Scenario**: iot-device-telemetry
- **Iteration**: 002-java (WITH skills)
- **Result**: ✅ **BUILD SUCCESS** - Complete Spring Boot 3 implementation after resolving compatibility issues
- **Score**: 8/10
- **Key Achievement**: Validated Cosmos DB best practices in Java ecosystem, identified framework version requirements gap
- **Rules Applied**: 26+ rules from AGENTS.md including:
  - 1.2: Denormalized device info in telemetry readings (deviceName, location)
  - 1.3: Embedded device summary for read efficiency
  - 1.5: Schema versioning (schemaVersion field)
  - 1.6: Type discriminators (type="device", type="telemetry")
  - 2.3: Hierarchical partition key (deviceId + yearMonth)
  - 2.5: Partition key aligned with query patterns
  - 3.1: All queries single-partition
  - 3.5: Parameterized queries throughout
  - 4.1: Async APIs with Project Reactor (Mono/Flux)
  - 4.13: Singleton CosmosClient
  - 5.1: Composite indexes for time-range queries
  - 6.1: Autoscale throughput for variable IoT workload
  - TTL: 30-day automatic expiration at container level

**Issues Encountered and Resolved**:

1. **Java Version Mismatch** (CRITICAL - NEW RULE NEEDED)
   - Problem: Spring Boot 3.2.1 requires Java 17+, pom.xml initially had Java 11
   - Error: "bad class file...has wrong version 61.0, should be 55.0"
   - Solution: Updated `<java.version>` to 17, set JAVA_HOME to Java 17 installation
   - Impact: Build blocker - developers would fail immediately without this knowledge
   - **GAP IDENTIFIED**: AGENTS.md doesn't document Java/Spring Boot version requirements

2. **SDK API Evolution** (MEDIUM impact)
   - Problem: `setMaxItemCount()` method not public in azure-cosmos 4.52.0
   - Solution: Removed explicit page size settings (SDK uses sensible defaults)
   - Impact: Code compiles after removal, no functionality loss

3. **Hierarchical Partition Key API** (HIGH - DOCUMENTATION NEEDED)
   - Problem: Constructor signature changed in current SDK version
   - Old (non-working): `new CosmosContainerProperties(name, List<String>)`
   - New (working):
   ```java
   PartitionKeyDefinition partitionKeyDef = new PartitionKeyDefinition();
   partitionKeyDef.setPaths(Arrays.asList("/deviceId", "/yearMonth"));
   partitionKeyDef.setKind(PartitionKind.MULTI_HASH);
   partitionKeyDef.setVersion(PartitionKeyDefinitionVersion.V2);
   ```
   - Impact: Build failure without proper API usage
   - **GAP IDENTIFIED**: Rule 2.3 mentions hierarchical keys but lacks Java SDK-specific API example

**Proposed Skill Improvements**:

1. **NEW RULE: `sdk-java-spring-boot-versions.md`** (CRITICAL impact)
   - Category: SDK Configuration (Section 4)
   - Problem: Framework version requirements not documented in skills
   - Content: Document Spring Boot 3.x → Java 17+, Spring Boot 2.7.x → Java 11/17, SDK compatibility matrix
   - Rationale: Prevents immediate build failures, critical for developer onboarding
   - Priority: HIGH - foundational requirement

2. **ENHANCE RULE 2.3**: Add Java SDK-specific hierarchical partition key code
   - Current state: Conceptual explanation only
   - Enhancement: Add code example showing `PartitionKeyDefinition` with `MULTI_HASH` and `V2`
   - Rationale: API has evolved, developers need current syntax
   - Priority: MEDIUM - affects hierarchical partition key adoption

**Observations**:
- ✅ All Cosmos DB best practices successfully applied in Java/Spring Boot ecosystem
- ✅ Async/reactive programming with Project Reactor properly implemented
- ✅ Build artifacts generated correctly (iot-telemetry-api-1.0.0.jar - 18.4 MB)
- ⚠️ Framework version requirements are external to Cosmos DB but critical for successful implementation
- ⚠️ SDK API documentation should be version-specific

**Lessons Learned**:
- Spring Boot version dictates minimum Java version (non-negotiable dependency)
- Azure Cosmos SDK API evolves between versions - check current documentation
- Skills should include framework compatibility matrices for complete guidance
- Hierarchical partition key API requires explicit V2 definition in Java SDK

**FILES TO MODIFY** (Proposed):
- `rules/sdk-java-spring-boot-versions.md` (new - CRITICAL)
- `rules/partition-hierarchical.md` (enhance with Java API example - MEDIUM)
- `rules/_sections.md` (if new rule added)
- `SKILL.md` (update quick reference)
- `AGENTS.md` (regenerate after rule changes)

---

#### 2026-01-29: Iteration 001 - IoT Telemetry Scenario (.NET)

- **Scenario**: iot-device-telemetry
- **Iteration**: 001-dotnet (WITH skills)
- **Result**: ✅ **SUCCESS** - Excellent implementation with all best practices applied
- **Score**: 9.5/10
- **Key Achievement**: Demonstrated comprehensive application of best practices for time-series IoT data
- **Rules Applied**: 30+ rules from AGENTS.md including:
  - 1.2: Denormalized `latestReading` in Device (avoids joins)
  - 1.3: Embedded `TelemetrySummary` for related data
  - 1.6: Type discriminators (`type` field)
  - 2.1: Hierarchical partition key prevents 20GB limit
  - 2.2: Synthetic key distributes writes (no hot partition)
  - 2.3: Hierarchical partition key (`deviceId` + `yearMonth`)
  - 2.5: Partition key aligned with query patterns
  - 2.6: Synthetic partition key for time-series
  - 3.1: All queries single-partition
  - 3.5: Parameterized queries throughout
  - 4.1: Async APIs throughout
  - 4.4/4.6: Correct mode per environment (Gateway for emulator, Direct for production)
  - 4.11: 429 retry configuration
  - 4.13: Singleton CosmosClient
  - 5.1: Composite indexes for time-range queries
  - 5.2: Excluded unused paths (temperature, humidity, batteryLevel)
  - 6.1: Autoscale for variable IoT workload
  - TTL: 30-day automatic expiration
- **Observations**:
  - ✅ All best practices from AGENTS.md were successfully applied
  - ✅ Hierarchical partition key perfectly suited for time-series data
  - ✅ Database initialized successfully with optimal container configurations
  - ✅ Clean build with no errors
  - ✅ Comprehensive documentation linking every decision to best practices
- **No Issues Found**: The iteration ran smoothly with no bugs or gaps requiring new rules
- **Lessons Learned**:
  - Indexing policy must include "/" path - learned to use `/*` with exclusions rather than overly specific inclusions
  - TCP connection settings only apply to Direct mode (not Gateway for emulator)
  - The skill kit is comprehensive for IoT time-series scenarios

**NO NEW RULES NEEDED**: All patterns and issues were covered by existing rules. This validates the skill kit's completeness for time-series IoT workloads.

**FILES MODIFIED**: None - no skill improvements needed

---

#### 2026-01-28: Cross-Iteration Review - New Rules from Lessons Learned

Based on reviewing all iteration ITERATION.md files and identifying patterns that could become rules:

**NEW RULES CREATED:**

1. **`pattern-change-feed-materialized-views.md`** (HIGH impact)
   - **Source**: Iterations 001, 002, 003 all noted cross-partition queries for admin endpoints
   - **Issue**: Status/date queries require expensive cross-partition fan-out
   - **Solution**: Document Change Feed pattern to maintain separate container optimized for admin queries
   - **Benefit**: Converts cross-partition queries into single-partition lookups

2. **`sdk-java-content-response.md`** (MEDIUM impact)
   - **Source**: Iteration 003-java discovered createItem returned null
   - **Issue**: Java SDK doesn't return document content after write operations by default
   - **Solution**: Set `contentResponseOnWriteEnabled(true)` at client or request level
   - **Benefit**: Prevents confusion when created items appear null

3. **`sdk-local-dev-config.md`** (MEDIUM impact)
   - **Source**: Iteration 004-python encountered system env vars overriding .env file
   - **Issue**: Developers with Azure CLI configured have COSMOS_ENDPOINT pointing to cloud, not emulator
   - **Solution**: Use `load_dotenv(override=True)`, environment-specific configs, and log endpoint at startup
   - **Benefit**: Prevents accidental connections to production during local development

**EXISTING RULE ENHANCED:**

4. **`sdk-emulator-ssl.md`** - Now covers ALL SDKs
   - **Previous**: Java-only SSL certificate guidance
   - **Enhanced**: Added .NET, Python, Node.js examples for Gateway mode and SSL handling
   - **Benefit**: Single reference for all SDK emulator configuration

**COMPILE SCRIPT UPDATED:**
- Added `pattern-` prefix for Design Patterns category (section 9)

**FILES MODIFIED:**
- `rules/pattern-change-feed-materialized-views.md` (new)
- `rules/sdk-java-content-response.md` (new)
- `rules/sdk-local-dev-config.md` (new)
- `rules/sdk-emulator-ssl.md` (enhanced)
- `rules/_sections.md` (added section 9)
- `SKILL.md` (updated quick reference)
- `scripts/compile.js` (added pattern- prefix)
- `AGENTS.md` (regenerated - now 53 rules)
- `testing/README.md` (added Continuous Improvement / Feedback Loop section)

---

#### 2026-01-28: Iteration 003 - Java SDK Validation (ecommerce-order-api)

- **Scenario**: ecommerce-order-api
- **Iteration**: 003-java (WITH skills)
- **Result**: ✅ **SUCCESS** - Critical enum serialization test passed
- **Improvement Validated**: Rule 4.10 works across both .NET and Java SDKs
- **Score**: 9.0/10
- **Key Rules Applied**:
  - 4.10: `@JsonValue`/`@JsonCreator` for enum serialization ✅
  - 4.1: Singleton CosmosAsyncClient via Spring @Bean ✅
  - 4.2: Async APIs with Project Reactor (Mono<T>) ✅
  - 4.3: ThrottlingRetryOptions configured ✅
  - 1.1: Embedded OrderItems ✅
  - 2.1: High-cardinality partition key (customerId) ✅
  - 3.1/3.5: Single-partition queries with SqlParameter ✅
  - 5.2: Composite indexes ✅
- **Observations**: 
  - The skill kit successfully guided Java-specific enum serialization
  - Gateway mode required for emulator (Direct mode has SSL issues)
  - `contentResponseOnWriteEnabled(true)` needed to get item back after create
- **Tests**: 5/6 passing (date range query has format issue, not enum-related)

**NEW RULE CREATED**: `sdk-emulator-ssl` - Configure SSL for Cosmos DB Emulator in Java
- **Issue**: Java SDK fails with SSL handshake errors when connecting to emulator
- **Solution**: Import emulator certificate into JDK truststore + use Gateway mode
- **Files Modified**: 
  - `rules/sdk-emulator-ssl.md` (new file)
  - `SKILL.md` (added to quick reference)
  - `AGENTS.md` (regenerated)

#### 2026-01-28: Iteration 002 - Skills Successfully Applied (ecommerce-order-api)

- **Scenario**: ecommerce-order-api
- **Iteration**: 002-dotnet (WITH skills)
- **Result**: ✅ **SUCCESS** - All tests passed, including the critical enum serialization test
- **Improvement Validated**: Rule 4.10 (enum serialization) was applied correctly, fixing the bug from iteration-001
- **Score**: 9.1/10 (vs 6/10 in baseline iteration-001)
- **Key Rules Applied**:
  - 4.10: JsonStringEnumConverter configured ✅
  - 4.1: Singleton CosmosClient ✅
  - 4.4: Direct connection mode ✅
  - 1.1: Embedded OrderItems ✅
  - 2.1/2.4: High-cardinality partition key (customerId) ✅
  - 3.1/3.2: Single-partition queries with projections ✅
  - 5.2: Composite indexes ✅
- **Observations**: 
  - The skill kit successfully prevented the enum serialization bug
  - Agent applied 18+ rules from the skill kit
  - Cross-partition queries (status/date) are unavoidable given partition key choice - could add guidance for Change Feed patterns

#### 2026-01-27: Testing Framework - Skills Must Be Loaded First

- **Scenario**: ecommerce-order-api
- **Iteration**: 001-dotnet
- **Issue**: Iteration 001 was run WITHOUT loading the skill kit first, making it a baseline test rather than a skill kit test
- **Improvement**: Updated testing framework documentation to emphasize skills MUST be loaded before each iteration
- **Files Modified**: 
  - `testing/README.md` - Added "CRITICAL: Install Skills FIRST" section
  - `testing/scenarios/_iteration-template.md` - Added "Skills Verification" section
  - `iteration-001-dotnet/ITERATION.md` - Marked as baseline (no skills)

#### 2026-01-29: Iteration 002 - AI Chat/RAG Scenario (Python / FastAPI / Azure Cloud)

- **Scenario**: ai-chat-rag
- **Iteration**: 002-python
- **Result**: ✅ **SUCCESSFUL** - Complete working implementation with vector search in Azure
- **Score**: 10/10 - Full repository layer, test data, end-to-end vector search validated
- **Environment**: Azure Cosmos DB (Cloud), DefaultAzureCredential auth
- **Key Achievement**: **VALIDATED** all 4 vector search rules work correctly in Python/Azure

**Implementation Summary**:
- ✅ Complete repository pattern (chat_repository.py, document_repository.py)
- ✅ Vector search using VectorDistance() queries working end-to-end
- ✅ Test data: 10 documents with 1536D embeddings + 3 chat sessions
- ✅ Vector similarity search returning ranked results
- ✅ Data visible and queryable in Azure Portal

**Technical Details**:
- SDK: azure-cosmos 4.14.5 (requires >= 4.7.0 for vector search)
- Vector Index: QuantizedFlat (optimal for < 50K vectors)
- Distance Function: Cosine similarity
- Partition Keys: /userId (sessions), /category (documents)

**Issues Encountered**:

1. **Windows Unicode Console Error**
   - Issue: Checkmark characters (✓) caused UnicodeEncodeError on Windows console
   - Solution: Replaced all ✓ with [OK] in logging output
   - Impact: Minor - cosmetic logging fix
   - Files: config.py, cosmos_service.py, main.py

2. **SDK Version Requirements**
   - Issue: Vector search requires azure-cosmos >= 4.7.0
   - Solution: Updated requirements.txt to specify minimum version
   - Installed: 4.14.5 (latest stable)
   - Impact: Critical for vector search functionality

3. **Missing Repository Layer**
   - Issue: Initial skeleton had endpoints but no data access implementation
   - Solution: Implemented complete repository pattern based on Microsoft samples
   - Pattern: upsert_item() for documents, read-modify-write for embedded messages
   - Impact: Required for functional application

4. **Vector Search Query Syntax**
   - Issue: Needed correct pattern for VectorDistance() queries
   - Solution: Referenced GitHub samples for proper query structure:
   ```python
   query = """
       SELECT TOP @limit c.title, c.content,
              VectorDistance(c.embedding, @queryVector) AS similarityScore
       FROM c
       WHERE VectorDistance(c.embedding, @queryVector) > @threshold
       ORDER BY VectorDistance(c.embedding, @queryVector)
   """
   ```
   - Impact: Essential for vector similarity search

**Vector Search Validation Results**:
```
Found 5 results ordered by similarity:
  1. Embedding Generation Techniques       | Score: 0.0533
  2. Change Feed Processing                | Score: 0.0461
  3. Python SDK for Cosmos DB              | Score: 0.0306
  4. Indexing Policies for Vector Search   | Score: 0.0281
  5. Multi-Region Replication              | Score: 0.0273
```

**Rules Validated**:
- ✅ Rule 10.1 (vector-enable-feature.md): Feature enabled in Azure account
- ✅ Rule 10.2 (vector-embedding-policy.md): 1536 dims, Cosine, float32 configured correctly
- ✅ Rule 10.3 (vector-index-type.md): QuantizedFlat index working, embeddings excluded from default indexing
- ✅ Rule 10.4 (vector-distance-query.md): VectorDistance() queries returning ranked results

**Best Practices Demonstrated**:
- ✅ Rule 1.2 (model-embed-related): Messages embedded in session documents
- ✅ Rule 2.3 (partition-high-cardinality): userId and category partition keys
- ✅ Rule 2.2 (index-exclude-unused): Vector embeddings excluded from default indexing
- ✅ Rule 3.6 (query-use-projections): Embeddings excluded from SELECT when not needed

**Lessons Learned**:

1. **SDK Version Critical**: Python requires azure-cosmos >= 4.7.0 for vector search (tested 4.14.5)
2. **Embedding Normalization**: Mock embeddings must be normalized to unit length for cosine similarity
3. **Windows Compatibility**: Use ASCII-safe characters in console output (avoid Unicode symbols)
4. **Query Patterns**: VectorDistance() must appear in SELECT, WHERE, and ORDER BY clauses
5. **Indexing Performance**: Excluding /embedding/* from default indexing is critical for RU costs
6. **Microsoft Samples**: GitHub samples provide authoritative patterns for repository implementation

**Gap Analysis**: 
- ✅ No gaps found - all 4 vector search rules worked perfectly
- ✅ Python implementation validated .NET rules work cross-language
- ✅ Azure cloud deployment validated (vs emulator in iteration 001)

**FILES CREATED**:
- ✅ `chat_repository.py` - Chat session data access layer (200 lines)
- ✅ `document_repository.py` - Document + vector search operations (220 lines)
- ✅ `create_test_data.py` - Test data generator with mock embeddings
- ✅ `test_vector_search.py` - Vector search validation script
- ✅ Updated `main.py` - Wired repositories to FastAPI endpoints
- ✅ `ITERATION.md` - Complete documentation

**NO SKILL MODIFICATIONS NEEDED** - All existing rules sufficient and accurate.

**Post-Iteration Rule Additions**:

After completing the iteration successfully, user provided GitHub samples showing proper implementation patterns. Based on this, added 2 new rules:

1. **vector-repository-pattern.md** (HIGH impact)
   - Issue: Agent had vector query rule but not complete repository implementation pattern
   - Solution: Created comprehensive rule showing data access layer with upsert, vector search, get/delete methods
   - Examples: Python, .NET, JavaScript, Java repository classes
   - Covers: Clean abstraction, testability, proper error handling, RU logging

2. **vector-normalize-embeddings.md** (MEDIUM impact)
   - Issue: No guidance on embedding normalization for cosine similarity or testing
   - Solution: Created rule explaining L2 normalization, deterministic mock embeddings
   - Examples: All languages showing normalized embedding generation with magnitude verification
   - Covers: Why normalize, formula, production vs testing, common mistakes

**Updated Files**:
- ✅ `rules/vector-repository-pattern.md` - NEW (HIGH impact)
- ✅ `rules/vector-normalize-embeddings.md` - NEW (MEDIUM impact)
- ✅ `AGENTS.md` - Recompiled with 56 total rules (was 54)

**Next Testing Priorities**:
- MEDIUM: Test vector search with Java (validate rules cross-language)
- MEDIUM: Test vector search with JavaScript/Node.js
- LOW: Test DiskANN vector index type (for > 50K vectors scenario)

---

#### 2026-01-27: Enum Serialization Mismatch Bug (ecommerce-order-api)

- **Scenario**: ecommerce-order-api
- **Iteration**: 001-dotnet
- **Issue**: Agent generated code where Cosmos SDK stored enums as integers but queries searched for strings, causing status queries to return empty results
- **Improvement**: ✅ Added new rule `sdk-serialization-enums.md` with guidance on consistent enum serialization
- **Priority**: HIGH
- **Files Modified**: 
  - `rules/sdk-serialization-enums.md` (new)
  - `AGENTS.md` (added section 4.10)

#### 2026-01-27: Missing Pagination Pattern (ecommerce-order-api)

- **Scenario**: ecommerce-order-api
- **Iteration**: 001-dotnet
- **Issue**: List queries returned all results without pagination, which would fail at scale
- **Analysis**: Rule `query-pagination.md` already exists with good content - the agent simply didn't apply it
- **Action**: No rule change needed, but highlights that agents may not always apply existing rules
- **Priority**: HIGH (for observation)
- **Files Modified**: None - rule already exists

#### 2026-01-27: Missing RU Diagnostics Logging (ecommerce-order-api)

- **Scenario**: ecommerce-order-api
- **Iteration**: 001-dotnet
- **Issue**: No logging of CosmosDiagnostics or RU consumption for debugging/monitoring
- **Analysis**: Rule `monitoring-ru-consumption.md` already exists with comprehensive SDK examples - agent didn't apply it
- **Action**: No rule change needed - rule has .NET examples with logging, telemetry, and middleware patterns
- **Priority**: MEDIUM (for observation)
- **Files Modified**: None - rule already exists

---

## Release History

### v1.0.0 (Initial Release)

- Initial set of 48 rules covering:
  - Data modeling (6 rules)
  - Partition key design (6 rules)
  - Query optimization (6 rules)
  - SDK best practices (9 rules)
  - Indexing strategies (5 rules)
  - Throughput & scaling (5 rules)
  - Global distribution (6 rules)
  - Monitoring & diagnostics (5 rules)
