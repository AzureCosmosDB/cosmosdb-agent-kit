#!/usr/bin/env bash
# Start the Cosmos DB Linux vnext emulator in the background and block
# until the data endpoint accepts requests. Idempotent: if the emulator
# is already up, returns immediately.
#
# Used by each task's tests/test.sh as the first step of the verifier.

set -euo pipefail

LOG_DIR="${VERIFIER_LOG_DIR:-/logs/verifier}"
mkdir -p "$LOG_DIR"
EMU_LOG="$LOG_DIR/emulator.log"

# The vnext-preview emulator uses HTTP on 8081 by default.
PROTOCOL="${COSMOS_PROTOCOL:-http}"

probe() {
    curl -ks --max-time 2 "${PROTOCOL}://localhost:8081/_explorer/emulator.pem" >/dev/null 2>&1 \
        || curl -ks --max-time 2 "${PROTOCOL}://localhost:8081/" >/dev/null 2>&1
}

# The vnext emulator's gateway serves static endpoints (/, emulator.pem) BEFORE
# the pgcosmos data-plane extension has finished initializing. During that window
# any real Cosmos operation returns HTTP 503 "pgcosmos extension is still starting;
# retry request shortly". Eager SDK clients (dotnet/java/nodejs/go) that open a
# connection at process start crash on that 503, so the port-only probe above is
# not a sufficient readiness signal. dataplane_ready() issues a signed GET /dbs
# and only reports success once the data plane answers (non-5xx).
COSMOS_KEY_WELL_KNOWN="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
dataplane_ready() {
    COSMOS_KEY="${COSMOS_KEY:-$COSMOS_KEY_WELL_KNOWN}" PROTOCOL="$PROTOCOL" python3 - <<'PY'
import os, sys, hmac, base64, hashlib, ssl, urllib.parse, urllib.request, urllib.error
from email.utils import formatdate
key = os.environ.get("COSMOS_KEY", "")
protocol = os.environ.get("PROTOCOL", "http")
date = formatdate(usegmt=True)
# Cosmos master-key auth: sign "verb\nresourceType\nresourceId\ndate\n\n" (lowercased).
text = "get\ndbs\n\n" + date.lower() + "\n\n"
sig = base64.b64encode(
    hmac.new(base64.b64decode(key), text.encode("utf-8"), hashlib.sha256).digest()
).decode()
auth = urllib.parse.quote("type=master&ver=1.0&sig=" + sig)
req = urllib.request.Request(
    protocol + "://localhost:8081/dbs",
    headers={"Authorization": auth, "x-ms-date": date, "x-ms-version": "2018-12-31"},
)
# The emulator's https gateway uses a self-signed cert; skip verification here
# (this is only a readiness probe, not app traffic).
ctx = ssl._create_unverified_context() if protocol == "https" else None
try:
    with urllib.request.urlopen(req, timeout=3, context=ctx) as r:
        sys.exit(0 if r.status < 500 else 1)
except urllib.error.HTTPError as e:
    # 5xx (esp. 503 "still starting") => not ready. Any 4xx means the data
    # plane is live and responding, which is all we need to gate on.
    sys.exit(1 if e.code >= 500 else 0)
except Exception:
    sys.exit(1)
PY
}

wait_dataplane() {
    local secs="${DATAPLANE_WAIT_SECS:-300}"
    echo -n "[start-emulator] waiting up to ${secs}s for pgcosmos data plane "
    for _ in $(seq 1 "$secs"); do
        if dataplane_ready; then
            echo " ok"
            return 0
        fi
        sleep 1
        echo -n "+"
    done
    echo " FAILED: data plane (pgcosmos) not ready"
    return 1
}

if probe; then
    echo "[start-emulator] emulator already responding on 8081"
    if wait_dataplane; then exit 0; else exit 1; fi
fi

# The vnext-preview image launches the emulator via
# /scripts/docker/docker_entrypoint.sh. Other candidates kept as fallbacks.
EMULATOR_BIN=""
for candidate in \
    /scripts/docker/docker_entrypoint.sh \
    /usr/local/bin/cosmos-emulator \
    /usr/local/bin/azure-cosmos-emulator \
    /opt/cosmos-emulator/start.sh \
    /tmp/cosmos/emulator.sh \
    /Cosmos/start.sh; do
    if [ -x "$candidate" ]; then
        EMULATOR_BIN="$candidate"
        break
    fi
done

if [ -z "$EMULATOR_BIN" ]; then
    echo "[start-emulator] FATAL: no emulator binary found." >&2
    echo "[start-emulator] Update start-emulator.sh with the correct path for the chosen EMULATOR_TAG." >&2
    exit 1
fi

