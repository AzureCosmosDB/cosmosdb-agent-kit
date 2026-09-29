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

## Writing Tests (Optional)

The repo includes a [Vally](https://github.com/microsoft/vally) eval framework under `evals/`. Evals are split by area (`*.eval.yaml`) and run with suites from `.vally.yaml`.

### Adding an eval stimulus for a new rule

Update the relevant area file in `evals/cosmosdb-best-practices/`:
- `modeling.eval.yaml`
- `query.eval.yaml`
- `sdk.eval.yaml`
- `throughput.eval.yaml`
- `security.eval.yaml`
- `vector.eval.yaml`
- `guardrails.eval.yaml`

Add a new `stimuli` entry using this shape:

```yaml
- name: your-rule-name-###
  prompt: "A realistic user prompt that should trigger your rule's guidance"
  tags:
    category: [throughput, serverless]
  rubric:
    - Clear criterion 1 for what a correct response must contain.
    - Clear criterion 2 for what a correct response must contain.
  graders:
    - type: skill-invocation
      config:
        required: [cosmosdb-best-practices]
    - type: prompt
```

### Running tests locally

```bash
# Install Vally by following the instructions at https://github.com/microsoft/vally

# Validate split eval files (PowerShell)
$files = @('modeling.eval.yaml','query.eval.yaml','sdk.eval.yaml','throughput.eval.yaml','security.eval.yaml','vector.eval.yaml','guardrails.eval.yaml'); foreach ($f in $files) { vally lint -e (Join-Path './evals/cosmosdb-best-practices' $f) }

# Run all split evals
vally eval --suite cosmosdb-all

# Run only serverless checks
vally eval --suite cosmosdb-serverless --workers 1

# Lint skill readiness
vally lint ./skills
```

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
6. **(Optional)** Add an eval task in `evals/` for your rule

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
