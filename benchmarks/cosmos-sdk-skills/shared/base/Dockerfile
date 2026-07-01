# cosmos-mosaic-base
# ------------------
# Shared base image for every mosaic-<sdk> task. Carries:
#   - Cosmos DB Linux vnext emulator binaries
#   - Python 3.12 + verifier dependencies (pytest, requests, azure-cosmos)
#   - The shared /verifier/ grader library
#   - /logs/verifier/ ready for the reward file
#
# Per-SDK task Dockerfiles do FROM cosmos-mosaic-base and add only the
# SDK runtime + the per-task /reference and /tests payload.
#
# The Cosmos emulator's default ENTRYPOINT runs the emulator as PID 1.
# We do NOT want that — Harbor needs to drive `tests/test.sh` as the
# verifier entrypoint, and the agent runs commands as a shell. So we
# override the ENTRYPOINT to /bin/bash and provide start-emulator.sh,
# which test.sh calls to start the emulator in the background.

ARG EMULATOR_TAG=vnext-preview
FROM mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:${EMULATOR_TAG}

USER root
WORKDIR /

# Reset the entrypoint — the emulator image normally runs the emulator
# as PID 1; we want the container to start as a bash shell and let
# test.sh control the emulator lifecycle.
ENTRYPOINT []
CMD ["/bin/bash"]

