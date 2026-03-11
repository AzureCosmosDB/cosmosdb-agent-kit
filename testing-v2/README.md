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
2. After CI runs, copy-paste one comment to trigger evaluation (step 4)

Everything else — code generation, testing, failure analysis, rule creation — is automated.

### The Key Insight

Tests are written against a **fixed API contract**, not against the generated code. The agent
is told exactly which endpoints, paths, field names, and status codes to implement. This makes
testing deterministic regardless of what the agent produces.

---

## Quick Start

### Prerequisites

- A GitHub repository with this code (your fork or the upstream repo)
- [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent) enabled on the repo
- The branch containing this framework set as the **default branch** (so Copilot and issue templates can find the files)

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

---

## Directory Layout

```
testing-v2/
├── README.md                              # This file
├── CREATE-SCENARIO.md                     # Recipe: how to create a new scenario
├── EVALUATE.md                            # Recipe: how to evaluate failures and create rules
├── IMPROVEMENTS-LOG.md                    # Log of discovered gaps and new rules
├── harness/                               # Shared test infrastructure (Python)
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
│   │       └── test_data_integrity.py     # Cosmos DB verification tests
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
| `testing-v2/harness/conftest_base.py` | Shared pytest fixtures | Maintainer |
| `testing-v2/harness/report.py` | Structured JSON + Markdown test reports | Maintainer |
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
