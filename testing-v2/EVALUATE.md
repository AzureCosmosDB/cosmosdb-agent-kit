# Recipe: Evaluate Test Results

This document tells a coding agent (or human) how to evaluate test results from a
test iteration and create or update rules in the Cosmos DB Agent Kit skills.

CI posts test results as a PR comment after every iteration. This recipe turns those
results into actionable skill improvements.

## Inputs

You need:
1. **Test results** — The PR comment posted by CI (or `test-report.json` artifact)
2. **The scenario** — Which scenario was tested (read from the PR title or test report)
3. **The API contract** — `testing-v2/scenarios/<scenario>/api-contract.yaml`
4. **Existing rules** — `skills/cosmosdb-best-practices/rules/*.md`
5. **The generated code** — in `testing-v2/scenarios/<scenario>/iterations/<iteration>/`

## Step-by-Step

### Step 1: Read the test results

Look at the PR comment with the test report, or read the `test-report.json` artifact.
For each failure, note:
- The test name (e.g., `TestCreatePlayer::test_new_player_has_zero_stats`)
- The failure message
- The test category (API contract vs data integrity)

### Step 2: Classify each failure

For every failing test, determine the root cause:

| Category | Description | Action |
|----------|-------------|--------|
| **Contract violation** | Code doesn't match the API contract (wrong path, missing field, wrong status code) | Fix the generated code — this is a code bug, not a skill gap |
| **Cosmos DB anti-pattern** | Code works but uses a bad practice (e.g., `/id` as partition key, cross-partition query, no ETag) | Create a **new rule** in `skills/cosmosdb-best-practices/rules/` |
| **Unclear existing rule** | A rule exists but the agent didn't follow it (ambiguous wording, missing example) | Update the **existing rule** to be clearer |
| **SDK/framework quirk** | Language-specific SDK issue (wrong method signature, missing import, SSL config) | Create an `sdk-*` rule with language-specific guidance |
| **Test too strict** | The test assertion is unreasonable or overly specific | Fix the test (rare — flag for human review) |

### Step 3: Create new rules (if needed)

For each failure classified as "Cosmos DB anti-pattern" or "SDK/framework quirk":

1. **Choose the correct prefix** based on category:
   - `model-` — Data modeling (embedding, referencing, document size)
   - `partition-` — Partition key design
   - `query-` — Query optimization
   - `sdk-` — SDK configuration and usage
   - `index-` — Indexing strategy
   - `throughput-` — RU budgeting and scaling
   - `global-` — Multi-region and replication
   - `monitoring-` — Observability and diagnostics
   - `pattern-` — Design patterns (change feed, materialized views, etc.)

2. **Create the rule file** at `skills/cosmosdb-best-practices/rules/<prefix>-<description>.md`

3. **Use this exact frontmatter format:**

```markdown
---
title: <Clear, actionable title>
impact: HIGH | MEDIUM | LOW
tags:
  - <relevant tags>
---

## Rule

<One paragraph stating the rule clearly>

## Why

<Why this matters — performance, cost, correctness>

## How

<Concrete implementation guidance>

### Example (Good)

```<language>
// Correct approach
```

### Example (Bad)

```<language>
// Anti-pattern to avoid
```

## References

- [Link to relevant Azure docs]
```

4. **Run the build** to regenerate AGENTS.md:
```bash
npm run build
```

### Step 4: Update existing rules (if needed)

For failures classified as "Unclear existing rule":

1. Read the existing rule file
2. Identify what's ambiguous or missing
3. Add clarifying text, better examples, or language-specific guidance
4. Run `npm run build`

### Step 5: Fix contract violations in the code (if needed)

For failures classified as "Contract violation":

1. Read the failing test to understand what's expected
2. Read the API contract to confirm the expected behavior
3. Fix the generated code to match the contract
4. Commit the fix to the PR branch

### Step 6: Update IMPROVEMENTS-LOG.md

Add an entry to `testing-v2/IMPROVEMENTS-LOG.md` with this format:

