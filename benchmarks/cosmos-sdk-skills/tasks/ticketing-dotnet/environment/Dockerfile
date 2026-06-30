FROM cosmos-mosaic-base:latest
ENV SDK="dotnet"
COPY tasks/ticketing-dotnet/tests/         /tests/
COPY tasks/ticketing-dotnet/solution/      /solution/
COPY tasks/ticketing-dotnet/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app