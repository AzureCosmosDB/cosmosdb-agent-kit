FROM cosmos-mosaic-base:latest
ENV SDK="nodejs"
COPY tasks/iot-nodejs/tests/         /tests/
COPY tasks/iot-nodejs/solution/      /solution/
COPY tasks/iot-nodejs/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app
