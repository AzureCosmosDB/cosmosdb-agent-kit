#!/usr/bin/env bash
set -euo pipefail
cd /app
exec java -jar target/mosaic-users.jar
