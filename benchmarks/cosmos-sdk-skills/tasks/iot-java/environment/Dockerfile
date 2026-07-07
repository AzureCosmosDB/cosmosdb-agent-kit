FROM cosmos-mosaic-base:latest
ENV SDK="java"
ENV SCENARIO="iot" \
    COSMOS_DATABASE="sensorgrid" \
    COSMOS_DEVICES_CONTAINER="devices" \
    COSMOS_READINGS_CONTAINER="readings"
COPY tasks/iot-java/tests/         /tests/
COPY tasks/iot-java/solution/      /solution/
COPY tasks/iot-java/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app