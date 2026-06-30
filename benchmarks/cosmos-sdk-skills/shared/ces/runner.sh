#!/bin/bash
# runner.sh — passed to msbench-cli via --runner. Mounted at /agent/runner.sh
# by the CES runtime and invoked by /entry.sh.
#
# Bypasses MSBench's github-copilot-cli plugin agent-downloader (which needs
# Microsoft-internal RBAC + unzip on Mariner). Uses the public
# @github/copilot npm CLI baked into the image and authenticates with a
# GITHUB_TOKEN passed in via --encrypted-env.
#
# Required env (via msbench-cli `--encrypted-env`):
#   GITHUB_TOKEN — github.com PAT belonging to an account with a Copilot
#                  subscription (e.g. `gh auth token`).

set -e

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------
if [ -z "${GITHUB_TOKEN:-}" ] && [ -n "${COPILOT_GITHUB_TOKEN:-}" ]; then
  export GITHUB_TOKEN="$COPILOT_GITHUB_TOKEN"
fi

if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo "[runner] ERROR: GITHUB_TOKEN is not set. Pass it through msbench-cli with --encrypted-env GITHUB_TOKEN." >&2
  exit 2
fi

export COPILOT_AUTO_UPDATE=false
export COPILOT_CUSTOM_AGENT=cosmosdb-best-practices

# -----------------------------------------------------------------------------
# Stage the cosmosdb-best-practices custom agent into ~/.copilot/agents/.
# Skill rules are baked into the image at /opt/cosmosdb-agent-kit/skills/.
# -----------------------------------------------------------------------------
SKILL_BASE="/opt/cosmosdb-agent-kit/skills/cosmosdb-best-practices"

if [ ! -d "$SKILL_BASE" ]; then
  echo "[runner] ERROR: expected baked skill directory at $SKILL_BASE" >&2
  exit 3
fi

mkdir -p "$HOME/.copilot/agents"
cat > "$HOME/.copilot/agents/cosmosdb-best-practices.md" <<EOF
---
name: cosmosdb-best-practices
description: Azure Cosmos DB best practices agent — reviews code, generates optimized patterns, and advises on data modeling, partition keys, queries, SDK usage, indexing, throughput, global distribution, vector search, and full-text search. Use when writing, reviewing, or refactoring code that interacts with Azure Cosmos DB.
tools: ["*"]
---

# Cosmos DB Best Practices Agent

You are a Cosmos DB best practices specialist. The full rule set is at:
  $SKILL_BASE

## Routing

| User wants to... | Action |
|---|---|
| General best practices overview | Read \`$SKILL_BASE/SKILL.md\` |
| Data modeling advice | Read relevant \`$SKILL_BASE/rules/model-*.md\` files |
| Partition key design | Read relevant \`$SKILL_BASE/rules/partition-*.md\` files |
| Query optimization | Read relevant \`$SKILL_BASE/rules/query-*.md\` files |
| SDK usage patterns | Read relevant \`$SKILL_BASE/rules/sdk-*.md\` files |
| Indexing strategies | Read relevant \`$SKILL_BASE/rules/index-*.md\` files |
| Throughput and scaling | Read relevant \`$SKILL_BASE/rules/throughput-*.md\` files |
| Global distribution | Read relevant \`$SKILL_BASE/rules/global-*.md\` files |
| Monitoring and diagnostics | Read relevant \`$SKILL_BASE/rules/monitoring-*.md\` files |
| Design patterns | Read relevant \`$SKILL_BASE/rules/pattern-*.md\` files |
| Developer tooling | Read relevant \`$SKILL_BASE/rules/tooling-*.md\` files |
| Vector search | Read relevant \`$SKILL_BASE/rules/vector-*.md\` files |
| Full-text search | Read relevant \`$SKILL_BASE/rules/fts-*.md\` files |

## How to Apply Rules

1. Read \`$SKILL_BASE/SKILL.md\` to identify relevant categories
2. Scan the code / task for patterns matching rule prefixes
3. Read the specific rule files that apply
4. Apply rules in generated code; cite rule IDs in comments for non-obvious choices

## Key Constraints
- Always read the specific rule file before citing it
- Each rule file contains incorrect and correct code examples — use these
- Rules cover C#, Python, Java, JavaScript, Go, and Rust — match the user's language
- If a user's scenario doesn't match any rule, say so rather than inventing guidance
EOF

echo "[runner] Installed agent at \$HOME/.copilot/agents/cosmosdb-best-practices.md"
echo "[runner] Skill base: $SKILL_BASE"

mkdir -p /logs/verifier

# -----------------------------------------------------------------------------
# Read problem statement from /drop/metadata.json + the full /instruction.md.
# -----------------------------------------------------------------------------
PROBLEM_STATEMENT=$(jq -r '.problem_statement' /drop/metadata.json)

if [ -z "$PROBLEM_STATEMENT" ] || [ "$PROBLEM_STATEMENT" = "null" ]; then
  echo "[runner] ERROR: problem_statement missing from /drop/metadata.json" >&2
  exit 4
fi

# Compose the full prompt: the short statement from metadata plus the full
# /instruction.md (which is where the API contract + build/run conventions
# + grading criteria live for this benchmark).
FULL_PROMPT="$PROBLEM_STATEMENT"
if [ -f /instruction.md ]; then
  FULL_PROMPT="${FULL_PROMPT}

The full task description lives at /instruction.md. Read it before doing anything else:

$(cat /instruction.md)"
fi

MODEL="${COPILOT_MODEL:-claude-sonnet-4.6}"
WORKDIR="${COPILOT_WORKDIR:-/app}"
mkdir -p "$WORKDIR"

echo "[runner] Invoking copilot:"
echo "[runner]   model=$MODEL"
echo "[runner]   agent=cosmosdb-best-practices"
echo "[runner]   cwd=$WORKDIR"
echo "[runner]   prompt: $(echo "$FULL_PROMPT" | head -c 200)..."

set +e
copilot \
  -p "$FULL_PROMPT" \
  --agent cosmosdb-best-practices \
  --model "$MODEL" \
  --allow-all \
  --no-auto-update \
  --no-ask-user \
  -C "$WORKDIR" \
  --output-format json \
  --share /logs/verifier/copilot-session.md \
  > /logs/verifier/copilot-session.jsonl
COPILOT_EXIT=$?
set -e

echo "[runner] copilot exit code: $COPILOT_EXIT"
echo "[runner] JSONL transcript: /logs/verifier/copilot-session.jsonl ($(wc -c < /logs/verifier/copilot-session.jsonl 2>/dev/null || echo 0) bytes)"
exit 0
