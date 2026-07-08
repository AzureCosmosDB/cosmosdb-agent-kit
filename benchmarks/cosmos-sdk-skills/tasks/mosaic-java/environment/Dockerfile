FROM maven:3.9-eclipse-temurin-21 AS jdk_provider

FROM cosmos-mosaic-base:latest

ENV SDK="java"

RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf

# The azure-cosmos Java v4 SDK always negotiates TLS for its Gateway HTTP
# client (unlike the JS/Python/Go/.NET SDKs, it will not talk plain HTTP to
# the gateway). The vnext emulator defaults to HTTP on :8081, so run this
# instance's emulator in HTTPS mode and point the app at the TLS endpoint.
# run.sh trusts the emulator's self-signed cert before launching.
ENV COSMOS_PROTOCOL="https" \
    COSMOS_ENDPOINT="https://localhost:8081"

# Copy the JDK + Maven from the provider stage. This is a single-shot
# COPY and incurs no network at build time.
COPY --from=jdk_provider /opt/java/openjdk /opt/jdk
COPY --from=jdk_provider /usr/share/maven  /opt/maven

RUN ln -s /opt/jdk/bin/java   /usr/local/bin/java && \
    ln -s /opt/jdk/bin/javac  /usr/local/bin/javac && \
    ln -s /opt/jdk/bin/jar    /usr/local/bin/jar && \
    ln -s /opt/maven/bin/mvn  /usr/local/bin/mvn

ENV JAVA_HOME=/opt/jdk \
    MAVEN_HOME=/opt/maven \
    PATH=/opt/jdk/bin:/opt/maven/bin:$PATH

COPY reference /reference

# Warm the local Maven cache with the reference impl's dependencies.
RUN cd /reference && mvn -B -q dependency:go-offline || true

WORKDIR /app
