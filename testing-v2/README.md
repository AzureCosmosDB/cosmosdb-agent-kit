# Cosmos DB Agent Kit — Testing Framework V2

This framework measures how well AI coding agents build Cosmos DB applications when given
the skills in this kit. It uses **contract-first testing**: API contracts and test suites
are defined *before* any code is generated, then an agent builds the app, and CI
automatically validates it. When tests fail, the agent evaluates the failures and creates
new rules to prevent them in future iterations.

## The Automated Loop

```
┌───────────────────────────────────────────────────────────────────────┐
│  1. CREATE ISSUE                                                      │
│     Open a "Run Test Iteration" issue, pick scenario + language.      │
│     Assign the issue to Copilot.                                      │
└───────────────────────┬───────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│  2. COPILOT GENERATES CODE                          [automated]       │
│     Copilot reads the skills, the scenario, and the API contract.     │
│     It generates a complete app in an iterations/ folder.             │
│     It opens a PR.                                                    │
└───────────────────────┬───────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│  3. CI TESTS THE APP                                [automated]       │
│     GitHub Actions starts the Cosmos DB emulator, builds the app,     │
│     launches it, and runs the pytest suite against the API contract.  │
│     Results are posted as a PR comment.                               │
└───────────────────────┬───────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│  4. EVALUATE FAILURES                               [one comment]     │
│     If tests failed, CI posts a ready-to-copy @copilot command.       │
│     Post it as a comment → Copilot evaluates failures, creates new    │
│     rules in skills/cosmosdb-best-practices/rules/, regenerates       │
│     AGENTS.md, updates IMPROVEMENTS-LOG.md, and commits to the PR.   │
└───────────────────────┬───────────────────────────────────────────────┘
                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│  5. MERGE AND CONTINUE                                                │
│     Review the PR and merge.                                          │
│     Run more iterations — the same scenario in a different language,  │
│     or the same language again. Since agent code generation is        │
│     non-deterministic, each iteration may produce different results   │
│     and surface new gaps.                                             │
└───────────────────────────────────────────────────────────────────────┘
```

**Your manual work per iteration:**
1. Create an issue and assign to Copilot (step 1)
2. After CI runs, copy-paste comment(s) to trigger Copilot (steps 3–4)

Most of the loop is automated, but **some copy-paste steps are unavoidable** due to a
GitHub platform limitation:

> **Why can't this be fully automated?** The Copilot coding agent only responds to
> `@copilot` mentions posted by a **human user**. Bot-posted mentions (from CI workflows
> using `GITHUB_TOKEN`) are ignored — GitHub designed this to prevent infinite bot loops.
> A Personal Access Token (PAT) could work around this, but PATs carry security risks
> (broad repo access, no fine-grained scoping for PR comments) and would need to be
> stored as a repository secret. For now, the copy-paste approach is safer and more
> transparent.

**What you must do manually:**
- **Approve workflow runs**: Every time Copilot pushes a commit to the PR, GitHub requires
  you to click **"Approve workflows to run"** on the PR's Checks tab. This is a GitHub
  Actions security feature for `pull_request_target` workflows — it treats the Copilot app
  as an external contributor whose workflows need manual approval each time.
- **Build/startup failure**: CI posts a `@copilot` fix prompt → copy-paste it as a new comment.
  (Copilot may also auto-retry by reading the failed CI check logs, but copy-paste is the
  reliable fallback.)
- **Test failures (skills run)**: CI posts a `@copilot` evaluation prompt → copy-paste it.
  Copilot fixes code + creates rules, CI re-runs automatically.
- **Deep evaluation**: CI posts a `@copilot` deep evaluation prompt → copy-paste it.
  This produces a thorough ITERATION.md with per-category analysis.
- **Test failures (control run)**: CI posts a `@copilot` fix prompt → copy-paste it.
  Copilot fixes code only (no rule creation).

