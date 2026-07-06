# mosaic-java task image
#
# Multi-stage: pull pre-built Temurin JDK 21 + Maven from official
# images (mcr.microsoft.com/openjdk and maven:eclipse-temurin) rather
# than curling tarballs at build time. The latter fails inside Docker
# Desktop's buildkit with curl exit 7 (no route to host) on Windows.

FROM maven:3.9-eclipse-temurin-21 AS jdk_provider

FROM cosmos-mosaic-base:latest

ENV SDK="java"

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

COPY tasks/mosaic-java/reference/     /reference/
COPY tasks/mosaic-java/tests/         /tests/
COPY tasks/mosaic-java/solution/      /solution/
COPY tasks/mosaic-java/instruction.md /instruction.md
COPY tasks/mosaic-java/metadata.json  /drop/metadata.json

# Warm the local Maven cache with the reference impl's dependencies.
RUN cd /reference && mvn -B -q dependency:go-offline || true

RUN chmod +x /solution/solve.sh /tests/test.sh

WORKDIR /app
