# Recipe: Create a New Test Scenario

This document tells a coding agent (or human) exactly how to create a new test scenario
for the Cosmos DB Agent Kit testing framework. Follow every step — the result must match
the format of existing scenarios so CI and the evaluation loop work correctly.

## Reference Implementation

Use `testing-v2/scenarios/gaming-leaderboard/` as your format reference for every file.
Read its files before generating anything.

## Inputs

You need these inputs (from the GitHub issue or the human):

1. **Scenario name** — kebab-case (e.g., `healthcare-appointments`)
2. **Description** — what the app does
3. **Entities** — data model with key fields
4. **Endpoints** — HTTP methods, paths, descriptions
5. **Expected scale** — data volumes and query patterns (optional)

## Step-by-Step

### 1. Create the directory structure

```
testing-v2/scenarios/<scenario-name>/
├── api-contract.yaml
├── SCENARIO.md
├── tests/
│   ├── conftest.py
│   ├── test_api_contract.py
│   └── test_data_integrity.py
└── iterations/
    └── .gitkeep
```

### 2. Generate `api-contract.yaml`

This is the most important file — everything else derives from it.

**Format rules:**
- Start with `name:` and `version: "1.0"`
- Include a `health:` section (GET /health → 200)
- List every endpoint under `endpoints:` with:
  - `method:` (GET, POST, PUT, PATCH, DELETE)
  - `path:` (exact path with `{param}` placeholders)
  - `description:`
  - `request.body.required:` and `request.body.properties:` (for POST/PUT/PATCH)
  - `parameters:` for path and query params
  - `response.status:` (201 for POST create, 200 for GET/PUT/PATCH, 204 for DELETE)
  - `response.body:` with `required:` fields and `properties:` with types
  - `errors:` for expected error responses (404 etc.)
- Use **camelCase** for all JSON field names
- Specify field `type:` as: string, integer, number, boolean, array, object
- Add `description:` to non-obvious fields
- For array responses, use `type: array` with `items:` containing `required:` and `properties:`

**Example structure** (reference `gaming-leaderboard/api-contract.yaml`):
```yaml
name: healthcare-appointments
version: "1.0"

health:
  path: /health
  method: GET
  response:
    status: 200

endpoints:
  create_patient:
    method: POST
    path: /api/patients
    description: Create a new patient record
    request:
      body:
        required:
          - patientId
          - name
          - email
        properties:
          patientId:
            type: string
          name:
            type: string
          email:
            type: string
    response:
      status: 201
      body:
        required:
          - patientId
          - name
          - email
        properties:
          patientId:
            type: string
          name:
            type: string
          email:
            type: string
    errors:
      - status: 409
        description: Patient already exists
```

### 3. Generate `tests/conftest.py`

**Must contain:**

```python
"""
Scenario-level conftest for <scenario-name> tests.
"""

import sys
from pathlib import Path

# Add harness to path
harness_dir = Path(__file__).resolve().parent.parent.parent.parent / "harness"
sys.path.insert(0, str(harness_dir))

from conftest_base import *  # noqa: F401,F403

import pytest


# Scenario-specific fixtures below
```

**Then add fixtures for:**
- `test_<entities>` — Hardcoded test data (deterministic, not random). Include 3–5 items minimum.
- `seeded_data` — A session-scoped fixture that creates all test data via the API and returns it.
  Use `api.request("POST", "/api/...", json=data)` and assert `201` responses.
  This fixture is called once before tests that need pre-existing data.

**Key rules for fixtures:**
- All test data is **hardcoded** — no `uuid.uuid4()`, no `random`, no `faker`
- IDs should be descriptive: `"patient-001"`, `"provider-alpha"`
- Design data so assertions are deterministic (e.g., known sort orders)
- Scope is `session` for all fixtures used across test classes

### 4. Generate `tests/test_api_contract.py`

**Structure: one test class per endpoint group.**

```python
"""
API Contract Tests for <Scenario Name>
"""

import pytest

class TestHealth:
    def test_health_returns_200(self, api):
        resp = api.request("GET", "/health")
        assert resp.status_code == 200

class TestCreatePatient:
    def test_create_returns_201(self, api):
        resp = api.request("POST", "/api/patients", json={...})
        assert resp.status_code == 201

    def test_response_has_required_fields(self, api):
        resp = api.request("POST", "/api/patients", json={...})
        body = resp.json()
        required = ["patientId", "name", "email"]
        missing = [f for f in required if f not in body]
        assert not missing, (
            f"Response missing required fields: {missing}. "
            f"See api-contract.yaml create_patient.response.body.required"
        )

    def test_not_found_returns_404(self, api):
        resp = api.request("GET", "/api/patients/nonexistent")
        assert resp.status_code == 404
```

