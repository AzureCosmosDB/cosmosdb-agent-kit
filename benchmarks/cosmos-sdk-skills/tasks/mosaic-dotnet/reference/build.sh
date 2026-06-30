#!/usr/bin/env bash
set -euo pipefail
cd /app
dotnet restore
dotnet build -c Release -o /app/out
