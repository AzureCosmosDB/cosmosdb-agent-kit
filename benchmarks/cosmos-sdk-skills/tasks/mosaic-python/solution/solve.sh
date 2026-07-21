#!/usr/bin/env bash
# Oracle solution for mosaic-python.
# Copies the reference implementation into the agent's workspace.
set -euo pipefail

mkdir -p /app
cp -r /reference/. /app/
chmod +x /app/build.sh /app/run.sh

echo "[solve] reference impl copied to /app:"
ls -la /app
