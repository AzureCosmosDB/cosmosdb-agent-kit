# cosmos-sdk-skills-bench

An MSBench benchmark that measures whether a coding agent obeys a loaded
Cosmos DB best-practices skill set (`skills/cosmosdb-sdk`) when building
services backed by Azure Cosmos DB. Three scenarios × five SDKs = **15
Harbor tasks**.

## Scenarios

| Scenario | Domain | Key Testing Angles |
|----------|--------|-------------------|
| **Mosaic** | User-profile CRUD (4 endpoints) | Singleton, preferred regions, retry, diagnostics |
| **TicketWave** | Event ticketing (6 endpoints) | ETag concurrency, conditional creates, patch API |
| **SensorGrid** | IoT telemetry ingest (5 endpoints) | Async API, write-heavy retry, diagnostics |

Each scenario has 5 SDK variants: **Python**, **.NET**, **Java**, **Node.js**, **Go**.

Every instruction is deliberately silent about Cosmos-specific best
practices; the agent is supposed to pick them up from its loaded skills,
not from the prompt.

## Layout

```
cosmos-sdk-skills-bench/
├── README.md                        # this file
├── mosaic.toml                      # harbor-format-curation config
├── msbench-registration/            # files to PR into msbench-benchmarks
│   ├── benchmark_loaders.toml
│   └── dataset.jsonl                # 15 rows (3 scenarios × 5 SDKs)
├── shared/
│   ├── base/                        # shared base image (emulator + verifier deps)
│   │   ├── Dockerfile
│   │   └── start-emulator.sh
│   └── verifier/                    # grader library copied into every task image
│       ├── conftest.py
│       ├── check_api.py
│       ├── check_behavior.py         # concrete emulator+request behavioral suite
│       ├── check_cosmos.py
│       ├── check_source.py           # STATIC client-config signals (see docstring)
│       ├── check_advanced_source.py
│       ├── check_skills.py
│       └── runner.sh
├── runner-with-skills.sh            # Custom runner that loads cosmosdb-sdk skills
└── tasks/
    ├── mosaic-python/               # Scenario A: User profiles
    ├── mosaic-dotnet/
    ├── mosaic-java/
    ├── mosaic-nodejs/
    ├── mosaic-go/
    ├── ticketing-python/            # Scenario B: Event ticketing
    ├── ticketing-dotnet/
    ├── ticketing-java/
    ├── ticketing-nodejs/
    ├── ticketing-go/
    ├── iot-python/                  # Scenario C: IoT telemetry
    ├── iot-dotnet/
    ├── iot-java/
    ├── iot-nodejs/
    └── iot-go/
```

Each `mosaic-<sdk>/` task is a Harbor-format task directory:

```
mosaic-<sdk>/
├── task.toml                # Harbor metadata + timeouts + resources
├── instruction.md           # Problem statement shown to the agent. NO best-practice hints.
├── environment/
│   └── Dockerfile           # FROM cosmos-mosaic-base, adds the SDK runtime
├── solution/
│   └── solve.sh             # Oracle: cp -r /reference/* /app/
├── reference/               # Minimal reference impl baked into the image
│   └── ...
└── tests/
    ├── test.sh              # Harbor entrypoint. Starts emulator + app, runs pytest, writes reward.txt
    └── checks.py            # Per-task grader. Imports /verifier/* and gates by language.
```

## What gets evaluated

