#!/bin/bash
# runner-with-skills.sh — MSBench runner that vendors the public cosmosdb-sdk
# skill into the container, exposes its AGENTS.md to Copilot as on-disk context,
# and invokes Copilot with a custom agent whose instructions include that file.

set -euo pipefail

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
export COPILOT_CUSTOM_AGENT=cosmosdb-sdk

# -----------------------------------------------------------------------------
# Vendor the public cosmosdb-sdk skill into ~/.copilot/skills/ and create a
# matching custom agent in ~/.copilot/agents/ so the AGENTS.md content becomes
# part of the agent instructions for this run.
# -----------------------------------------------------------------------------
SKILL_NAME="cosmosdb-sdk"
SKILL_REF="${COSMOS_SKILL_REF:-0355b0ff817bae9eb7fc20eda894ad64eb2cffe2}"
SKILL_BASE_URL="${COSMOS_SKILL_BASE_URL:-https://raw.githubusercontent.com/AzureCosmosDB/cosmosdb-agent-kit/${SKILL_REF}/skills/${SKILL_NAME}}"
SKILL_DIR="$HOME/.copilot/skills/$SKILL_NAME"
AGENT_FILE="$HOME/.copilot/agents/${SKILL_NAME}.md"

mkdir -p "$SKILL_DIR" "$HOME/.copilot/agents"

fetch_required() {
  local url="$1"
  local dest="$2"
  echo "[runner] Fetching $url"
  curl -fsSL "$url" -o "$dest"
}

fetch_optional() {
  local url="$1"
  local dest="$2"
  curl -fsSL "$url" -o "$dest" 2>/dev/null || true
}

fetch_required "$SKILL_BASE_URL/AGENTS.md" "$SKILL_DIR/AGENTS.md"
fetch_optional "$SKILL_BASE_URL/SKILL.md" "$SKILL_DIR/SKILL.md"
fetch_optional "$SKILL_BASE_URL/README.md" "$SKILL_DIR/README.md"
fetch_optional "$SKILL_BASE_URL/metadata.json" "$SKILL_DIR/metadata.json"

cat > "$AGENT_FILE" <<EOF
---
name: ${SKILL_NAME}
description: Azure Cosmos DB SDK specialist. Use when building, reviewing, or refactoring code that uses Azure Cosmos DB SDKs across .NET, Java, Python, Go, Node.js, or Spring Boot.
tools: ["*"]
---

# Cosmos DB SDK Agent

This run vendors the public cosmosdb-sdk skill from:
https://github.com/AzureCosmosDB/cosmosdb-agent-kit/tree/main/skills/${SKILL_NAME}

into:

- ${SKILL_DIR}/AGENTS.md
- ${SKILL_DIR}/SKILL.md (if available)
- ${SKILL_DIR}/metadata.json (if available)

Treat ${SKILL_DIR}/AGENTS.md as the authoritative instruction set for this run.
Follow its SDK guidance when maintaining, generating, or refactoring Azure Cosmos DB code.

Important constraints:
- Apply language-specific SDK guidance when the skill provides it.
- Reuse Cosmos client instances, prefer async APIs, configure retries/diagnostics,
  and use emulator-safe settings when applicable.
- Do not invent SDK-specific guidance that is absent from the skill.
- If relevant language-specific guidance is missing, say so explicitly and only
  apply the general guidance that the skill actually contains.

---

EOF
cat "$SKILL_DIR/AGENTS.md" >> "$AGENT_FILE"

echo "[runner] Installed skill at $SKILL_DIR"
echo "[runner] Installed agent at $AGENT_FILE"
echo "[runner] Skill ref: $SKILL_REF"

mkdir -p /logs/verifier

# -----------------------------------------------------------------------------
# Read problem statement from metadata + the full /instruction.md.
# -----------------------------------------------------------------------------
METADATA_FILE="${METADATA_PATH:-/drop/metadata.json}"
PROBLEM_STATEMENT=$(jq -r '.problem_statement' "$METADATA_FILE")

if [ -z "$PROBLEM_STATEMENT" ] || [ "$PROBLEM_STATEMENT" = "null" ]; then
  echo "[runner] ERROR: problem_statement missing from $METADATA_FILE" >&2
  exit 4
fi

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
echo "[runner]   agent=$SKILL_NAME"
echo "[runner]   cwd=$WORKDIR"
echo "[runner]   prompt: $(echo "$FULL_PROMPT" | head -c 200)..."

set +e
copilot \
  -p "$FULL_PROMPT" \
  --agent "$SKILL_NAME" \
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
