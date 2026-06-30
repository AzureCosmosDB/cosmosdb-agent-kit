# mosaic-nodejs task image
FROM cosmos-mosaic-base:latest

ENV SDK="nodejs"

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

COPY tasks/mosaic-nodejs/reference/     /reference/
COPY tasks/mosaic-nodejs/tests/         /tests/
COPY tasks/mosaic-nodejs/solution/      /solution/
COPY tasks/mosaic-nodejs/instruction.md /instruction.md
COPY tasks/mosaic-nodejs/metadata.json  /drop/metadata.json

RUN cd /reference && npm install --omit=dev

RUN chmod +x /solution/solve.sh /tests/test.sh

WORKDIR /app
