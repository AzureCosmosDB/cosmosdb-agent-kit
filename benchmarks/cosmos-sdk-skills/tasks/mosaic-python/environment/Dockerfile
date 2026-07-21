FROM cosmos-mosaic-base:latest

ENV SDK="python"

RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf

# Bake the reference implementation in. solve.sh copies it into /app
# when the oracle agent runs.
COPY reference /reference

# Pre-install the reference impl's dependencies into the image so the
# oracle agent runs quickly. The agent under evaluation will install
# their own deps from /app/build.sh; this just warms the wheel cache.
RUN pip3 install --no-cache-dir -r /reference/requirements.txt

WORKDIR /app