**Rules for tests:**
- Use the `api` fixture for HTTP requests and `seeded_data` fixture for tests that need data
- One `TestClassName` per endpoint group (e.g., `TestCreatePatient`, `TestGetPatient`, `TestSearchProviders`)
- Always test: correct status code, required fields present, correct field types, 404 for missing items
- Assertion messages must reference `api-contract.yaml` and be actionable
- For list/search endpoints, test filtering, pagination (if applicable), and empty results
- Use unique IDs per test to avoid conflicts (e.g., `"test-create-001"`, `"test-create-002"`)
- Tests that need seeded data should declare the `seeded_data` fixture as a parameter

### 5. Generate `tests/test_data_integrity.py`

```python
"""
Data Integrity Tests for <Scenario Name>
"""

import pytest

class TestDataPersistence:
    def test_documents_exist_in_cosmos(self, api, seeded_data, cosmos_database):
        containers = list(cosmos_database.list_containers())
        assert len(containers) > 0

    def test_database_is_created(self, cosmos_database):
        props = cosmos_database.read()
        assert props is not None

class TestPartitionKeyDesign:
    def test_containers_have_partition_keys(self, cosmos_database):
        for container_props in cosmos_database.list_containers():
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            assert len(paths) > 0

    def test_no_id_only_partition_key(self, cosmos_database):
        for container_props in cosmos_database.list_containers():
            pk = container_props.get("partitionKey", {})
            paths = pk.get("paths", [])
            for path in paths:
                assert path != "/id", (
                    f"Container uses /id as partition key — this causes hot partitions. "
                    f"See rule: partition-avoid-hotspots"
                )
```

**Keep these tests generic.** They check Cosmos DB design regardless of the scenario.
Add scenario-specific data integrity tests only when relevant (e.g., checking multi-tenant isolation).

### 6. Generate `SCENARIO.md`

Follow the exact structure of `gaming-leaderboard/SCENARIO.md`. It must contain:

1. **Overview** — What the app does
2. **Language Suitability** table — All 6 languages
3. **Requirements** — Functional and technical
4. **Data Model** — Entities and their relationships, expected volumes
5. **Expected Operations** — Checklist of what's required
6. **API Contract (V2)** section — Table of all endpoints, link to `api-contract.yaml`
7. **Prompt to Give Agent** — One prompt per language (Python, .NET, Java, Node.js, Go)

**The prompts are CRITICAL.** Each language prompt MUST end with this block (adapted for your scenario):

```
---
**CRITICAL: API Contract Requirements**
Your API MUST implement these EXACT endpoints with these EXACT paths and field names.
Automated tests will validate conformance — any deviation will cause test failures.

Endpoints:
- GET  /health                              → Returns 200 when app is ready
- POST /api/patients                        → Body: {patientId, name, email} → 201 with {patientId, name, email}
- GET  /api/patients/{patientId}            → 200 with {patientId, name, email} or 404
[... all other endpoints ...]

Field naming: use camelCase.
[... any defaults or special rules ...]

**You MUST also create a file called `iteration-config.yaml`** in your iteration folder with:
```yaml
language: <language>
database: <scenario-name>
port: <port>
health: /health
build: <build command>
run: <run command>
```

The Cosmos DB connection uses environment variables:
- COSMOS_ENDPOINT (default: https://localhost:8081)
- COSMOS_KEY (default: the standard emulator key)

Do NOT hardcode connection strings. Read them from environment variables or configuration.
```

### 7. Create `iterations/.gitkeep`

Create an empty file at `testing-v2/scenarios/<scenario-name>/iterations/.gitkeep` to ensure
the directory is tracked by git.

## Validation Checklist

Before opening the PR, verify:

- [ ] `api-contract.yaml` lists every endpoint including `/health`
- [ ] Every endpoint in the contract has at least one test in `test_api_contract.py`
- [ ] All field names are camelCase throughout (contract, tests, prompts)
- [ ] `conftest.py` imports `from conftest_base import *` and has a `seeded_data` fixture
- [ ] `SCENARIO.md` has prompts for at least Python, .NET, Java, Node.js, and Go
- [ ] Every prompt ends with the CRITICAL API Contract Requirements block
- [ ] Every prompt includes the `iteration-config.yaml` requirement
- [ ] The `iterations/.gitkeep` file exists
- [ ] Status codes match: POST create → 201, GET → 200, not found → 404
