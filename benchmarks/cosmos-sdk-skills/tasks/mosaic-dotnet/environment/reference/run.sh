#!/usr/bin/env bash
set -euo pipefail
cd /app
exec dotnet /app/out/Mosaic.Users.dll
