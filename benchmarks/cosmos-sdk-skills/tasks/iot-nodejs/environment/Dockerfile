FROM cosmos-mosaic-base:latest
ENV SDK="nodejs"
ENV SCENARIO="iot" \
    COSMOS_DATABASE="sensorgrid" \
    COSMOS_DEVICES_CONTAINER="devices" \
    COSMOS_READINGS_CONTAINER="readings"
COPY tasks/iot-nodejs/tests/         /tests/
COPY tasks/iot-nodejs/solution/      /solution/
COPY tasks/iot-nodejs/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app