# Install Python 3.12 + verifier dependencies. The base image is
# Mariner-based; use tdnf when available, fall back to dnf/apt.
RUN set -eux; \
    if command -v tdnf >/dev/null 2>&1; then \
        tdnf install -y python3 python3-pip ca-certificates curl jq procps tar gzip && tdnf clean all; \
    elif command -v dnf >/dev/null 2>&1; then \
        dnf install -y python3 python3-pip ca-certificates curl jq procps-ng tar gzip && dnf clean all; \
    else \
        apt-get update && apt-get install -y --no-install-recommends \
            python3 python3-pip ca-certificates curl jq procps tar gzip \
            && rm -rf /var/lib/apt/lists/*; \
    fi; \
    # CES /save.sh + /restore.sh invoke `python` (not `python3`). Mariner
    # only installs `python3`, so add the bare `python` symlink the CES
    # contract relies on.
    if ! command -v python >/dev/null 2>&1; then ln -sf "$(command -v python3)" /usr/local/bin/python; fi

# Verifier dependencies. Pin versions so the benchmark is reproducible.
# pathspec is used by /glob_files.py (part of the CES save-secrets payload).
RUN python3 -m pip install --no-cache-dir \
    pytest==8.3.3 \
    requests==2.32.3 \
    azure-cosmos==4.7.0 \
    pyyaml==6.0.2 \
    pathspec==0.12.1

# Isolated venv for the verifier so the agent's /app/build.sh cannot
# accidentally pollute (e.g. by `pip install`ing a different
# azure-cosmos version into system site-packages and shadowing
# `from azure.cosmos import CosmosClient`). The verifier runner uses
# /opt/verifier-venv/bin/python preferentially.
RUN python3 -m venv /opt/verifier-venv && \
    /opt/verifier-venv/bin/pip install --no-cache-dir \
        pytest==8.3.3 \
        requests==2.32.3 \
        azure-cosmos==4.7.0 \
        pyyaml==6.0.2

# Shared verifier library + emulator helper. Both are owned by the
# image, not by the agent — the agent's /app/ cannot modify these.
COPY shared/verifier/ /verifier/
COPY shared/base/start-emulator.sh /usr/local/bin/start-emulator
RUN chmod +x /usr/local/bin/start-emulator

# MSBench / CES backend contract files. The CES runtime expects all of
# these to exist at root inside the task image:
#   /ces_activate.sh          legacy env-activation stub (no-op)
#   /entry.sh                 master orchestrator (encrypt -> agent -> decrypt -> eval -> parse)
#   /save.sh, /restore.sh     secret encrypt/decrypt
#   /glob_files.py            helper for save.sh (needs pathspec)
#   /cut_metadata.py          helper for save.sh (strips non-public metadata keys)
#   /parse.py                 Harbor reward -> MSBench eval.json
#   /secret_files.txt         globs for what to encrypt before agent runs
#   /nonsecret_metadata_keys.txt  metadata keys agent is allowed to see
#   /opt/activate_python.sh   no-op python-env activator
# Per-task /drop/metadata.json is COPIED by each task Dockerfile.
COPY shared/ces/ces_activate.sh                /ces_activate.sh
COPY shared/ces/entry.sh                       /entry.sh
COPY shared/ces/save.sh                        /save.sh
COPY shared/ces/restore.sh                     /restore.sh
COPY shared/ces/glob_files.py                  /glob_files.py
COPY shared/ces/cut_metadata.py                /cut_metadata.py
COPY shared/ces/parse.py                       /parse.py
COPY shared/ces/secret_files.txt               /secret_files.txt
COPY shared/ces/nonsecret_metadata_keys.txt    /nonsecret_metadata_keys.txt
COPY shared/ces/activate_python.sh             /opt/activate_python.sh
# CES injects its own broken /glob_files.py at runtime (TypeError in the
# pathspec on_error callback when /var/lock is a dangling symlink),
# clobbering ours. /opt/ is not on CES's overwrite path, so we stage a
# self-contained pure-bash encryption script there and entry.sh calls it
# directly instead of /save.sh. See the comment in safe_save.sh.
COPY shared/ces/safe_save.sh                   /opt/safe_save.sh
RUN chmod +x /ces_activate.sh /entry.sh /save.sh /restore.sh /opt/activate_python.sh /opt/safe_save.sh

# Directories the verifier and CES runtime write to.
RUN mkdir -p /logs/verifier /app /reference /output /drop /agent /testbed

# The vnext-preview emulator (postgres + rust gateway) must run as the
# unprivileged `cosmosdev` user. CES entry.sh + runner.sh run as root.
# Both write to /logs (emulator -> /logs/*.log; verifier -> /logs/verifier/);
# make the relevant dirs world-writable (sticky) so the two cooperate.
RUN chown -R cosmosdev:cosmosdev /data /home/cosmosdev 2>/dev/null || true; \
    chmod -R 1777 /logs /output /drop /agent /testbed /app /reference 2>/dev/null || true

# -----------------------------------------------------------------------------
# Pre-install the public @github/copilot CLI so the --runner approach can
# invoke it without going through MSBench's agent-downloader (which needs
# Microsoft-internal RBAC + unzip on this Mariner-based image).
# Pin to the same version the working cosmosdb-rules benchmark uses.
# -----------------------------------------------------------------------------
RUN npm install -g @github/copilot@1.0.54

# -----------------------------------------------------------------------------
# Bake the cosmosdb-best-practices skill rules into the image so runner.sh
# can stage them as a custom Copilot agent at run time.
# The build context root is `cosmos-sdk-skills-bench/`, and the skills live
# in the sibling `cosmosdb-agent-kit/` repo. The build wrapper stages a copy
# at `cosmos-sdk-skills-bench/.cosmosdb-best-practices-skills/` before
# invoking `docker build`, so we COPY from there to avoid leaking the whole
# agent-kit repo into the build context.
# -----------------------------------------------------------------------------
COPY .cosmosdb-best-practices-skills /opt/cosmosdb-agent-kit/skills/cosmosdb-best-practices

# Well-known emulator endpoint + key are constants. Tasks export these
# into the agent's environment so the agent reads them from env, not
# from a hardcoded literal in source.
ENV COSMOS_ENDPOINT="http://localhost:8081" \
    COSMOS_KEY="C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==" \
    COSMOS_DATABASE="mosaic" \
    COSMOS_USERS_CONTAINER="users" \
    APP_PORT="9080" \
    APP_WORKDIR="/app" \
    REFERENCE_DIR="/reference" \
    VERIFIER_LOG_DIR="/logs/verifier"
