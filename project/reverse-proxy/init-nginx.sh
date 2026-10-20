#!/bin/bash

KAFKA_UI_NET="kafka-ui"
KAFKA_UI_PORT=8080
MAX_WAIT=120
SECONDS=0

echo "Waiting for Kafka UI to accept connections..."

while true; do
    # Apenas para acompanhamento no log
    echo $(nc -zv ${KAFKA_UI_NET} ${KAFKA_UI_PORT})
    # Tenta estabelecer uma conexão silenciosa com o Kafka UI
    if nc -z ${KAFKA_UI_NET} ${KAFKA_UI_PORT} >/dev/null 2>&1; then
        echo "Kafka UI is accepting connections."
        break
    fi
    if [ $SECONDS -ge $MAX_WAIT ]; then
        echo "Timed out waiting for Kafka UI."
        exit 1
    fi
    sleep 5
    SECONDS=$((SECONDS+5))
done

echo "Starting NGINX."
nginx -g 'daemon off;'
