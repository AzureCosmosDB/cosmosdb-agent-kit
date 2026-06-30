FROM cosmos-mosaic-base:latest
ENV SDK="python"
COPY tasks/iot-python/tests/         /tests/
COPY tasks/iot-python/solution/      /solution/
COPY tasks/iot-python/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app