echo "[start-emulator] launching $EMULATOR_BIN in background, logging to $EMU_LOG"
# vnext-preview emulator must run as the `cosmosdev` user (postgres refuses
# to start as root). The remote backend's Mariner image has no `su`/`runuser`/`setpriv`
# and its `sudo` is broken (PAM auth fails), so use python3 to drop privs
# directly via setuid/setgid. Locally on a dev box we usually have sudo,
# so fall back to that when python or cosmosdev isn't around.
if ! id cosmosdev >/dev/null 2>&1; then
    echo "[start-emulator] FATAL: cosmosdev user missing from container" >&2
    exit 1
fi

# The remote backend mounts /logs and /data as root-owned at runtime, overriding the image's
# baked permissions. Since the emulator runs as the unprivileged `cosmosdev`
# user, it cannot write to those dirs (postgres data, SSL certs, *.log).
# start-emulator runs as root here, so hand ownership to cosmosdev before the
# privilege drop. Keep /logs/verifier writable by root too (the verifier writes
# pytest.log etc. as root later); root can always write regardless of owner.
if [ "$(id -u)" = "0" ]; then
    for d in /logs /data; do
        mkdir -p "$d" 2>/dev/null || true
        chown -R cosmosdev:cosmosdev "$d" 2>/dev/null || true
        chmod -R u+rwX,g+rwX "$d" 2>/dev/null || true
    done
fi

if command -v python3 >/dev/null 2>&1; then
    nohup python3 - "$EMULATOR_BIN" "$PROTOCOL" >"$EMU_LOG" 2>&1 <<'PY' &
import os, pwd, sys
bin_path, protocol = sys.argv[1], sys.argv[2]
p = pwd.getpwnam("cosmosdev")
os.setgid(p.pw_gid)
os.setgroups([p.pw_gid])
os.setuid(p.pw_uid)
os.environ["HOME"] = p.pw_dir
os.environ["USER"] = "cosmosdev"
os.chdir(p.pw_dir)
# Move the emulator's own health endpoint off :8080 to keep the default port
# range clear. The agent's app listens on $APP_PORT (9080, baked into the image).
os.execvp("bash", ["bash", "-lc", f"bash {bin_path!r} --protocol {protocol} --health-port 8079"])
PY
elif command -v sudo >/dev/null 2>&1 && sudo -n -u cosmosdev true 2>/dev/null; then
    nohup sudo -u cosmosdev -E -H bash -lc "bash '$EMULATOR_BIN' --protocol $PROTOCOL --health-port 8079" \
        >"$EMU_LOG" 2>&1 &
else
    nohup bash "$EMULATOR_BIN" --protocol "$PROTOCOL" --health-port 8079 >"$EMU_LOG" 2>&1 &
fi
EMU_PID=$!
echo "$EMU_PID" > "$LOG_DIR/emulator.pid"

# Dump the full picture of a failed startup. The postgres init error (the
# real root cause) appears near the TOP of the log; the readiness health-poll
# loop floods the bottom. Tail-only diagnostics hid the cause in the past, so
# show both head and tail.
dump_emulator_log() {
    echo "[start-emulator] head of $EMU_LOG (postgres init / real error):"
    head -n 60 "$EMU_LOG" 2>/dev/null || true
    echo "[start-emulator] ...tail of $EMU_LOG:"
    tail -n 40 "$EMU_LOG" 2>/dev/null || true
}

# Wait for the emulator to accept connections. The vnext emulator bundles
# PostgreSQL + Citus + ~10 heavy extensions; on a contended remote-backend host that
# init can take several minutes (locally it's ~3s). Default to a generous
# ceiling and allow override via EMULATOR_WAIT_SECS.
EMULATOR_WAIT_SECS="${EMULATOR_WAIT_SECS:-420}"
echo -n "[start-emulator] waiting up to ${EMULATOR_WAIT_SECS}s for ${PROTOCOL}://localhost:8081 "
for i in $(seq 1 "$EMULATOR_WAIT_SECS"); do
    if probe; then
        echo " ok (after ${i}s)"
        # The emulator's docker_entrypoint.sh also spawns a `health_check_server`
        # binary on :8080 that we cannot disable via CLI flag in this image.
        # The agent's app listens on $APP_PORT (9080, baked into the image), not
        # :8080, but we clear this stray server as hygiene so nothing squats near
        # the app's port range. The data gateway on :8081 is unaffected.
        for pid in $(pgrep -f health_check_server 2>/dev/null); do
            kill "$pid" 2>/dev/null || true
        done
        if wait_dataplane; then exit 0; else dump_emulator_log; exit 1; fi
    fi
    if ! kill -0 "$EMU_PID" 2>/dev/null; then
        echo " FAILED: emulator process exited"
        dump_emulator_log
        exit 1
    fi
    sleep 1
    echo -n "."
done

echo " FAILED: timed out after ${EMULATOR_WAIT_SECS}s"
dump_emulator_log
exit 1
