FROM cosmos-mosaic-base:latest
ENV SDK="go"
ENV SCENARIO="iot" \
    COSMOS_DATABASE="sensorgrid" \
    COSMOS_DEVICES_CONTAINER="devices" \
    COSMOS_READINGS_CONTAINER="readings"
COPY tasks/iot-go/tests/         /tests/
COPY tasks/iot-go/solution/      /solution/
COPY tasks/iot-go/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app