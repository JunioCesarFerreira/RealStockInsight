#!/bin/bash

KAFKA_UI_NET="kafka-ui"
KAFKA_UI_PORT=8080
MAX_WAIT=120
SECONDS=0

echo "Aguardando o Kafka estar pronto para conexões..."

while true; do
    # Apenas para acompanhamento no log
    echo $(nc -zv ${KAFKA_UI_NET} ${KAFKA_UI_PORT})
    # Tenta estabelecer uma conexão silenciosa com o Kafka UI
    if nc -z ${KAFKA_UI_NET} ${KAFKA_UI_PORT} >/dev/null 2>&1; then
        echo "O Kafka está pronto para conexões!"
        break
    fi
    if [ $SECONDS -ge $MAX_WAIT ]; then
        echo "Atingiu o tempo máximo de espera para o Kafka estar pronto."
        exit 1
    fi
    sleep 5
    SECONDS=$((SECONDS+5))
done

echo "Iniciando o NGINX."
nginx -g 'daemon off;'
