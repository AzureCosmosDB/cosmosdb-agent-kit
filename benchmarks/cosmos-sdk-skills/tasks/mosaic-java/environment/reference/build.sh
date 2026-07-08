#!/usr/bin/env bash
set -euo pipefail
cd /app
mvn -B -q package -DskipTests
