#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app
cp -r /reference/. /app/
chmod +x /app/build.sh /app/run.sh
echo "[solve] mosaic-nodejs reference impl copied to /app"
