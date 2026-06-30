# Mosaic Cosmos DB SDK Benchmark — Test Coverage

*A plain-language overview of what this benchmark measures, for product and program stakeholders.*

---

## 1. What this benchmark measures

We give an AI coding agent the **Cosmos DB best-practices skill** and ask it to build the
**same backend service in five languages** (Python, .NET, Java, Node.js, Go). We then run an
automated test suite that answers two questions for each language:

1. **Does the service actually work?** (Functional correctness)
2. **Did the agent follow Microsoft's Cosmos DB best practices?** (Quality of the implementation)

The point is not just "can the agent write code" — it's "does loading our best-practices skill
measurably change the agent's behaviour toward the patterns we recommend." Every quality check
maps back to a specific rule in the Cosmos DB best-practices guidance.

---

## 2. How the tests are organized — five coverage layers

The suite is grouped into five layers, moving from "does it run" up to "is it well-engineered and honest," plus a check that the agent actually used the guidance.

| Layer | Theme | What it answers |
| --- | --- | --- |
| **Layer 1** | Functional correctness | Does the API behave per the contract? |
| **Layer 2** | Data modeling | Did the agent design good Cosmos documents and containers? |
| **Layer 3** | SDK configuration | Did the agent set up the Cosmos client the recommended way? |
| **Layer 4** | Anti-patterns & honesty | Did the agent avoid known mistakes and avoid fabricating guidance? |
| **Layer 5** | Skill engagement | Did the agent actually open and read the best-practices skill? |

Layers 1 and 2 are **language-agnostic** — they inspect the running service and the data it
stored, so they apply identically to all five SDKs. Layers 3 and 4 are **language-aware** — each
check knows the idioms of its language and is skipped for the others. Layer 5 is **language-agnostic**
and runs for every SDK.

---

## 3. Coverage detail

### Layer 1 — Functional correctness *(applies to all 5 SDKs)*

Runs against the agent's live service.

| Check | What it verifies | Why it matters |
| --- | --- | --- |
| Health endpoint | `GET /health` returns `200` + a status body | Confirms the service started and is reachable |
| Create persists fields | A created user is stored with name, email, city, and interests intact (including order) | Confirms writes work and nothing is dropped or reordered |
| Get existing user | `GET /users/{id}` returns `200` for a known user | Core read path works |
| Get unknown user | `GET /users/{id}` returns `404` for a missing user | Correct not-found handling, not a crash or empty `200` |
| List by city | `GET /users?city=Seattle` returns only Seattle users | Query/filter path works and is correctly scoped |
| List with no match | Filtering on an unknown city returns an empty array | Empty results handled cleanly |

### Layer 2 — Data modeling *(applies to all 5 SDKs)*

Inspects the actual documents and container settings the agent created.

| Check | What it verifies | Why it matters |
| --- | --- | --- |
| Partition key exists | The container declares a partition key | Required for any scalable Cosmos design |
| Partition key isn't `/city` | The key is not the city field | Cities are a long-tail distribution → hot partitions and wasted throughput |
| Partition key is user-shaped | The key resolves to the user identity | Single-user lookups hit a single partition (cheap, fast) |
| Indexing policy present | The container has an indexing policy | Baseline for any indexing decision |
| Indexing policy is tailored | It's not the default "index everything" policy | Indexing every field inflates write cost on a write-heavy catalog |
| Excludes unused paths | At least one real field is excluded from indexing | Dropping indexes on never-filtered fields cuts write RU 20–80% |
| Throughput configured | RU/s is set at the database or container level | Explicit capacity planning instead of silent defaults |
| Type discriminator | Documents carry a type/kind field | Lets multiple entity types safely share a container |
| Schema version | Documents carry a version field | Enables safe schema evolution over time |
| ISO-8601 timestamps | `createdAt` is stored as an ISO-8601 string | Strings index and sort correctly in Cosmos; epoch numbers don't |
| Interests as string array | The interests field is a proper array of strings | Correct, queryable shape |
| Email & city are strings | Core fields have the expected types | Guards against type drift |

