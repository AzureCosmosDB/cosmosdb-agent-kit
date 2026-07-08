FROM cosmos-mosaic-base:latest

ENV SDK="nodejs"

RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf

# Install Node.js 20 via the official NodeSource binary tarball.
ARG NODE_URL="https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz"
RUN curl -fsSL "$NODE_URL" -o /tmp/node.tar.xz \
    && tar -xJf /tmp/node.tar.xz -C /opt \
    && mv /opt/node-v20.18.0-linux-x64 /opt/node \
    && ln -s /opt/node/bin/node /usr/local/bin/node \
    && ln -s /opt/node/bin/npm  /usr/local/bin/npm \
    && ln -s /opt/node/bin/npx  /usr/local/bin/npx \
    && rm /tmp/node.tar.xz

ENV NODE_HOME=/opt/node \
    PATH=/opt/node/bin:$PATH \
    NODE_TLS_REJECT_UNAUTHORIZED=0

COPY reference /reference

RUN cd /reference && npm install --omit=dev

WORKDIR /app
