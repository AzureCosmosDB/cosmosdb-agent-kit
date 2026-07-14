#!/usr/bin/env bash
# Shared verifier runner. Each task's tests/test.sh calls this with the
# task's SDK name as $1.
#
# Responsibilities:
#   1. Start the Cosmos emulator (idempotent).
#   2. Ensure the agent produced /app/build.sh and /app/run.sh.
#   3. Run /app/build.sh.
#   4. Run /app/run.sh in the background.
#   5. Wait for the agent's /health endpoint.
#   6. Run pytest over /verifier/check_*.py + /tests/checks.py.
#   7. Write 0 or 1 to /logs/verifier/reward.txt.
#
# Always writes reward.txt, even on early failure (default 0).

set -uo pipefail

SDK="${1:-}"
if [ -z "$SDK" ]; then
    echo "[runner] usage: runner.sh <sdk>" >&2
    exit 2
fi

export SDK
LOG_DIR="${VERIFIER_LOG_DIR:-/logs/verifier}"
APP_DIR="${APP_WORKDIR:-/app}"
APP_PORT="${APP_PORT:-9080}"
mkdir -p "$LOG_DIR"
REWARD_FILE="$LOG_DIR/reward.txt"
echo "0" > "$REWARD_FILE"  # default to failure; success path overwrites at the end

# Convenience: a labelled section marker for the log.
section() { echo; echo "============================================================"; echo "[runner] $*"; echo "============================================================"; }

# ---------------------------------------------------------------------
# COSMOS connection-string convenience.
# A single env var `COSMOS` may carry a full Cosmos DB connection string,
# e.g. "AccountEndpoint=https://acct.documents.azure.com:443/;AccountKey=<key>==;".
# When set, split it into the discrete COSMOS_ENDPOINT / COSMOS_KEY vars
# that the agent's app, the verifier (conftest) and the live-account
# logic below all already consume. This lets a live account be supplied
# as ONE encrypted env (e.g. `msbench-cli run --encrypted-env COSMOS`)
# instead of two. Parsing runs BEFORE live-mode detection, so setting
# COSMOS alone is enough to switch off the bundled emulator.
# The AccountKey is base64 (chars A-Za-z0-9+/=) and never contains ';',
# so splitting each field on ';' is safe and order-independent.
# ---------------------------------------------------------------------
if [ -n "${COSMOS:-}" ]; then
    _cs_ep="$(printf '%s' "$COSMOS" | sed -n 's/.*[Aa]ccount[Ee]ndpoint=\([^;]*\).*/\1/p')"
    _cs_key="$(printf '%s' "$COSMOS" | sed -n 's/.*[Aa]ccount[Kk]ey=\([^;]*\).*/\1/p')"
    if [ -n "$_cs_ep" ] && [ -n "$_cs_key" ]; then
        export COSMOS_ENDPOINT="$_cs_ep"
        export COSMOS_KEY="$_cs_key"
        echo "[runner] parsed COSMOS connection string -> COSMOS_ENDPOINT=$COSMOS_ENDPOINT (COSMOS_KEY hidden)"
    else
        echo "[runner] WARNING: COSMOS is set but AccountEndpoint/AccountKey could not be parsed; leaving COSMOS_ENDPOINT/COSMOS_KEY unchanged." >&2
    fi
    unset _cs_ep _cs_key
fi

# ---------------------------------------------------------------------
# Live-account mode.
# When COSMOS_ENDPOINT points at a real Azure Cosmos account (anything
# that is not the in-container emulator on localhost), we:
#   (a) skip starting the bundled emulator entirely;
#   (b) give each SDK its own database, so several SDK instances that
#       share one account never read/write each other's data;
#   (c) give each SDK its own app listener port, so several instances
#       that happen to share a network namespace (same msbench run)
#       never collide on the HTTP port.
# This is what makes "all five SDKs in ONE run against one live account"
# safe. Default (emulator) behaviour is completely unchanged.
# ---------------------------------------------------------------------
LIVE_MODE=0
case "${COSMOS_ENDPOINT:-}" in
    ""|*localhost*|*127.0.0.1*|*0.0.0.0*) LIVE_MODE=0 ;;
    *) LIVE_MODE=1 ;;
esac

