FROM cosmos-mosaic-base:latest
ENV SDK="python"
COPY tasks/ticketing-python/tests/         /tests/
COPY tasks/ticketing-python/solution/      /solution/
COPY tasks/ticketing-python/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app