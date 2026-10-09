# Contributing to cosmosdb-agent-kit

Thank you for your interest in contributing! This project is a collection of skills for AI coding agents working with Azure Cosmos DB.

## Ways to Contribute

### 1. Add New Rules (Most Common)

Add new best practice rules to the existing `cosmosdb-best-practices` skill:

1. Create a new rule file in `skills/cosmosdb-best-practices/rules/`
2. Follow the naming convention: `{prefix}-{description}.md`
   - Use an existing prefix that matches the category (e.g., `query-`, `model-`, `sdk-`)
3. Use the template at `skills/cosmosdb-best-practices/rules/_template.md`
4. Include valid frontmatter with `title`, `impact`, and `tags`
5. (Optional) Run `npm run build` to preview the compiled `AGENTS.md` locally. It is generated on demand and is not committed, so you do not need to include it in your PR.
6. **Add an evaluation task** (see [Writing Tests](#writing-tests) below)

**Example rule file name:** `query-use-top-clause.md`

### 2. Improve Existing Rules

- Review and enhance rule content for clarity or accuracy
- Add missing examples or edge cases
- Update rules as Azure Cosmos DB evolves
- Fix typos or grammatical errors

### 3. Create a New Skill

The kit is designed to host multiple focused skills. Each skill is self-contained in its own directory. To create a new skill:

1. Create a new directory under `skills/` (kebab-case name)
2. Add the required files:

```
skills/
  {skill-name}/           # kebab-case directory name
    SKILL.md              # Required: skill definition (frontmatter + content)
    metadata.json         # Required: version, organization, abstract, references
    README.md             # Required: documentation for the skill
    rules/                # Required for rule-based skills
      _sections.md        # Section metadata (defines prefixes and ordering)
      _template.md        # Template for new rules in this skill
      {prefix}-{name}.md  # Individual rule files
```

3. Define sections in `rules/_sections.md` with frontmatter:

```yaml
---
sections:
  - { prefix: 'sizing-', name: 'Data Sizing', number: 1, impact: 'CRITICAL' }
  - { prefix: 'ru-', name: 'RU Calculation', number: 2, impact: 'HIGH' }
---
```

4. Build and validate:

```bash
# Build just your skill
npm run build:skill {skill-name}

# Or build all skills
npm run build

# Validate
npm run validate:skill {skill-name}
```

5. Create a matching eval directory at `evals/{skill-name}/` (see [Writing Tests](#writing-tests))

### 4. Report Issues / Suggest Improvements

- Open GitHub issues for bugs, inaccuracies, or missing best practices
- Suggest new rule categories or skill ideas
- Share feedback on rule effectiveness

### 5. Test Compatibility

- Test skills with different AI agents (Claude Code, GitHub Copilot, Gemini CLI, Cursor)
- Report compatibility issues or unexpected behavior

## Getting Started

```bash
# Clone the repo
git clone https://github.com/AzureCosmosDB/cosmosdb-agent-kit.git
cd cosmosdb-agent-kit

# Install dependencies
npm install

# Make changes to rules, then build
npm run build

# Validate your changes
npm run validate
```

## Writing Tests

[Vally](https://github.com/microsoft/vally) tests live skill activation and answer
correctness. Each rule has exactly one stimulus in its category's
[`eval.yaml`](evals/cosmosdb-best-practices/); the root spec checks that PostgreSQL
does not activate the skill. Category files keep the suite readable and stay
within Vally's YAML alias limits.

The npm commands discover specs explicitly under `evals/`; the live runner
([`scripts/eval.mjs`](scripts/eval.mjs)) passes each file to Vally. No root Vally
configuration or legacy task/fixture files are needed.

### Adding a test for a rule

Add a stimulus to `evals/cosmosdb-best-practices/<prefix>/eval.yaml`. Match its
`name` and `tags.rule` to the rule filename without `.md`, and reuse that file's
`rule-graders` anchor:

```yaml
  # Project needed fields.
  - name: query-use-projections
    tags: { category: query, rule: query-use-projections }
    prompt: |
      A Cosmos DB list page needs only id and name but SELECT * returns large
      attachments too. Show the better query.
    rubric:
      - Select c.id and c.name only, reducing payload/client work without returning unused attachments.
    graders: *rule-graders
```

Keep the comment to a few words (at most six) and new prompts short (at most 65
words). Use specific rubric criteria that distinguish correct guidance from the
anti-pattern. Test the rule's current body, not just its filename or index
summary. Do not supply the expected answer in the prompt.

The 13 original Vally scenarios are migrated into these category specs with
their original prompts (apart from whitespace wrapping). Their `tags.legacy`
values preserve the old task IDs; stimulus names match the corresponding rules.
The original vector-index decision matrix is the one longer prompt retained to
preserve its small-dataset fallback and recall-tuning coverage (up to 180 words).
The obsolete task files and mock configuration are removed, not the scenarios.

All four checks must pass: execution completed, correct skill activation,
nonempty output, and the LLM judge's binary correctness verdict. The overall
threshold is 1, so activation alone cannot compensate for incorrect advice.
Offline tests verify exact rule coverage and exercise both passing and failing
grader outcomes with a fake judge; they do not establish live response quality.
They also require every rule to be linked from the skill's quick reference.
Ask explicitly for any scenario-specific caveats the rubric requires; a request
for a brief recommendation should not secretly require an exhaustive checklist.
Check SDK documentation/source before treating a version number or exact wording
as the only correct answer.

### Running tests locally

Use Node.js 22.22.2 or newer supported by the pinned dependencies.

```bash
npm ci
npm run build
npm run eval:lint
npm run eval:test

# Live evaluations require Copilot model access.
npm run eval

# Limit live execution to one rule or category.
npm run eval -- --tag rule=query-point-reads
npm run eval -- --tag category=query

# Run a migrated scenario by its original task ID.
npm run eval -- --tag legacy=indexing-composite-005

# Check non-activation.
npm run eval -- --tag category=activation
```

For live runs, authenticate the Copilot CLI or set `COPILOT_GITHUB_TOKEN` and
`GITHUB_TOKEN` to a Copilot-enabled token in your shell. Never commit tokens.
The pinned defaults use `gpt-5.6-luna` for execution and `gpt-5.6-terra` for
judging; override them with `--model` and `--judge-model` if needed.
Runs use five workers, one trial per stimulus, no executor retries, and a
three-minute per-trial timeout. LLM grading adds time and model usage.
Reports and trajectories are written under the ignored `results/` directory.

### CI behavior

The [Vally workflow](.github/workflows/evals.yml) runs on manual dispatch,
relevant main-branch pushes, and every pull request. Unrelated PRs receive a
successful skip check. Relevant PRs run build, spec lint, and offline grader
tests; fork PRs never receive organization-billed model access.

Same-repository PRs, main-branch pushes, and manual runs also execute live tests
using `github.token` with `contents: read` and `copilot-requests: write`. This
requires organization/repository Copilot access to the configured models.
The live runner has no PR-comment write permission.

Markdown reports appear in the Actions summary, and reports/trajectories are
uploaded as artifacts for 14 days, including after failures. The aggregate
`Vally evaluation gate` fails on offline errors or failed live evaluations;
whether it blocks merging depends on branch protection settings. No PR comment
is posted.

## Rule File Format

Each rule file should follow this structure:

```markdown
---
title: Short descriptive title
impact: Critical | High | Medium | Low
tags:
  - relevant-tag
  - another-tag
---

## Description

Explain what this rule addresses and why it matters.

## Recommendation

Clear, actionable guidance.

## Example

Show code or configuration examples when applicable.

## References

- Link to official documentation
```

## Pull Request Guidelines

1. **One rule per PR** for new rules (makes review easier)
2. **Run validation** before submitting: `npm run validate`
3. **Do not commit `AGENTS.md`** — it is generated on demand (release CI and benchmarking)
4. **Write clear commit messages** describing the change
5. **Link related issues** in the PR description
6. **Add or update the matching evaluation** in `evals/` for your rule

## PR Merge Requirements

Your PR must pass these checks before merge:

- [ ] `npm run validate` passes
- [ ] One approving review from a code owner

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the content, not the contributor

## Questions?

Open an issue with the `question` label if you need help getting started.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
