---
applyTo: "**"
---

When performing a code review, apply these checks for the cosmosdb-agent-kit repository.

**The full checklist, field requirements, and per-section details live in
[`.github/skills/code-review/checklist.md`](../skills/code-review/checklist.md)
— read that file for the complete rules. This file summarizes the key gates.**

## Severity Tiers

- 🔴 Blocking: Must fix before merge.
- 🟡 Recommendation: Should fix.
- 🟢 Suggestion: Nice to have.

## Key Gates (🔴 Blocking)

**Rule files** (`skills/*/rules/*.md`):
- Frontmatter: `title`, `impact` (CRITICAL|HIGH|MEDIUM-HIGH|MEDIUM|LOW-MEDIUM|LOW), `impactDescription`, `tags`
- Body: `**Incorrect` + `**Correct` sections with fenced code blocks
- Filename: `{prefix}-{description}.md` (model-, partition-, query-, sdk-, index-, throughput-, global-, monitoring-, pattern-, tooling-, vector-)

**Build**:
- `AGENTS.md` is generated on demand (`npm run build`) and is not committed; do not require it in rule PRs

**Eval tasks** (`evals/**/*.yaml`):
- Required fields: `id`, `name`, `description`, `tags`, `inputs.prompt`, `expected.outcomes`

**Test scenarios** (`testing-v2/scenarios/`):
- `api-contract.yaml`: camelCase fields, `health:` section required
- `tests/conftest.py`: deterministic data only — no uuid4(), random, faker

**Scripts**: Changes to compile.js/validate.js must not break existing rules.

**Workflows**: No hardcoded secrets. Use `${{ secrets.* }}` or `${{ github.token }}`.

**General**: No secrets, API keys, or connection strings anywhere.

## Rule Provenance (🔴 Blocking)

Rules in this repo are created by the automated evaluation loop (LLM reviews test failures and proposes rules). Flag rules that show signs of LLM confabulation rather than verified Cosmos DB knowledge:

- 🔴 Claims specific RU costs, internal limits, or SDK implementation details without a verifiable documentation link
- 🔴 Attributes a test failure to a Cosmos DB "best practice" that may actually be a framework bug, test misconfiguration, or code generation error
- 🔴 Invents SDK method signatures, parameters, or behaviors that don't exist in official SDK docs
- 🔴 Presents a scenario-specific workaround as a universal rule (e.g., "always do X" when X only applies to the exact test that failed)
- 🟡 Rule has no Reference link to official Microsoft documentation — high hallucination risk
- 🟡 Rule's Incorrect/Correct examples look synthetic rather than drawn from real SDK usage patterns

## Duplication — compare against ALL existing rules (🔴 Blocking for true duplicates)

New rules must not restate or contradict guidance an existing rule already covers. Do not
rely on the PR diff or memory — enumerate the existing rules and compare guidance, not titles:

- Read the rule files under `skills/<skill>/rules/` and the index in `skills/<skill>/SKILL.md`.
  Check all rules sharing the new rule's prefix, and scan the other prefixes for overlapping guidance.
- 🔴 Block if the core recommendation already exists in another rule — ask the author to extend
  the existing rule instead of adding a duplicate.
- 🔴 Block if the new rule contradicts an existing rule, until reconciled.
- 🟡 Recommend consolidation or cross-referencing for partial overlap.
- Always name the specific existing rule files you compared against; "no duplicates" without a
  list is not an acceptable review.

## Recommendations (🟡)

- Rule content must be generic (any Cosmos DB app, not scenario-specific)
- Version bumps via `npm run version` (bumps all manifests atomically)
- API field names in examples: camelCase
- One rule per PR for new rules

## Out of Scope

Formatting, line length, trailing whitespace, comment style, markdown lint.
