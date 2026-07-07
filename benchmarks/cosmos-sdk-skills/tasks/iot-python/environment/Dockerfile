FROM cosmos-mosaic-base:latest
ENV SDK="python"
ENV SCENARIO="iot" \
    COSMOS_DATABASE="sensorgrid" \
    COSMOS_DEVICES_CONTAINER="devices" \
    COSMOS_READINGS_CONTAINER="readings"
COPY tasks/iot-python/reference/     /reference/
COPY tasks/iot-python/tests/         /tests/
COPY tasks/iot-python/solution/      /solution/
COPY tasks/iot-python/instruction.md /instruction.md
COPY tasks/iot-python/metadata.json  /drop/metadata.json
RUN pip3 install --no-cache-dir -r /reference/requirements.txt
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app