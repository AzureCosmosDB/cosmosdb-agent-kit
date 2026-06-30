#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -o /app/mosaic-users ./...
