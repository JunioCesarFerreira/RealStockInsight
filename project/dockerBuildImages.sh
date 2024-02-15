#!/bin/sh

echo ""
echo "* Construindo Imagens Docker"
echo ""

# 1. Prepara imagem do banco de dados
echo "# IMAGEM DO BANCO DE DADOS"
cd database/postgresql
docker build -t rsi-db .
cd ../../

# 2. Prepara imagem da API oficial
echo "# IMAGEM DA API"
cd webapi
docker build -t rsi-api .
cd ..

# 3. Prepara imagem do UI
echo "# IMAGEM DO UI"
cd graph-view
docker build -t rsi-ui .
cd ..

# 4. Prepara imagem do Kafka Consumer para rede complexa
echo "# IMAGEM DO CONSUMIDOR DA REDE COMPLEXA DO KAFKA"
cd kafka-services/consumer-network
docker build -t rsi-consumer-network .
cd ../../

# 5. Prepara imagem do Kafka Consumer para tendências de mercado
echo "# IMAGEM DO CONSUMIDOR DE TENDÊNCIAS DO KAFKA"
cd kafka-services/consumer-trend
docker build -t rsi-consumer-trend .
cd ../../

# 6. Prepara imagem do Kafka Producer
echo "# IMAGEM DO PRODUTOR DO KAFKA"
cd kafka-services/producer
docker build -t rsi-producer .
cd ../..

# 7. Prepara imagem dos bots de simulação
echo "# IMAGEM DOS BOTS DE SIMULAÇÃO"
cd complex-network/simulation
docker build -t rsi-investor-bot .
cd ../../

# 8. Prepara imagem do Nginx
echo "# IMAGEM DO PROXY NGINX"
cd reverse-proxy
docker build -t rsi-nginx-proxy .
cd ..
