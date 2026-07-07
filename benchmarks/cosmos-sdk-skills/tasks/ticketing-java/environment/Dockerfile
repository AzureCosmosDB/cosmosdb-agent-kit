FROM cosmos-mosaic-base:latest
ENV SDK="java"
ENV SCENARIO="ticketing" \
    COSMOS_DATABASE="ticketwave" \
    COSMOS_EVENTS_CONTAINER="events" \
    COSMOS_TICKETS_CONTAINER="tickets"
COPY tasks/ticketing-java/tests/         /tests/
COPY tasks/ticketing-java/solution/      /solution/
COPY tasks/ticketing-java/instruction.md /instruction.md
RUN chmod +x /solution/solve.sh /tests/test.sh
WORKDIR /app