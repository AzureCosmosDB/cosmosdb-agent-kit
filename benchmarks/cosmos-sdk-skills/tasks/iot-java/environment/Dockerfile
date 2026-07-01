FROM cosmos-mosaic-base:latest
ENV SDK="java"
COPY tasks/iot-java/tests/         /tests/
COPY tasks/iot-java/solution/      /solution/
COPY tasks/iot-java/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app
