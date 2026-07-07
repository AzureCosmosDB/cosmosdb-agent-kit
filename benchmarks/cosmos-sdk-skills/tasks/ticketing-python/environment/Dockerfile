FROM cosmos-mosaic-base:latest
ENV SDK="python"
ENV SCENARIO="ticketing" \
    COSMOS_DATABASE="ticketwave" \
    COSMOS_EVENTS_CONTAINER="events" \
    COSMOS_TICKETS_CONTAINER="tickets"
COPY tasks/ticketing-python/reference/     /reference/
COPY tasks/ticketing-python/tests/         /tests/
COPY tasks/ticketing-python/solution/      /solution/
COPY tasks/ticketing-python/instruction.md /instruction.md
COPY tasks/ticketing-python/metadata.json  /drop/metadata.json
RUN pip3 install --no-cache-dir -r /reference/requirements.txt
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app