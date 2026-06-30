FROM cosmos-mosaic-base:latest
ENV SDK="go"
COPY tasks/iot-go/tests/         /tests/
COPY tasks/iot-go/solution/      /solution/
COPY tasks/iot-go/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app