Per the spec, the grader scores these categories (see
[Coverage matrix](#coverage-matrix) for which categories run on which SDK):

1. **Live behavior (primary, hard to game)** — `check_behavior.py` builds
   and starts the app, drives the HTTP API, then **independently reads the
   Cosmos emulator with the verifier's own client** and asserts the two
   agree: every created user is a real Cosmos document (an in-memory /
   SQLite store that never writes to Cosmos fails here), the API read/list
   paths match the persisted documents, the partition-key value equals the
   user id, a duplicate `POST` is rejected without creating a second
   document, and the city filter returns exactly the matching rows. This is
   the defensible core — it proves runtime behavior, not source tokens.
2. **API conformance** — live HTTP probes of `/health`, `POST /users`,
   `GET /users/{id}`, `GET /users?city=...`. Right status codes, right
   payload shapes, right round-trip values.
3. **Cosmos data shape** — partition keys are userId-shaped (not `/id`,
   not `/city`), indexing policy present, throughput configured,
   documents carry a type discriminator + schemaVersion + ISO-8601
   `createdAt` + `interests` as a string array.
4. **Source-code best practices (secondary, static)** — singleton client,
   preferred regions (where the local rule covers the SDK), Direct
   connection mode for .NET and Java only, retry/resilience configured,
   diagnostics enabled, lifecycle/disposal handled. These are client-side
   configuration a single-node local emulator **cannot** prove
   behaviorally (lessons doc §15/§16), so they stay as source signals and
   are clearly labeled as such in `check_source.py`.
5. **Skills compliance** — no hardcoded account keys, endpoint read from
   env, no Python `ConnectionPolicy` mutation, no abandoned
   `Azure.Cosmos` preview package in .NET, latest non-deprecated SDK
   used in every SDK.
6. **Anti-gaming hygiene** — comments are stripped before the
   source-code regex checks, and required patterns demand real SDK
   identifiers, not just keywords.

## Reward model

Each task's `tests/test.sh` writes `0` or `1` to
`/logs/verifier/reward.txt`, per the Harbor contract. A run scores `1`
only when **every** mandatory check passes. The pytest run is
**verbose** even on success — the `/logs/verifier/` directory holds a
per-check log (`api.log`, `cosmos.log`, `source.log`, `skills.log`) so a
failing run is debuggable by inspecting which check rejected it.

> **Note:** If MSBench accepts graded float rewards (this is documented
> as a future direction in the wiki), the runner is easy to switch over.
> See `shared/verifier/runner.sh` for the conversion point.

## Coverage matrix

D = directly scored. N/A = explicitly out of
scope for this SDK in this benchmark.

| Category                              | Python | .NET | Java | Node.js | Go  |
|---------------------------------------|--------|------|------|---------|-----|
| API conformance                       | D      | D    | D    | D       | D   |
| Required user fields persist          | D      | D    | D    | D       | D   |
| Partition key choice (userId-shaped)  | D      | D    | D    | D       | D   |
| Indexing policy present               | D      | D    | D    | D       | D   |
| Throughput configured                 | D      | D    | D    | D       | D   |
| Type discriminator on docs            | D      | D    | D    | D       | D   |
| Schema versioning                     | D      | D    | D    | D       | D   |
| ISO-8601 `createdAt` stored as string | D      | D    | D    | D       | D   |
| `interests[]` stored as string array  | D      | D    | D    | D       | D   |
| Latest SDK package / version          | D      | D    | D    | D       | D   |
| Singleton client                      | D      | D    | D    | D       | D   |
| Preferred regions                     | D      | D    | D    | D       | N/A |
| Direct connection mode                | N/A    | D    | D    | N/A     | N/A |
| Retry / resilience                    | D      | D    | D    | D       | N/A |
| Diagnostics / logging                 | D      | D    | D    | D       | N/A |
| Lifecycle / disposal                  | D      | D    | D    | N/A     | N/A |
| No hardcoded account key              | D      | D    | D    | D       | D   |
| Endpoint from env                     | D      | D    | D    | D       | D   |
| Forbidden anti-patterns               | D      | D    | N/A  | N/A     | N/A |

## Container architecture

Each task image is built `FROM cosmos-mosaic-base`. The base image
contains:

- The Cosmos DB Linux **vnext** emulator binaries (small, fast startup,
  starts in the background; ENTRYPOINT is overridden so the verifier
  controls lifecycle).
- Python 3.12 + `pytest`, `requests`, `azure-cosmos`, `pyyaml` for the
  verifier (the verifier always runs in Python regardless of the SDK
  being evaluated).
- `/verifier/` — the shared grader library, copied in once.
- `/logs/verifier/` — the directory the reward + per-check logs are
  written to.
- `start-emulator.sh` — used by every task's `test.sh` to launch the
  emulator and wait for readiness.

Per-task images add only the SDK runtime (`python:3.12-slim`'s site
packages, `dotnet/sdk:8.0` layers, `eclipse-temurin:21-jdk`,
`node:20-bookworm`, `golang:1.22`) plus the per-task `/reference/`,
`/tests/`, `/instruction.md`, `/solution/`. The agent's workspace is
`/app/`.

## Building locally (Harbor)

The repository is laid out for `harbor-format-curation`. To build all
five images locally:

```bash
cd cosmos-sdk-skills-bench
harbor-format-curation import mosaic.toml
harbor-format-curation build --profile local mosaic.toml
harbor-format-curation update-database --profile local mosaic.toml
```

The vertical-slice walkthrough is documented in `tasks/mosaic-python/`.
That task was built first end-to-end to prove the architecture; the
other four follow the same pattern.

## Validating before merging

Per [Bring Your Own Benchmark Repository](https://github.com/devdiv-microsoft/MicrosoftSweBench/wiki/4.-Bring-Your-Own-Benchmark-Repository),
once your images are built and pushed you can run the benchmark
without contributing to `msbench-benchmarks`:

```bash
msbench-cli run \
  --config fix_validation \
  --benchmark cosmos-sdk-skills \
  --dataset msbench-registration/dataset.jsonl
```

## What is _not_ in this repo

- The Cosmos DB best-practices skill set itself. That lives in
  `cosmosdb-agent-kit/skills/cosmosdb-best-practices/` in the sibling
  repo. The benchmark only measures obedience to those rules; it does
  not own them.
- The local `cosmosdb-agent-kit/testing-v2/` harness. That is a
  separate, lighter-weight pytest harness for local iteration, not an
  MSBench benchmark.

## CI Pipeline (GitHub Actions)

A GitHub Actions workflow at `cosmosdb-agent-kit/.github/workflows/msbench-eval.yaml`
automates the evaluation loop:

```bash
# Single command runs all 15 instances × 3 independent attempts
msbench-cli run --benchmark cosmos-sdk-skills --repeat 3 --runner runner-with-skills.sh
```

**How it works:**
1. Workflow is triggered manually via `workflow_dispatch`
2. Authenticates to Azure (OIDC) and installs `msbench-cli`
3. Runs `scripts/msbench-eval.py` which submits one `--repeat 3` run
4. MSBench executes all 15 instances × 3 attempts = 45 tasks
5. Results are merged with `--merge pass_at_k` for per-instance reliability
6. If any instance's average pass rate < 90%, `scripts/create-skills-issue.py` creates a GitHub issue mapping failures to specific `sdk-*` rules

**Runner:** `runner-with-skills.sh` downloads and installs the `cosmosdb-sdk`
skill set before invoking the agent, so the agent has access to all 29 rules.
