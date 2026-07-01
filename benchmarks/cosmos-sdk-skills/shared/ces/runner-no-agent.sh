#!/bin/bash
# runner-no-agent.sh — Same as runner.sh but WITHOUT the cosmosdb-best-practices
# agent loaded. This provides a baseline to compare against the agent-assisted run.

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

mkdir -p /logs/verifier

# -----------------------------------------------------------------------------
# Read problem statement from /drop/metadata.json + the full /instruction.md.
# -----------------------------------------------------------------------------
PROBLEM_STATEMENT=$(jq -r '.problem_statement' /drop/metadata.json)

if [ -z "$PROBLEM_STATEMENT" ] || [ "$PROBLEM_STATEMENT" = "null" ]; then
  echo "[runner] ERROR: problem_statement missing from /drop/metadata.json" >&2
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

echo "[runner] Invoking copilot (NO agent — baseline run):"
echo "[runner]   model=$MODEL"
echo "[runner]   agent=NONE"
echo "[runner]   cwd=$WORKDIR"
echo "[runner]   prompt: $(echo "$FULL_PROMPT" | head -c 200)..."

set +e
copilot \
  -p "$FULL_PROMPT" \
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