if [ "$LIVE_MODE" = "1" ]; then
    # Per-SDK database isolation. Overrides the image's baked default so
    # both the agent's app and the verifier target the same unique db.
    # Prefix defaults to the scenario database baked into the image.
    export COSMOS_DATABASE="${COSMOS_DATABASE_PREFIX:-${COSMOS_DATABASE:-mosaic}}-${SDK}"
    # Per-SDK listener port. The app must honour $APP_PORT (verifier
    # contract), and the verifier reads the same APP_PORT, so they stay
    # aligned. Distinct ports keep co-located instances from fighting.
    case "$SDK" in
        python) APP_PORT="${APP_PORT_PYTHON:-9080}" ;;
        dotnet) APP_PORT="${APP_PORT_DOTNET:-8082}" ;;
        java)   APP_PORT="${APP_PORT_JAVA:-8083}" ;;
        nodejs) APP_PORT="${APP_PORT_NODEJS:-8084}" ;;
        go)     APP_PORT="${APP_PORT_GO:-8085}" ;;
    esac
    export APP_PORT
    echo "[runner] LIVE account mode: endpoint=$COSMOS_ENDPOINT database=$COSMOS_DATABASE app_port=$APP_PORT"
fi

section "1/6 Starting Cosmos emulator"
if [ "$LIVE_MODE" = "1" ]; then
    echo "[runner] live account configured; skipping bundled emulator startup."
elif ! /usr/local/bin/start-emulator; then
    echo "[runner] emulator failed to start; aborting" | tee -a "$LOG_DIR/emulator.log"
    exit 0  # exit 0 because we already wrote reward=0; non-zero exit confuses Harbor
fi

section "2/6 Verifying /app/build.sh and /app/run.sh exist"
for f in build.sh run.sh; do
    if [ ! -x "$APP_DIR/$f" ] && [ ! -f "$APP_DIR/$f" ]; then
        echo "[runner] FATAL: $APP_DIR/$f is missing or not executable." | tee "$LOG_DIR/contract.log"
        echo "[runner] The agent must produce /app/build.sh (one-shot setup) and /app/run.sh (foreground server)." | tee -a "$LOG_DIR/contract.log"
        exit 0
    fi
    chmod +x "$APP_DIR/$f" || true
done

section "3/6 Running /app/build.sh"
( cd "$APP_DIR" && ./build.sh ) > "$LOG_DIR/build.log" 2>&1
BUILD_RC=$?
if [ $BUILD_RC -ne 0 ]; then
    echo "[runner] /app/build.sh exited $BUILD_RC. Tail of $LOG_DIR/build.log:"
    tail -n 80 "$LOG_DIR/build.log" || true
    exit 0
fi

section "4/6 Launching /app/run.sh in background"
# The agent may have launched /app/run.sh during its session and left it
# bound to $APP_PORT (or the container is reused across runs). Kill any
# squatter so the verifier's own launch can bind. The base images do NOT
# ship fuser/ss/lsof, so prefer those when present but fall back to a
# python3 /proc walker, which needs no external tools (we run as root).
free_app_port() {
    local port="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -k -n tcp "$port" 2>/dev/null || true
    fi
    if command -v ss >/dev/null 2>&1; then
        ss -ltnHp "sport = :$port" 2>/dev/null \
            | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u \
            | while read -r pid; do
                [ -n "$pid" ] && kill -9 "$pid" 2>/dev/null || true
            done
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 - "$port" <<'PYEOF'
import glob, os, signal, sys
port = int(sys.argv[1])
want = "%04X" % port
inodes = set()
for path in ("/proc/net/tcp", "/proc/net/tcp6"):
    try:
        with open(path) as fh:
            next(fh)  # skip header
            for line in fh:
                p = line.split()
                if len(p) < 10 or p[3] != "0A":  # 0A == LISTEN
                    continue
                if p[1].rsplit(":", 1)[-1].upper() == want:
                    inodes.add(p[9])
    except OSError:
        pass
if not inodes:
    sys.exit(0)
killed = set()
for fd in glob.glob("/proc/[0-9]*/fd/*"):
    try:
        link = os.readlink(fd)
    except OSError:
        continue
    if link.startswith("socket:["):
        ino = link[8:-1]
        if ino in inodes:
            pid = int(fd.split("/")[2])
            if pid != os.getpid():
                killed.add(pid)
for pid in killed:
    try:
        os.kill(pid, signal.SIGKILL)
        print("[runner] killed stale process on :%d (pid=%d)" % (port, pid))
    except OSError:
        pass
PYEOF
    fi
}
free_app_port "$APP_PORT"
# Give the port a moment to free up after SIGKILL.
for i in 1 2 3 4 5; do
    curl -fsS --max-time 1 "http://localhost:$APP_PORT/health" >/dev/null 2>&1 || break
    sleep 1
