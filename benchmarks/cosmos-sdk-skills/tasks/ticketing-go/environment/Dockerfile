FROM cosmos-mosaic-base:latest
ENV SDK="go"
COPY tasks/ticketing-go/tests/         /tests/
COPY tasks/ticketing-go/solution/      /solution/
COPY tasks/ticketing-go/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app