```markdown
#### <DATE>: Iteration <NNN> - <Scenario Name> (<Language> / <Framework>)

- **Scenario**: <scenario-name>
- **Iteration**: <NNN>-<language>
- **Result**: ✅ SUCCESSFUL / ⚠️ PARTIAL / ❌ FAILED — <brief summary>
- **Score**: <X>/10

**Rules Created** 🆕:
1. **<rule-filename>.md** — <brief description> (<IMPACT>)

**Rules Updated** 🔧:
1. **<rule-filename>.md** — <what changed> (<IMPACT>)

**Issues Encountered & Resolved**:
1. **<Issue title>** — <category emoji> <CATEGORY>
   - Problem: <what went wrong>
   - Impact: <what effect it had>
   - Solution: <what was done>
   - Status: ✅ Fixed / ⚠️ Noted

**Test Results**:
- ✅ <passing test> — <brief note>
- ❌ <failing test> — <brief note on why>

**Best Practices Applied**: <count> of <total> rules applied correctly
**Lessons for Next Iteration**: <what to improve>
```

### Step 7: Run the build

After creating or updating any rules:

```bash
npm run build
```

This regenerates `skills/cosmosdb-best-practices/AGENTS.md` which is the compiled file
that agents read. Always commit the regenerated AGENTS.md.

### Step 8: Commit everything to the PR

Commit all changes to the PR branch:
- New/updated rule files in `skills/cosmosdb-best-practices/rules/`
- Regenerated `skills/cosmosdb-best-practices/AGENTS.md`
- Updated `testing-v2/IMPROVEMENTS-LOG.md`
- Any code fixes in the iteration directory

## Scoring Guide

Rate the iteration 1–10:

| Score | Meaning |
|-------|---------|
| 9–10  | All tests pass, good Cosmos DB practices, clean code |
| 7–8   | Most tests pass, minor issues, reasonable practices |
| 5–6   | Many tests fail but app runs, significant practice gaps |
| 3–4   | App runs but major failures, poor practices |
| 1–2   | App doesn't build or start |

## What Signals a Good Rule

A rule is worth creating when:
- The same mistake would likely be made by other agents in other iterations
- The issue is Cosmos DB-specific (not a general coding error)
- The fix is concrete and can be expressed as clear guidance
- The existing rule set doesn't already cover it

A rule is NOT needed when:
- The failure is a one-off code bug (typo, wrong variable name)
- The issue is language-specific boilerplate (not Cosmos DB related)
- An existing rule already covers the exact issue clearly

---

## Batch Evaluation

When evaluating **batch aggregate results** (from `/aggregate` on a batch issue), the
process differs from single-iteration evaluation:

### Key Differences

1. **Focus on Consistent Failures** — The `BATCH-RESULTS.md` classifies each test as
   "always-pass", "always-fail", or "flaky". Only **always-fail** tests indicate real
   skill gaps that need new or updated rules.

2. **Ignore Flaky Tests** — Tests that pass in some iterations but fail in others are
   LLM stochasticity, not skill gaps. Do not create rules for flaky tests.

3. **No Code Fixes** — Unlike single-iteration evaluation, you're not fixing generated
   code. You're analyzing aggregate patterns to improve the skill set.

4. **Statistical Context** — Use the standard deviation and confidence level from
   BATCH-RESULTS.md to calibrate your assessment.

### Batch Evaluation Steps

1. Read the `BATCH-RESULTS.md` on the summary PR branch
2. For each **always-fail** test:
   - Read the test code to understand what it checks
   - Read the API contract for expected behavior
   - Classify using the same categories as Step 2 above
3. Create or update rules only for tests classified as "Cosmos DB anti-pattern",
   "Unclear existing rule", or "SDK/framework quirk"
4. Run `npm run build` to regenerate AGENTS.md
5. Update `testing-v2/IMPROVEMENTS-LOG.md`
6. Commit to the summary PR branch

### Control Run Batch Evaluation

For control runs (skills=no), do NOT create or update rules. Instead:
1. List which consistent failures would have been prevented by existing rules
2. Note any gaps where no existing rule covers the failure
3. Update IMPROVEMENTS-LOG.md with the analysis
4. Commit with `[skip ci]` in the message
