# mosaic-go task image
FROM cosmos-mosaic-base:latest

ENV SDK="go"

# Install Go 1.22 from the official tarball.
ARG GO_URL="https://go.dev/dl/go1.22.8.linux-amd64.tar.gz"
RUN curl -fsSL "$GO_URL" -o /tmp/go.tar.gz \
    && tar -C /opt -xzf /tmp/go.tar.gz \
    && ln -s /opt/go/bin/go /usr/local/bin/go \
    && ln -s /opt/go/bin/gofmt /usr/local/bin/gofmt \
    && rm /tmp/go.tar.gz

ENV GOROOT=/opt/go \
    GOPATH=/root/go \
    PATH=/opt/go/bin:/root/go/bin:$PATH

COPY tasks/mosaic-go/reference/     /reference/
COPY tasks/mosaic-go/tests/         /tests/
COPY tasks/mosaic-go/solution/      /solution/
COPY tasks/mosaic-go/instruction.md /instruction.md
COPY tasks/mosaic-go/metadata.json  /drop/metadata.json

# Warm the Go module cache with the reference impl's dependencies.
RUN cd /reference && go mod download

RUN chmod +x /solution/solve.sh /tests/test.sh

WORKDIR /app
