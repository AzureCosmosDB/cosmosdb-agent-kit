# mosaic-dotnet task image
FROM cosmos-mosaic-base:latest

ENV SDK="dotnet"

# Install .NET 8 SDK. Mariner-based base needs the Microsoft repo or a
# tarball install. Use the official install script for portability.
RUN curl -fsSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh \
    && chmod +x /tmp/dotnet-install.sh \
    && /tmp/dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -s /usr/share/dotnet/dotnet /usr/local/bin/dotnet \
    && rm /tmp/dotnet-install.sh

ENV DOTNET_ROOT=/usr/share/dotnet \
    DOTNET_NOLOGO=1 \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1 \
    NUGET_XMLDOC_MODE=skip

COPY tasks/mosaic-dotnet/reference/     /reference/
COPY tasks/mosaic-dotnet/tests/         /tests/
COPY tasks/mosaic-dotnet/solution/      /solution/
COPY tasks/mosaic-dotnet/instruction.md /instruction.md
COPY tasks/mosaic-dotnet/metadata.json  /drop/metadata.json

# Pre-restore the reference impl's NuGet packages so the build doesn't
# hit the network at test time.
RUN cd /reference && dotnet restore

RUN chmod +x /solution/solve.sh /tests/test.sh

WORKDIR /app