done
( cd "$APP_DIR" && ./run.sh ) > "$LOG_DIR/app.log" 2>&1 &
APP_PID=$!
echo "$APP_PID" > "$LOG_DIR/app.pid"
trap '[ -n "${APP_PID:-}" ] && kill "$APP_PID" 2>/dev/null || true' EXIT

section "5/6 Waiting for http://localhost:$APP_PORT/health"
HEALTH_OK=0
for i in $(seq 1 90); do
    if curl -fsS --max-time 3 "http://localhost:$APP_PORT/health" >/dev/null 2>&1; then
        HEALTH_OK=1
        echo "[runner] /health ok after ${i}s"
        break
    fi
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        echo "[runner] FATAL: app process exited before /health became ready"
        tail -n 80 "$LOG_DIR/app.log" || true
        exit 0
    fi
    sleep 1
done
if [ $HEALTH_OK -ne 1 ]; then
    echo "[runner] FATAL: /health did not respond within 90s"
    tail -n 80 "$LOG_DIR/app.log" || true
    exit 0
fi

section "6/6 Running pytest grader"
# In emulator mode the bundled docker_entrypoint.sh overrides
# COSMOS_ENDPOINT to `https://localhost:8081` even though we launched it
# with --protocol http. Reassert the verifier's view so the cosmos
# client doesn't try TLS on a plaintext port. In live mode we must NOT
# touch COSMOS_ENDPOINT — it already points at the real account.
if [ "$LIVE_MODE" = "1" ]; then
    echo "[runner] live account: COSMOS_ENDPOINT=$COSMOS_ENDPOINT database=$COSMOS_DATABASE (not re-pinned)"
else
    export COSMOS_ENDPOINT="${COSMOS_PROTOCOL:-http}://localhost:8081"
    echo "[runner] COSMOS_ENDPOINT pinned to $COSMOS_ENDPOINT for pytest"
fi

# Run all shared checks + the task-specific checks. Order reflects intent:
# check_behavior.py is the concrete emulator+request suite (the defensible
# core); check_source.py / check_skills.py remain STATIC signals for
# client-side configuration the single-node emulator cannot prove. The
# task's checks.py may add more SDK-specific assertions; if absent, only the
# shared ones run.
PYTEST_TARGETS=("/verifier/check_api.py" "/verifier/check_behavior.py" "/verifier/check_cosmos.py" "/verifier/check_source.py" "/verifier/check_skills.py")
if [ -f "/tests/checks.py" ]; then
    PYTEST_TARGETS+=("/tests/checks.py")
fi

# Force conftest discovery from /verifier.
export PYTHONDONTWRITEBYTECODE=1
PYTEST_OUT="$LOG_DIR/pytest.log"

# Use an isolated python so the agent's build.sh cannot pollute the
# verifier's azure-cosmos / requests / pytest install (e.g. by
# pip-installing an incompatible version into system site-packages).
if [ -x /opt/verifier-venv/bin/python ]; then
    VERIFIER_PY=/opt/verifier-venv/bin/python
else
    VERIFIER_PY=python3
fi

"$VERIFIER_PY" -m pytest -v --tb=short --no-header \
    --rootdir=/verifier \
    --override-ini "python_files=check_*.py checks.py" \
    "${PYTEST_TARGETS[@]}" \
    > "$PYTEST_OUT" 2>&1
PYTEST_RC=$?

echo
echo "=== pytest output (tail) ==="
tail -n 80 "$PYTEST_OUT" || true
echo "=== end pytest tail ==="

if [ $PYTEST_RC -eq 0 ]; then
    section "PASS — writing reward=1"
    echo "1" > "$REWARD_FILE"
else
    section "FAIL — reward stays at 0 (see $PYTEST_OUT)"
fi

# Always exit 0 so Harbor reads the reward file rather than treating the
# verifier script itself as failed.
exit 0
