FROM cosmos-mosaic-base:latest
ENV SDK="dotnet"
COPY tasks/iot-dotnet/tests/         /tests/
COPY tasks/iot-dotnet/solution/      /solution/
COPY tasks/iot-dotnet/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app
