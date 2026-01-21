# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Repository Overview

A collection of skills for AI coding agents working with Azure Cosmos DB. Skills are packaged instructions and scripts that extend agent capabilities.

## Creating a New Skill

### Directory Structure

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

### Naming Conventions

- **Skill directory**: `kebab-case` (e.g., `cosmosdb-best-practices`)
- **SKILL.md**: Always uppercase, always this exact filename
- **AGENTS.md**: Always uppercase, always this exact filename
- **Rule files**: `prefix-description.md` (e.g., `model-embed-related.md`)

### SKILL.md Format

```markdown
---
name: {skill-name}
description: {One sentence describing when to use this skill. Include trigger phrases.}
license: MIT
metadata:
  author: cosmosdb-agent-kit
  version: "1.0.0"
---

# {Skill Title}

{Brief description of what the skill does.}

## When to Apply

{List of scenarios when this skill should be used}

## Rule Categories by Priority

{Table showing categories and their impact levels}

## Quick Reference

{Organized list of all rules by category}
```

### Best Practices for Context Efficiency

Skills are loaded on-demand — only the skill name and description are loaded at startup. The full `SKILL.md` loads into context only when the agent decides the skill is relevant. To minimize context usage:

- **Keep SKILL.md under 500 lines** — put detailed reference material in AGENTS.md
- **Write specific descriptions** — helps the agent know exactly when to activate the skill
- **Use progressive disclosure** — reference supporting files that get read only when needed

## Output

The build process compiles individual rule files into `AGENTS.md`:

```bash
npm run build
# or
node scripts/compile.js
```

## Troubleshooting

### Build Issues

- Ensure all rule files have valid frontmatter (title, impact, tags)
- Check that rule files use the correct prefix for their section
- Verify metadata.json exists and has valid JSON

### Creating the Zip Package

After creating or updating a skill:

```bash
cd skills
zip -r cosmosdb-best-practices.zip cosmosdb-best-practices/
```

### End-User Installation

Document these installation methods for users:

**Claude Code:**
```bash
cp -r skills/cosmosdb-best-practices ~/.claude/skills/
```

**GitHub Copilot / VS Code:**
```bash
cp -r skills/cosmosdb-best-practices ~/.copilot/skills/
```

**Using add-skill:**
```bash
npx add-skill AzureCosmosDB/cosmosdb-agent-kit
```
