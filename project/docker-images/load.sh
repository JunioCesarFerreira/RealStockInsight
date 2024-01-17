#!/bin/bash

echo ""
echo "Automation for testing containers"

# Lista de contêineres a serem gerenciados
containers=(
  "rsi-db"
  "rsi-api"
  "rsi-ui"
  "rsi-consumer-network"
  "rsi-consumer-trend"
  "rsi-producer"
  "rsi-investor-bot"
  "rsi-nginx-proxy"
)

# Passo 1: Remove os contêineres antigos (se existirem)
echo ""
echo "step 1/4 - remove containers"
docker-compose down

# Passo 2: Remove imagens antigas do Docker
echo ""
echo "step 2/4 - remove images"
for container in "${containers[@]}"; do
  docker rmi "$container"
done

# Passo 3: Carrega as imagens Docker
echo ""
echo "step 3/4 - load images"
for container in "${containers[@]}"; do
  docker load -i "${container}.tar"
done

# Passo 4: Instância contêiners e rede Docker
echo ""
echo "step 4/4 - containers up"
docker-compose up -d

echo ""
echo "Finished process!"
echo ""
