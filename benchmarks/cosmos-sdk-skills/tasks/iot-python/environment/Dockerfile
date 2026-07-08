FROM cosmos-mosaic-base:latest
ENV SDK="python"
ENV SCENARIO="iot" \
    COSMOS_DATABASE="sensorgrid" \
    COSMOS_DEVICES_CONTAINER="devices" \
    COSMOS_READINGS_CONTAINER="readings"
# harbor-format-curation's install_all.sh only detects apt-get / dnf / yum / apk.
# This base is Azure Linux (tdnf), so provide `which` and a dnf->tdnf shim so
# harbor's RPM install branch runs cleanly instead of falling back to apt-get.
# Also pre-install zip/unzip: the CES agent harness cannot install them on tdnf
# ("Unsupported package manager") and needs them to package agent output, so
# baking them in makes CES skip its install step (as it does for docker/node).
RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf
COPY reference /reference
RUN pip3 install --no-cache-dir -r /reference/requirements.txt
WORKDIR /app
