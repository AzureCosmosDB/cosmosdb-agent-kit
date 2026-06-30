FROM cosmos-mosaic-base:latest
ENV SDK="nodejs"
COPY tasks/ticketing-nodejs/tests/         /tests/
COPY tasks/ticketing-nodejs/solution/      /solution/
COPY tasks/ticketing-nodejs/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app