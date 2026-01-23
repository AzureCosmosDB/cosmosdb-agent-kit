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
5. Run `npm run build` to compile rules into AGENTS.md

**Example rule file name:** `query-use-top-clause.md`

### 2. Improve Existing Rules

- Review and enhance rule content for clarity or accuracy
- Add missing examples or edge cases
- Update rules as Azure Cosmos DB evolves
- Fix typos or grammatical errors

### 3. Create a New Skill

For advanced contributors, create an entirely new skill following the structure in [AGENTS.md](AGENTS.md):

```
skills/
  {skill-name}/           # kebab-case directory name
    SKILL.md              # Required: skill definition
    AGENTS.md             # Required: compiled rules (generated)
    metadata.json         # Required: version and metadata
    README.md             # Required: documentation
    rules/                # Required for rule-based skills
      _sections.md        # Section metadata
      _template.md        # Template for new rules
      {prefix}-{name}.md  # Individual rule files
```

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
3. **Run build** to regenerate AGENTS.md: `npm run build`
4. **Write clear commit messages** describing the change
5. **Link related issues** in the PR description

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the content, not the contributor

## Questions?

Open an issue with the `question` label if you need help getting started.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
