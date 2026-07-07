FROM cosmos-mosaic-base:latest
ENV SDK="nodejs"
ENV SCENARIO="ticketing" \
    COSMOS_DATABASE="ticketwave" \
    COSMOS_EVENTS_CONTAINER="events" \
    COSMOS_TICKETS_CONTAINER="tickets"
COPY tasks/ticketing-nodejs/tests/         /tests/
COPY tasks/ticketing-nodejs/solution/      /solution/
COPY tasks/ticketing-nodejs/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app