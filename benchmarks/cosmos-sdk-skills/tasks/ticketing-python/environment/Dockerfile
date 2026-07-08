FROM cosmos-mosaic-base:latest
ENV SDK="python"
ENV SCENARIO="ticketing" \
    COSMOS_DATABASE="ticketwave" \
    COSMOS_EVENTS_CONTAINER="events" \
    COSMOS_TICKETS_CONTAINER="tickets"
RUN tdnf install -y which zip unzip \
    && printf '#!/bin/sh\nexec tdnf "$@"\n' > /usr/local/bin/dnf \
    && chmod +x /usr/local/bin/dnf
COPY reference /reference
RUN pip3 install --no-cache-dir -r /reference/requirements.txt
WORKDIR /app
