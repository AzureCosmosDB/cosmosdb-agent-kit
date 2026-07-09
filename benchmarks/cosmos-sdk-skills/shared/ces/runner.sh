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

# -----------------------------------------------------------------------------
# Install the cosmosdb-best-practices skill as a normally discoverable skill.
#
# The skill is baked into the image at /opt/cosmosdb-agent-kit/skills/. We copy
# it into ~/.copilot/skills/ — the personal skills directory the @github/copilot
# CLI auto-discovers at startup. At startup the agent only sees each skill's
# name + description (from SKILL.md frontmatter) and decides on its own whether
# the skill is relevant and worth reading in full.
#
# IMPORTANT: This runner deliberately gives the agent NO hint to consult the
# skill — no custom agent persona, no routing table, no mention in the prompt.
# The default agent runs the task as-is. This keeps the benchmark an honest
# measurement of the skill's organic effect: does an agent that merely has the
# skill installed (as any user would) apply the Cosmos DB best practices?
# -----------------------------------------------------------------------------
SKILL_BASE="/opt/cosmosdb-agent-kit/skills/cosmosdb-best-practices"

if [ ! -d "$SKILL_BASE" ]; then
  echo "[runner] ERROR: expected baked skill directory at $SKILL_BASE" >&2
  exit 3
fi

mkdir -p "$HOME/.copilot/skills"
rm -rf "$HOME/.copilot/skills/cosmosdb-best-practices"
cp -r "$SKILL_BASE" "$HOME/.copilot/skills/cosmosdb-best-practices"

echo "[runner] Installed discoverable skill at \$HOME/.copilot/skills/cosmosdb-best-practices"
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
echo "[runner]   agent=default (skill installed but not hinted)"
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