**Automated re-triggering**: When Copilot pushes fixes to the PR branch, CI re-runs
automatically via `pull_request_target` — but you still need to **approve the workflow**
each time. The `auto-trigger-tests.yaml` bridge handles the trigger; the approval gate is
the manual step. For control runs the deep evaluation commit includes `[skip ci]` to
prevent unnecessary re-runs.

### The Key Insight

Tests are written against a **fixed API contract**, not against the generated code. The agent
is told exactly which endpoints, paths, field names, and status codes to implement. This makes
testing deterministic regardless of what the agent produces.

---

## Quick Start

### Prerequisites

- A **fork** of this repository (see [Fork Requirement](#fork-requirement) below)
- [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) enabled on your fork
- The branch containing this framework set as the **default branch** (so Copilot and issue templates can find the files)

### Fork Requirement

**⚠️ You must run the batch testing pipeline from a fork**, not directly in the upstream repo.

**Why?** The upstream repository (AzureCosmosDB/cosmosdb-agent-kit) has an enterprise-level
policy that blocks GitHub Actions workflows from creating or approving pull requests. This policy
exists for security — it prevents Actions workflows from automatically merging code without human
review.

However, the batch testing pipeline needs to create a **summary PR** to aggregate results from
multiple iterations. Since this is blocked in the upstream repo, the workflow cannot complete
automatically there.

**The workflow:**

1. **Fork the repo to your personal account** (or organization)
2. **Run the batch tests in your fork** — here, Actions has write permissions, so the full automation works
3. **Generate quality results** — after multiple iterations, the workflow creates a summary PR with aggregated findings and recommendations
4. **Open a PR to upstream** with your summary findings and any new rules you've created
5. **Upstream maintainers review and merge** your contributions

**In short:** Forks are where the experiments happen; PRs to upstream are where validated
findings get merged. This separation ensures all code going into the upstream repo has been
reviewed by humans, while still enabling fully automated experimentation in your fork.



### Run Your First Iteration

1. Go to **Issues** → **New Issue** → select **"Run Test Iteration"**
2. Pick a scenario (e.g., `gaming-leaderboard`) and a language (e.g., `python`)
3. Click **Submit new issue**
4. **Assign the issue to `copilot`** (the GitHub Copilot bot user)
5. Wait — Copilot will open a PR with generated code
6. CI runs automatically on the PR and posts test results as a comment
7. If tests failed, CI also posts a second comment with a ready-to-copy `@copilot` evaluation command — post it as a new comment to trigger evaluation
8. Review the results and merge, or open another iteration

### Create a New Scenario

1. Go to **Issues** → **New Issue** → select **"Create New Scenario"**
2. Fill in the scenario name, description, entities, and endpoints
3. **Assign the issue to `copilot`**
4. Copilot will follow the recipe in `testing-v2/CREATE-SCENARIO.md` and open a PR with the complete scenario (contract, tests, prompts, directory structure)

### Pushing Findings Back to Upstream

Once you've completed a batch test in your fork and generated a summary PR with findings and rules:

1. **Review the summary PR** to verify the findings and any new rules created
2. **Merge the summary PR** into your fork's main branch (if the workflow couldn't create it automatically, you can manually create the PR from the prepared branch)
3. **Create a PR to the upstream repo** (AzureCosmosDB/cosmosdb-agent-kit):
   - Base: `AzureCosmosDB/cosmosdb-agent-kit/main`
   - Head: `YourUserName/cosmosdb-agent-kit/batch-XXXXXX-...` (your fork's batch results branch)
   - Title: Use the batch summary title (e.g., "batch: gaming-leaderboard aggregate results — skills loaded (python)")
   - Body: Copy the aggregated results and evaluation findings from your summary PR
4. **Add context** explaining:
   - Which scenario and language(s) were tested
   - Whether skills were loaded (control vs skills run)
   - Any key findings or patterns discovered
5. **Upstream maintainers review and merge** your findings into the official repository

This workflow ensures that all code, rules, and improvements in the upstream repo have been
validated experimentally in a fork first, then reviewed by maintainers before merging.

---

## Directory Layout

```
testing-v2/
├── README.md                              # This file
├── CREATE-SCENARIO.md                     # Recipe: how to create a new scenario
├── EVALUATE.md                            # Recipe: how to evaluate failures and create rules
├── IMPROVEMENTS-LOG.md                    # Log of discovered gaps and new rules
├── harness/                               # Shared test infrastructure (Python)
│   ├── aggregate.py                       # Batch results aggregation (mean/stddev/consistency)
│   ├── conftest_base.py                   # Shared pytest fixtures
│   ├── report.py                          # Structured JSON/Markdown report generation
│   └── requirements.txt                   # Python dependencies for test runner
├── scenarios/
│   ├── _scenario-template.md              # Template for new scenarios
│   ├── _iteration-template.md             # Template for iteration docs
│   ├── _iteration-config-template.yaml    # Template for iteration-config.yaml
│   ├── gaming-leaderboard/                # Reference scenario
│   │   ├── SCENARIO.md                    # Requirements + per-language prompts
│   │   ├── api-contract.yaml              # API specification
│   │   └── tests/                         # pytest suite
│   │       ├── conftest.py                # Fixtures and test data
│   │       ├── test_api_contract.py       # HTTP contract tests
│   │       ├── test_data_integrity.py     # Cosmos DB verification tests
│   │       └── test_cosmos_infrastructure.py  # Infrastructure & SDK tests
│   ├── ecommerce-order-api/               # 7 endpoints, order lifecycle
│   ├── iot-device-telemetry/              # 9 endpoints, time-series + aggregation
│   ├── ai-chat-rag/                       # 8 endpoints, RAG with vector search
│   └── multitenant-saas/                  # 13 endpoints, tenant isolation
```

**What Copilot creates per iteration:**

```
scenarios/gaming-leaderboard/iterations/
  └── iteration-001-python/
      ├── iteration-config.yaml    # Build/run config (REQUIRED by CI)
      ├── main.py                  # Application source code
      ├── requirements.txt         # App dependencies
      └── ...                      # Other app files
```

---

## How Each Piece Works

### Issue Templates

| Template | File | Purpose |
|----------|------|---------|
| Run Test Iteration | `.github/ISSUE_TEMPLATE/run-iteration.yml` | Trigger code generation for a scenario + language |
| Batch Test | `.github/ISSUE_TEMPLATE/batch-test.yml` | Run N independent iterations for statistical significance |
| Create New Scenario | `.github/ISSUE_TEMPLATE/create-scenario.yml` | Trigger scenario creation from a description |

Both templates include an **Agent Instructions** section in the issue body that tells Copilot
exactly what to do when assigned.

### Copilot Instructions

`.github/copilot-instructions.md` provides repo-level instructions to the Copilot coding agent.
It tells Copilot how to handle each type of issue and where to find the recipe files.

### Recipe Files

| File | Purpose |
|------|---------|
| `testing-v2/CREATE-SCENARIO.md` | Step-by-step recipe for creating a new scenario — directory structure, api-contract.yaml format, test patterns, SCENARIO.md prompts |
| `testing-v2/EVALUATE.md` | Step-by-step recipe for evaluating test failures — classification categories, rule creation format, IMPROVEMENTS-LOG.md format, scoring guide |

These are machine-readable instruction documents. The coding agent follows them literally.

### CI Workflow

`.github/workflows/test-iteration.yaml` triggers on any PR that modifies files under
`testing-v2/scenarios/*/iterations/**`. It:

1. Detects which scenario and iteration changed (from file paths in the PR diff)
2. Starts the Cosmos DB Linux emulator as a Docker service container
3. Reads `iteration-config.yaml` for language, build command, run command, and port
4. Sets up the language toolchain (Python, .NET, Java, Node.js, Go)
5. Builds and starts the app
6. Waits for the `/health` endpoint to return 200
7. Runs `pytest` against the scenario's test suite
8. Posts a structured results comment on the PR
9. If tests failed, posts a second comment with a ready-to-copy `@copilot` evaluation command

### API Contracts

Each scenario has an `api-contract.yaml` defining every endpoint, field name, type, status code,
and error response. Tests are written against this contract. Agent prompts include it verbatim
in a **CRITICAL: API Contract Requirements** block.

### Test Categories

Each scenario has up to 4 categories of tests, each measuring a different layer:

| Category | File | What It Measures | Signal Source |
|----------|------|-----------------|---------------|
| **API Contract** | `test_api_contract.py` | HTTP endpoints match the contract: correct paths, status codes, field names, types | Functional correctness — catches wrong routes, missing fields |
| **Data Integrity** | `test_data_integrity.py` | Data round-trips correctly through the API: writes match reads, relationships hold | Logical correctness — catches inconsistent data, orphaned refs |
| **Robustness** | `test_robustness.py` | Error handling and edge cases: bad input, missing items, concurrent updates | Defensive coding — catches missing validation, bad error codes |
| **Cosmos Infrastructure** | `test_cosmos_infrastructure.py` | Below-the-HTTP-surface quality: partition keys, indexing, serialization, SDK patterns | **Skills effectiveness** — catches anti-patterns that HTTP tests miss |

The first three categories test what the API does; the fourth tests _how_ the app is built.

#### Why Cosmos Infrastructure Tests Matter

HTTP contract tests only verify *what* the API returns — correct routes, status codes, and field names.
An agent can produce a working API that passes every contract test yet still be poorly built: using
`/id` as the partition key, missing composite indexes, storing enums as integers, or not using ETag
concurrency. Infrastructure tests catch these problems by connecting directly to Cosmos DB and
inspecting the containers, indexing policies, and stored documents.

**How this creates differentiation between control and skills runs:**

The key insight is that an agent without skills doesn't know Cosmos DB best practices, so it makes
reasonable-but-wrong choices that HTTP tests can't detect. Infrastructure tests expose these gaps:

| What Infrastructure Tests Check | Without Skills (typical) | With Skills (typical) |
|--------------------------------|--------------------------|----------------------|
| Composite indexes for filter+sort queries | ❌ Missing — agent doesn't know `WHERE x ORDER BY y` needs a composite index | ✅ Present — `index-composite` rule explicitly says to add them |
| `type` discriminator field in documents | ❌ Missing — agent only adds polymorphism fields for multi-type containers | ✅ Present — `model-type-discriminator` rule says to add to ALL containers |
| `schemaVersion` field in documents | ❌ Missing or wrong name (e.g., `_schemaVersion`) | ✅ Present with correct name — `model-schema-versioning` rule specifies `schemaVersion` |
| Jackson/JSON serialization of Cosmos system fields | ❌ Crashes on `_rid`, `_self`, `_ts` — agent forgets `FAIL_ON_UNKNOWN_PROPERTIES=false` | ✅ Configured correctly — `sdk-java-cosmos-config` rule covers this |
| Enums stored as strings (not integers) | ❌ Sometimes stored as ordinals | ✅ Always strings — `model-json-serialization` rule covers enum handling |
| ETag-based optimistic concurrency | ❌ Often missing | ✅ Present — `sdk-etag-concurrency` rule provides patterns |

**Concrete example from real test runs (ecommerce-order-api, Java):**

- **Control run (no skills)**: 39/91 tests passed (42.9%). The agent produced a working Spring Boot
  app with correct routes, but Jackson `ObjectMapper` without `FAIL_ON_UNKNOWN_PROPERTIES=false`
  caused all Cosmos DB read operations to crash on system fields (`_rid`, `_self`, `_etag`, `_ts`).
  This single missing SDK configuration cascaded into ~40 test failures across all categories.
  Infrastructure tests also caught: no composite indexes, no type discriminator, no schema version.

- **With-skills run**: 86/91 tests passed (94.5%). The same scenario with skills loaded produced
  correct SDK configuration, proper indexing, and document structure. The 5 remaining failures were
  minor (3 infrastructure gaps fixed post-evaluation, 1 test isolation issue, 1 skip).

The infrastructure tests are what make the 42.9% → 94.5% gap visible. Without them, both runs
would have similar pass rates on HTTP-only tests (since the core HTTP contract logic is not the
differentiator — it's the Cosmos DB configuration underneath).

### Build & Startup Signals

CI captures build and startup attempt results as structured JSON files, independent of whether
the build ultimately succeeds (after retries). These signals measure first-attempt quality.

**How build signals are collected:**

1. The CI workflow runs the build command from `iteration-config.yaml` (e.g., `mvn package -DskipTests`)
2. It captures stdout, stderr, and exit code into `build-signal.json`:
   ```json
   {
     "build_command": "mvn package -DskipTests",
     "exit_code": 0,
     "succeeded": true,
     "stdout_tail": "... BUILD SUCCESS ...",
     "stderr_tail": ""
   }
   ```
3. Similarly, `startup-signal.json` records whether the app started and responded to `/health`

**How signals affect scoring:**

- A **build failure** on the first attempt incurs a -1 point penalty in the overall score.
  Even if the Copilot agent fixes the build in a subsequent commit, the penalty remains because
  the initial failure reveals a gap in the agent's knowledge (missing dependency, wrong version,
  SDK misconfiguration) that the skills should have prevented.
- A **startup failure** similarly incurs a -1 point penalty.
- These signals are recorded in `ITERATION.md` alongside test results for comparison across iterations.

**Why this matters for differentiation:**

An agent with skills loaded gets explicit guidance on Maven dependencies, SSL configuration,
Spring Boot properties, and SDK versions. An agent without skills may produce code that compiles
but fails at startup due to missing SSL trust configuration for the Cosmos DB emulator, or uses
an incompatible dependency version. The build/startup signal captures these first-attempt failures
even when the agent eventually self-corrects.

---

## The Evaluation Feedback Loop

When tests fail, each failure is a signal that can improve the skill set:

| Failure Category | What Happened | Action |
|-----------------|---------------|--------|
| **Contract violation** | Code doesn't match the API contract (wrong path, missing field, wrong status code) | Fix the generated code |
| **Cosmos DB anti-pattern** | Code works but uses a bad practice (e.g., `/id` as partition key) | Create a **new rule** |
| **Unclear existing rule** | A rule exists but the agent didn't follow it | **Update the rule** to be clearer |
| **SDK/framework quirk** | Language-specific SDK issue | Create an `sdk-*` rule |
| **Test too strict** | Test assertion is unreasonable | Fix the test (rare) |

The full evaluation process is documented in `testing-v2/EVALUATE.md`. The Copilot agent
follows this recipe when asked to evaluate failures on a PR.

### Example Cycle

1. **Iteration 001 (Python)**: Agent uses `/id` as sole partition key
   → `test_no_id_only_partition_key` fails
2. **Evaluation**: Copilot classifies this as "Cosmos DB anti-pattern"
3. **Rule created**: `rules/partition-avoid-id-only.md`, `npm run build` regenerates AGENTS.md
4. **Iteration 002 (Python)**: Agent loads the updated rules → partition key test passes
5. **Logged**: Entry added to `testing-v2/IMPROVEMENTS-LOG.md`

### Control Run vs Skills Run — Different Workflows

The framework treats control runs and skills runs differently:

**Control run (no skills loaded):**
```
Agent generates code → CI runs tests → CI posts results
→ User triggers deep evaluation → Copilot analyzes code
→ Copilot identifies which EXISTING rules would have helped
→ Copilot commits analysis with [skip ci] → DONE (no iteration)
```
- Source code is **always zipped immediately** — no iteration will follow
- Deep evaluation is analysis-only: Copilot does NOT fix code or create rules
- The commit includes `[skip ci]` to prevent CI from re-running

**Skills run (skills loaded):**
```
Agent generates code → CI runs tests → CI posts results
→ User triggers deep evaluation → Copilot analyzes code
→ Copilot fixes code + creates new rules + runs npm run build
→ Copilot commits → CI re-runs tests automatically
→ Repeat until all tests pass → Source code gets zipped
```
- Source code is **only zipped when all tests pass** — Copilot needs the raw files to iterate
- Deep evaluation includes code fixes and rule creation
- The commit does NOT include `[skip ci]` — we want CI to re-test the fixes
- When new rules are created, `npm run build` regenerates `AGENTS.md` (the compiled rules file)
- `SKILL.md` does not need updating — it's a static entry point; new rules are picked up
  automatically through the build process

---

## Batch Testing (Statistical Significance)

Single-run comparisons between skills and control are unreliable due to LLM stochasticity —
the same agent can produce wildly different code quality across runs. Batch testing solves
this by running N independent iterations of the same scenario and aggregating the results.

### Why Batch Testing?

In real testing, we observed:
- **Control run**: 96.7% pass rate (agent got lucky — every endpoint worked perfectly)
- **Skills run**: 89.0% pass rate (agent had a bug in one endpoint — 8 cascading failures)

The skills run was actually *better* on infrastructure tests (composite indexes, document
structure) but scored lower overall due to one stochastic LLM failure. With N=5 iterations,
these random variations average out, revealing the true signal.

### Architecture: 5+1 PR Pattern

```
┌─────────────────────────────────────────────┐
│  1. CREATE BATCH ISSUE                       │
│     Fill in scenario, language, skills, N     │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  2. COMMENT "/batch-start"                   │
│     Automatically creates N child issues      │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  3. ASSIGN @copilot TO EACH CHILD ISSUE      │
│     Copilot generates code from scratch       │
│     → opens PR → CI tests it                  │
│     (approve workflow runs for each PR)        │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  4. POST "/aggregate 60,61,62,63,64"         │
│     Comment on the parent batch issue         │
│     Downloads artifacts from all N PRs        │
│     Computes mean/stddev/min/max pass rate    │
│     Creates summary PR with BATCH-RESULTS     │
│     Closes the N child PRs                    │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│  5. DEEP EVALUATION                          │
│     Copy-paste @copilot prompt from summary   │
│     PR → Copilot analyzes consistent failures │
│     → creates/updates rules → commits to PR   │
└─────────────────────────────────────────────┘
```

### Running a Batch Test

#### Step 1: Create the batch issue

Go to **Issues** → **New Issue** → select **"Batch Test (Multiple Iterations)"**.
Pick scenario, language, skills (yes/no), and number of iterations (3, 5, or 7). Submit.

#### Step 2: Comment `/batch-start`

Comment **`/batch-start`** on the batch issue. This creates N child issues,
each with pre-assigned iteration directories and full instructions.

#### Step 3: Assign Copilot to each child issue

Go to each child issue (linked in the summary comment) and assign **@copilot**.
Copilot generates code and opens a PR for each one.

#### Step 4: Approve workflow runs

Each PR triggers CI via `pull_request_target`, which requires manual approval.
Go to **Actions**, find the pending runs, and approve each one.

#### Step 5: Wait for test results

After approval, CI runs tests and posts results on each PR. Wait until every PR
shows a test results comment.

#### Step 6: Trigger aggregation

Post a comment **on the parent batch issue** with the child issue numbers.
The exact command is pre-filled in the summary comment posted when the
children were created — just copy and paste it:

```
/aggregate 60,61,62,63,64
```

The workflow automatically resolves each child issue to its PR, then:
- Downloads `test-report.json` artifacts from each child PR's CI run
- Computes aggregate statistics (mean, stddev, min, max)
- Creates a summary PR with `BATCH-RESULTS.md`
- Closes all child PRs and deletes their branches
- Posts the aggregate summary on the parent batch issue
- Posts a ready-to-copy `@copilot` deep evaluation prompt on the summary PR

#### Step 7: Deep evaluation

The aggregation workflow posts a comment on the summary PR with a ready-to-copy
`@copilot` evaluation prompt. Copy-paste it as a new comment on the summary PR.
Copilot will:

- Read the `BATCH-RESULTS.md` aggregate data
- Focus on **consistently-failing tests** (not flaky ones)
- Classify each failure per `testing-v2/EVALUATE.md`
- Create or update rules for real skill gaps (skills runs only)
- Update `testing-v2/IMPROVEMENTS-LOG.md`
- Commit everything to the summary PR branch

> **Alternative:** You can also trigger aggregation from **Actions** → **Aggregate Batch
> Results** → **Run workflow**, entering the batch issue number and child issue numbers.

### Batch Results Output

The aggregate analysis includes:

| Section | What It Shows |
|---------|--------------|
| **Aggregate Summary** | Mean/stddev/min/max for pass rate and score across N iterations |
| **Per-Iteration Results** | Individual pass rate and score for each run |
| **Category Breakdown** | Mean/stddev per test category (api_contract, cosmos_infrastructure, etc.) |
| **Test Consistency** | Classifies each test as always-pass, always-fail, or flaky |
| **Statistical Assessment** | Confidence level based on standard deviation |

**Test Consistency** is the most valuable output — it separates real gaps from noise:

- **Always-fail tests**: These indicate a genuine skills gap (or contract misunderstanding)
  that skills should address
- **Always-pass tests**: Reliable baseline — both skills and control handle these
- **Flaky tests**: LLM stochasticity — these tests pass in some iterations but not others,
  indicating the failure is random rather than systematic

### Comparing Skills vs. Control

Run two batch tests for the same scenario + language:
1. Batch with `skills=yes` (N iterations)
2. Batch with `skills=no` (N iterations)

Then compare the aggregate means. With N=5, a difference greater than 2× the pooled
standard deviation is likely a real effect of the skills, not noise.

### Issue Templates and Workflows

| Template/Workflow | File | Purpose |
|-------------------|------|---------|
| Batch Test | `.github/ISSUE_TEMPLATE/batch-test.yml` | Create parent tracking issue |
| Create Batch Children | `.github/workflows/create-batch-children.yaml` | Creates N child issues from a batch issue |
| Aggregate Batch Results | `.github/workflows/aggregate-batch.yaml` | Collects results, creates summary PR, closes children |
| Aggregate Script | `testing-v2/harness/aggregate.py` | Computes statistics from multiple test-report.json files |

---

## Available Scenarios

| Scenario | Endpoints | Domain | Key Challenges |
|----------|-----------|--------|----------------|
| `gaming-leaderboard` | 7 | Gaming | Ranking queries, score aggregation, partitioning for leaderboards |
| `ecommerce-order-api` | 7 | E-commerce | Order lifecycle, inventory, transactional consistency |
| `iot-device-telemetry` | 9 | IoT | Time-series data, aggregation, high-volume ingestion |
| `ai-chat-rag` | 8 | AI/RAG | Vector search, conversation history, document chunking |
| `multitenant-saas` | 13 | SaaS | Tenant isolation, hierarchical partition keys, cross-tenant queries |

Each scenario has a `SCENARIO.md` with full requirements and prompts for 5+ languages.

---

## Running Tests Locally

Useful for debugging failures or developing new test cases without waiting for CI.

### Prerequisites

1. **Cosmos DB Emulator** running on `https://localhost:8081`
   ```bash
   # Docker (Linux emulator)
   docker run -d -p 8081:8081 -p 10250-10255:10250-10255 \
     mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
   ```
   Or use the [Windows emulator](https://learn.microsoft.com/en-us/azure/cosmos-db/local-emulator).

2. **Python 3.10+** with test dependencies:
   ```bash
   pip install -r testing-v2/harness/requirements.txt
   ```

3. **Your app** built and running on the configured port.

### Running Tests

```bash
cd testing-v2/scenarios/gaming-leaderboard/

# Point to the iteration
export ITERATION_DIR=iterations/iteration-001-python   # Linux/Mac
$env:ITERATION_DIR="iterations/iteration-001-python"   # PowerShell

# Run all tests
pytest tests/ -v

# Run only contract tests
pytest tests/test_api_contract.py -v

# Run only data integrity tests
pytest tests/test_data_integrity.py -v

# Run only infrastructure/SDK tests
pytest tests/test_cosmos_infrastructure.py -v

# Run a specific test class
pytest tests/test_api_contract.py::TestGlobalLeaderboard -v
```

If your app is already running (skip the harness's app startup):
```bash
APP_ALREADY_RUNNING=1 APP_PORT=8000 pytest tests/ -v
```

---

## Testing in a Fork

To test the full loop in your own fork:

1. **Push this branch** to your fork
2. **Set the branch as the default** in your fork's Settings → General → Default branch
   - This is required because issue templates and `.github/copilot-instructions.md` are read from the default branch
3. **Enable Copilot coding agent** on the fork (if not already enabled)
4. **Create an issue** using the "Run Test Iteration" template
5. **Assign it to Copilot** — the loop runs entirely within your fork

CI triggers on PRs within your fork. It never touches the upstream repo.

---

## Supported Languages

The test runner is always Python (pytest + requests). The **app under test** can be any language:

| Language | Framework | Port | Build | Run |
|----------|-----------|------|-------|-----|
| Python | FastAPI | 8000 | `pip install -r requirements.txt` | `uvicorn main:app --port 8000` |
| .NET 8 | ASP.NET Web API | 5000 | `dotnet build` | `dotnet run` |
| Java | Spring Boot 3 | 8080 | `mvn package -DskipTests` | `java -jar target/*.jar` |
| Node.js | Express | 3000 | `npm install` | `node server.js` |
| Go | Gin | 8080 | `go build -o server .` | `./server` |

Configure per-iteration via `iteration-config.yaml`.

---

## File Reference

| File | Purpose | Who Manages |
|------|---------|-------------|
| `.github/ISSUE_TEMPLATE/run-iteration.yml` | Issue form: trigger an iteration | Maintainer |
| `.github/ISSUE_TEMPLATE/create-scenario.yml` | Issue form: create a new scenario | Maintainer |
| `.github/workflows/test-iteration.yaml` | CI pipeline: build, test, report | Maintainer |
| `.github/copilot-instructions.md` | Repo-level Copilot agent instructions | Maintainer |
| `testing-v2/CREATE-SCENARIO.md` | Recipe for scenario creation | Maintainer |
| `testing-v2/EVALUATE.md` | Recipe for failure evaluation + rule creation | Maintainer |
| `testing-v2/IMPROVEMENTS-LOG.md` | Log of discovered gaps and rules created | Agent + Human |
| `testing-v2/harness/conftest_base.py` | Shared pytest fixtures (including Cosmos DB direct access) | Maintainer |
| `testing-v2/harness/evaluate.py` | Automated evaluation and ITERATION.md generation | Maintainer |
| `testing-v2/harness/report.py` | Structured JSON + Markdown test reports with category breakdowns | Maintainer |
| `scenarios/<name>/api-contract.yaml` | API spec (tests validate against this) | Created at scenario setup |
| `scenarios/<name>/tests/*.py` | pytest test suite | Created at scenario setup |
| `scenarios/<name>/SCENARIO.md` | Requirements + agent prompts | Created at scenario setup |
| `scenarios/<name>/iterations/*/iteration-config.yaml` | Build/run config for one iteration | Agent |
| `skills/cosmosdb-best-practices/rules/*.md` | Individual best-practice rules | Agent (via evaluation) |
| `skills/cosmosdb-best-practices/AGENTS.md` | Compiled rules (generated by `npm run build`) | Generated |

---

## Build Commands

```bash
# Compile rules into AGENTS.md (run after adding/editing rules)
npm run build

# Validate rule files
npm run validate
```
