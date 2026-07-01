FROM cosmos-mosaic-base:latest
ENV SDK="java"
COPY tasks/ticketing-java/tests/         /tests/
COPY tasks/ticketing-java/solution/      /solution/
COPY tasks/ticketing-java/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app