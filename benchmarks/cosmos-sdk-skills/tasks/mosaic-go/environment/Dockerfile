FROM cosmos-mosaic-base:latest

ENV SDK="go"

RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf

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

COPY reference /reference

# Warm the Go module cache with the reference impl's dependencies.
RUN cd /reference && go mod download

WORKDIR /app