### Layer 3 — SDK configuration best practices *(language-aware)*

Scans the agent's source for the recommended client setup. Each row notes which languages it applies to.

| Check | What it verifies | Applies to |
| --- | --- | --- |
| Current SDK package | Uses the current first-party Cosmos package, not a deprecated/preview one | All 5 |
| Singleton client | The Cosmos client is created once and reused, not per-request | All 5 |
| Provision once | Database/container creation happens once at startup, not on every request | All 5 |
| Preferred regions | The client declares preferred regions/locations | Python, .NET, Java, Node.js |
| Direct connection mode | Uses Direct mode for production-grade latency | .NET, Java |
| Retry / throttling config | Configures retry behaviour for throttled (429) requests | Python, .NET, Java, Node.js |
| Diagnostics enabled | Turns on diagnostics/logging or sets an app identifier | Python, .NET, Java, Node.js |
| Client lifecycle | Properly closes/disposes the client (or relies on DI to) | Python, .NET, Java |
| End-to-end timeout | Enforces a hard deadline across retries, not just per-attempt | .NET, Java |

### Layer 4 — Anti-patterns & honesty *(language-aware)*

Catches known mistakes and checks that the agent is transparent when guidance doesn't exist.

| Check | What it verifies | Applies to |
| --- | --- | --- |
| No hardcoded account key | No real Cosmos key literal in source (emulator key excepted) | All 5 |
| Endpoint from configuration | Reads the endpoint from env/config, not hardcoded | All 5 |
| No legacy connection policy | Avoids the old pre-partitioning client style | Python |
| Async client in async app | Uses the async Cosmos client (+ async handlers, pinned deps) inside async web frameworks | Python |
| No preview package | Doesn't reference the abandoned preview package | .NET |
| No sync-over-async blocking | No `.Result` / `.Wait()` blocking on async Cosmos calls | .NET |
| No reactive blocking | No `.block()` collapsing a reactive pipeline | Java |
| No fabricated guidance | Doesn't claim "official" Node-specific best practices that don't exist | Node.js |
| Guidance transparency | Where no Go-specific guidance exists, the agent says what it borrowed or asks — no silent guessing | Go |
| No overstated certainty | Doesn't fabricate "official" Go-specific recommendations | Go |

### Layer 5 — Skill engagement *(applies to all 5 SDKs)*

Reads the agent's own session transcript to confirm it actually consulted the bundled
best-practices skill. Layers 1–4 measure the *quality of the result*; this layer measures whether
the agent *used the guidance we gave it* — so a strong model can't quietly skip the skill and still
look compliant by luck.

| Check | What it verifies | Why it matters |
| --- | --- | --- |
| Session transcript captured | The agent's session log was recorded for review | Without it we can't verify skill usage (flags an infrastructure gap, not the agent) |
| Read the skill index | The agent opened the skill's top-level `SKILL.md` guide | The index is the entry point that routes to the right detailed rules |
| Read at least one rule | The agent opened at least one specific rule file (e.g. partitioning, retries) | The concrete, actionable guidance lives in the rule files — opening the index alone isn't enough |

---

## 4. Approximate check counts per SDK

Functional + quality checks that run per language.

| SDK | Approx. checks |
| --- | :---: |
| Python | ~35 |
| .NET | ~35 |
| Java | ~34 |
| Node.js | ~31 |
| Go | ~29 |

*Counts vary slightly per run: a few checks self-skip when not relevant (e.g. the Python async
checks only fire if the agent chose an async web framework). Node.js and Go are lighter by design
— some configuration knobs and published guidance simply don't exist for those SDKs, and the
benchmark rewards honesty about that rather than penalizing a missing setting.*

---

*Coverage source of truth: `shared/verifier/check_api.py`, `check_cosmos.py`, `check_source.py`,
`check_skills.py`, plus per-task `tasks/mosaic-*/tests/checks.py`.*
