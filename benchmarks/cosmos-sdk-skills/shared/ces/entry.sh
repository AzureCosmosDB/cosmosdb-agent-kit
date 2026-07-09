#!/bin/bash
# MSBench / CES master orchestrator. Sourced/run by the CES backend after
# /ces_activate.sh. Derived verbatim from the cosmosdb-rules.* images, with
# one change: INSTANCE_ID is read from /drop/metadata.json so a single
# entry.sh can serve every task in the benchmark.
set -euo pipefail

# Standard MSBench directory paths
export AGENT_DIR="/agent"           # Where agent code lives (mounted at runtime)
export TESTBED_DIR="/testbed"       # The workspace/repository the agent works on
export OUTPUT_DIR="/output"         # Where to write results (eval.json, etc.)

# Metadata paths
export METADATA_PATH="/drop/metadata.json"
export EVAL_SCRIPT_PATH="/tests/test.sh"

# Instance identifier — prefer the instanceId env var (set by the MSBench local
# Docker backend), fall back to /drop/metadata.json (CES backend contract), and
# default to "unknown" so a missing/renamed key never aborts the run under set -e.
export INSTANCE_ID="${instanceId:-}"
if [ -z "$INSTANCE_ID" ]; then
    INSTANCE_ID="$(python3 -c "import json; print(json.load(open('${METADATA_PATH}')).get('instance_id','unknown'))" 2>/dev/null || echo unknown)"
fi
export INSTANCE_ID

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Redirect all output to entry.log (000 prefix for chronological ordering)
exec &> "${OUTPUT_DIR}/000_entry.log"

# Encrypt secret files before agent runs
ENCRYPTED_FILE="$(mktemp)"
export ENCRYPTED_FILE

# Check if agent provides an encryption key (used by oracle verification)
if [ -f "${AGENT_DIR}/msbench_secret_files_key" ]; then
    echo "Using encryption key from ${AGENT_DIR}/msbench_secret_files_key"
    key=$(cat "${AGENT_DIR}/msbench_secret_files_key")
else
    echo "Generating random encryption key"
    key=$(openssl rand -hex 32)
fi

bash /opt/safe_save.sh "${key}" /secret_files.txt /nonsecret_metadata_keys.txt "${ENCRYPTED_FILE}" &> "${OUTPUT_DIR}/010_encrypt.log"
echo "Save exit code: $?"

# Run the agent
bash "${AGENT_DIR}/runner.sh" &> "${OUTPUT_DIR}/020_runner.log"

# Restore (decrypt) secret files after agent completes
if [ -f "${ENCRYPTED_FILE}" ]; then
    bash /restore.sh "${key}" "${ENCRYPTED_FILE}" &> "${OUTPUT_DIR}/030_decrypt.log"
    echo "Restore exit code: $?"
else
    echo "Encrypted file already consumed (oracle runner decrypted)" > "${OUTPUT_DIR}/030_decrypt.log"
    echo "Skipping restore - already decrypted"
fi

# Copy metadata.json to output folder for post-analysis
if [ -f "$METADATA_PATH" ]; then
    cp "$METADATA_PATH" "$OUTPUT_DIR/task_metadata.json"
    echo "Copied $METADATA_PATH to output folder as task_metadata.json"
else
    echo "WARNING: $METADATA_PATH not found, skipping copy"
fi

# Run the Harbor tests directly (use set +e to not exit on test failure)
echo "Running evaluation..."
set +e
bash "$EVAL_SCRIPT_PATH" &> "$OUTPUT_DIR/040_eval.log"
EVAL_EXIT_CODE=$?
set -e
echo "Eval exit code: $EVAL_EXIT_CODE" >> "$OUTPUT_DIR/040_eval.log"

# Copy verifier logs to output folder
if [ -d "/logs/verifier" ] && [ "$(ls -A /logs/verifier 2>/dev/null)" ]; then
    cp -r /logs/verifier/* "$OUTPUT_DIR/" 2>/dev/null || true
    echo "Copied verifier logs to output folder"
fi

# Parse Harbor reward output to MSBench eval.json format
echo "Parsing results..."
(. /opt/activate_python.sh && python3 /parse.py) &> "$OUTPUT_DIR/050_parse.log"
PARSE_EXIT_CODE=$?
echo "Parse exit code: $PARSE_EXIT_CODE" >> "$OUTPUT_DIR/050_parse.log"

# Mark what file contains the eval output
echo "eval.json" > "$OUTPUT_DIR/eval_output.txt"

echo "Evaluation complete."
