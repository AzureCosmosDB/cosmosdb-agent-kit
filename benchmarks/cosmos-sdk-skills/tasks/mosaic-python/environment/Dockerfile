# mosaic-python task image
# ------------------------
# FROM cosmos-mosaic-base (emulator + python verifier + /verifier library).
# Adds: Python is already in the base image, so we only layer in the
# per-task /reference/ payload, /tests/, /instruction.md and /solution/.
#
# The agent's workspace is /app/ (created by the base image).

FROM cosmos-mosaic-base:latest

# Per-task SDK env. The agent reads SDK from /tests/test.sh but having it
# in the image env makes ad-hoc verifier invocations work too.
ENV SDK="python"

# Bake the reference implementation in. solve.sh copies it into /app
# when the oracle agent runs.
COPY tasks/mosaic-python/reference/     /reference/
COPY tasks/mosaic-python/tests/         /tests/
COPY tasks/mosaic-python/solution/      /solution/
COPY tasks/mosaic-python/instruction.md /instruction.md
COPY tasks/mosaic-python/metadata.json  /drop/metadata.json

# Pre-install the reference impl's dependencies into the image so the
# oracle agent runs quickly. The agent under evaluation will install
# their own deps from /app/build.sh; this just warms the wheel cache.
RUN pip3 install --no-cache-dir -r /reference/requirements.txt

RUN chmod +x /solution/solve.sh /tests/test.sh

WORKDIR /app
