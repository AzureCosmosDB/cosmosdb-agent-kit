# Code Review Checklist — cosmosdb-agent-kit

This is the full review checklist. The slim `.github/instructions/code-review.instructions.md`
points here. Expand this file freely — it has no character limit.

---

## Severity Tiers

| Tier | Meaning |
|------|---------|
| 🔴 Blocking | Must fix before merge. Broken build, invalid rule format, missing build step, incorrect technical content. |
| 🟡 Recommendation | Should fix. Unclear guidance, missing examples, poor naming, incomplete coverage. |
| 🟢 Suggestion | Nice to have. Style improvements, additional references, minor wording tweaks. |

---

## 1. Rule Files (`skills/*/rules/*.md`)

### Format (enforced by `npm run validate`)

| Field | Required | Constraint |
|-------|----------|------------|
| `title` | 🔴 Yes | String, clear and actionable |
| `impact` | 🔴 Yes | One of: CRITICAL, HIGH, MEDIUM-HIGH, MEDIUM, LOW-MEDIUM, LOW |
| `impactDescription` | 🔴 Yes | String describing quantitative impact (e.g., "10-50x improvement") |
| `tags` | 🔴 Yes | Comma-separated string or YAML list |

### Body Content

- 🔴 Must contain a `**Incorrect` section with at least one fenced code block
- 🔴 Must contain a `**Correct` section with at least one fenced code block
- 🟡 Should include a `Reference:` link to official Microsoft documentation

### Naming

- 🔴 Filename: `{prefix}-{description}.md`
- 🔴 Valid prefixes: `model-`, `partition-`, `query-`, `sdk-`, `index-`, `throughput-`, `global-`, `monitoring-`, `pattern-`, `tooling-`, `vector-`, `fts-`, `security-`
- 🟡 Description should be 2-4 hyphenated words max

### Content Quality

- 🟡 Must be generic — applicable to any Cosmos DB app, not tied to a specific scenario
- � One rule per PR for new rules (flag PRs bundling unrelated rules)

### Rule Provenance & Hallucination Detection

Rules in this repo are often created by the automated evaluation loop: an LLM reviews CI test failures and proposes new rules. This creates a high risk of confabulated "best practices" that sound plausible but aren't grounded in reality. Apply extra scrutiny:

