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

if probe; then
    echo "[start-emulator] emulator already responding on 8081"
    exit 0
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
# to start as root). CES's Mariner image has no `su`/`runuser`/`setpriv`
# and its `sudo` is broken (PAM auth fails), so use python3 to drop privs
# directly via setuid/setgid. Locally on a dev box we usually have sudo,
# so fall back to that when python or cosmosdev isn't around.
if ! id cosmosdev >/dev/null 2>&1; then
    echo "[start-emulator] FATAL: cosmosdev user missing from container" >&2
    exit 1
fi

# CES mounts /logs and /data as root-owned at runtime, overriding the image's
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
# Move emulator's own health endpoint off :8080 — the agent's app needs that port.
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
# PostgreSQL + Citus + ~10 heavy extensions; on a contended CES host that
# init can take several minutes (locally it's ~3s). Default to a generous
# ceiling and allow override via EMULATOR_WAIT_SECS.
EMULATOR_WAIT_SECS="${EMULATOR_WAIT_SECS:-420}"
echo -n "[start-emulator] waiting up to ${EMULATOR_WAIT_SECS}s for ${PROTOCOL}://localhost:8081 "
for i in $(seq 1 "$EMULATOR_WAIT_SECS"); do
    if probe; then
        echo " ok (after ${i}s)"
        # The emulator's docker_entrypoint.sh also spawns a `health_check_server`
        # binary on :8080 that we cannot disable via CLI flag in this image.
        # Kill it so the agent's app (which binds :8080 per /instruction.md)
        # can take the port. The data gateway on :8081 is unaffected.
        for pid in $(pgrep -f health_check_server 2>/dev/null); do
            kill "$pid" 2>/dev/null || true
        done
        exit 0
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