- 🔴 **Unverifiable technical claims**: Rule states specific RU costs (e.g., "this saves 40 RUs"), internal limits, throttling thresholds, or SDK implementation details without citing official documentation. If you cannot find the claim at learn.microsoft.com/azure/cosmos-db/, flag it.
- 🔴 **Misattributed root cause**: Rule attributes a test failure to a Cosmos DB behavior when the actual cause was likely a code generation bug, framework misconfiguration, test harness issue, or language-specific quirk. Ask: "Would a human engineer who debugged this end-to-end reach the same conclusion?"
- 🔴 **Invented APIs**: Rule references SDK methods, parameters, configuration options, or error codes that don't exist in the official SDK docs. Check against the actual Azure SDK for [.NET](https://learn.microsoft.com/dotnet/api/microsoft.azure.cosmos), [Java](https://learn.microsoft.com/java/api/com.azure.cosmos), [Python](https://learn.microsoft.com/python/api/azure-cosmos/azure.cosmos), [Node.js](https://learn.microsoft.com/javascript/api/@azure/cosmos).
- 🔴 **Over-generalization from single failure**: Rule presents a workaround for one specific test scenario as a universal best practice. The rule should apply broadly — if it only makes sense for the exact code that triggered it, it's not a valid rule.
- 🟡 **Missing documentation reference**: Rule has no `Reference:` link. High hallucination risk — rules derived from real Cosmos DB behavior almost always have a doc page to cite.
- 🟡 **Synthetic-looking examples**: The Incorrect/Correct code examples look fabricated (nonsensical variable names, unrealistic usage patterns, code that wouldn't compile) rather than drawn from real SDK documentation or samples.

**Heuristic**: If a rule was created in the same PR as test iteration code (visible in IMPROVEMENTS-LOG.md), treat its technical claims with higher skepticism — it was generated from failure analysis, not from engineering experience or documentation review.

### Duplication, Overlap & Conflicts (compare against ALL existing rules)

A new rule must not restate — or contradict — guidance that an existing rule already
covers. Duplicates bloat the skill and dilute the index; conflicts give agents
contradictory advice. Do NOT rely on memory or on the PR diff alone. Actively compare the
new rule against the existing rule set:

1. **Enumerate existing rules.** Read the rule filenames under `skills/<skill>/rules/` and
   the category index in `skills/<skill>/SKILL.md`. Check every rule sharing the new
   rule's prefix (e.g. a new `sdk-` rule vs all existing `sdk-*` rules), and scan the other
   prefixes too — overlapping guidance often lands under a different category.
2. **Compare guidance, not just titles.** Does the new rule's core recommendation,
   Incorrect/Correct pattern, or API usage already appear in — or contradict — an existing rule?
3. **Classify and flag:**
   - 🔴 **Duplicate**: the core guidance already exists elsewhere. Block; ask the author to
     extend/refine the existing rule instead of adding a new one.
   - 🔴 **Conflict**: the new rule contradicts an existing rule. Block until reconciled.
   - 🟡 **Partial overlap**: shares significant scope with an existing rule. Recommend
     consolidating, cross-referencing, or narrowing scope.
   - 🟢 **Distinct**: no meaningful overlap.
4. **Name the rules you compared against.** A review that says "no duplicates" without
   listing the specific existing rule files it checked is not sufficient.

---

## 2. Build Artifacts & Versioning

### AGENTS.md (generated on demand)

- `AGENTS.md` is no longer committed; it is generated on demand by `npm run build` (used by release CI and benchmarking)
- Do NOT flag a rules change for a missing `AGENTS.md` update, and do NOT commit a regenerated `AGENTS.md`

### Version Bumping

- 🟡 When rules are added or significantly changed, version should be bumped
- `npm run version <semver>` (runs `scripts/version.js`) bumps ALL manifests atomically:
  - `package.json`
  - `plugin.json`
  - `gemini-extension.json`
  - `.claude-plugin/plugin.json`
  - `.codex-plugin/plugin.json`
  - `.cursor-plugin/plugin.json`
  - `apm.yml`
  - `skills/*/metadata.json`
- 🟡 Partial version bumps (editing one manifest by hand) create inconsistency — flag them

---

## 3. Eval Tasks (`evals/**/*.yaml`)

| Field | Required | Type |
|-------|----------|------|
| `id` | 🔴 Yes | String (unique identifier) |
| `name` | 🔴 Yes | String (short descriptive name) |
| `description` | 🔴 Yes | String (what this test validates) |
| `tags` | 🔴 Yes | List (should match rule category: sdk, model, partition, query, security, fts, vector, etc.) |
| `inputs.prompt` | 🔴 Yes | String (realistic user query triggering the rule's guidance) |
| `expected.outcomes` | 🔴 Yes | List (at minimum `- type: task_completed`) |

- 🟡 The prompt should be a realistic developer question, not synthetic or overly specific
- 🟡 Tags should align with the rule categories in `_sections.md`

---

## 4. Test Scenarios (`testing-v2/scenarios/`)

### api-contract.yaml

- 🔴 All JSON field names must use camelCase (Cosmos DB convention)
- 🔴 Must include a `health:` section (GET /health → 200)
- 🔴 Every endpoint needs: method, path, description, response.status
- 🟡 Request bodies should specify `required` and `properties` with types

### tests/conftest.py

- 🔴 Test data must be hardcoded and deterministic
- 🔴 No `uuid.uuid4()`, `random`, `faker`, or any non-deterministic generation
- 🟡 IDs should be descriptive: `"player-001"`, `"order-alpha"`
- 🟡 Include 3-5 test items minimum

### iteration-config.yaml

- 🔴 Must specify: language, database, port, health
- 🟡 Build/run commands must match the declared language

### Reference implementation

- `gaming-leaderboard/` is the canonical reference for all file formats

---

## 5. Scripts (`scripts/`)

### compile.js

- 🔴 Changes must not break existing rule files
- 🔴 Must preserve the AGENTS.md output structure (TOC with numbered sections, full rule content below)
- 🟡 Should handle all valid `_sections.md` configurations

### validate.js

- 🔴 Must enforce: title, impact (enum), impactDescription, tags, **Incorrect/**Correct sections, code blocks
- 🔴 Must skip files starting with `_` (template, sections)
- 🟡 Error messages should be clear and actionable

### version.js

- 🔴 Must update all manifests listed in the script atomically
- 🔴 Must validate semver format input

---

## 6. Workflows (`.github/workflows/`)

- 🔴 No secrets or tokens hardcoded — use `${{ secrets.* }}` or `${{ github.token }}`
- 🔴 No `--no-verify` or similar safety bypasses
- 🟡 `test-iteration.yaml` must preserve the contract: detect iteration → start emulator → build app → run pytest → post PR comment
- 🟡 `auto-trigger-tests.yaml` must check for `iteration-config.yaml` existence before triggering
- 🟡 `release.yml` must run validate + build before packaging

---

## 7. General

- 🔴 No secrets, API keys, or real connection strings anywhere (even in examples)
- 🟡 API field names in all code examples must use camelCase
- 🟡 Cosmos DB SDK code should follow singleton client pattern
- 🟢 Commit messages should be descriptive

---

## Out of Scope

Do not flag: formatting preferences, line length, trailing whitespace, comment style,
or markdown lint issues that don't affect agent consumption or build.
