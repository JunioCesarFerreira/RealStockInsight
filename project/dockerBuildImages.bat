@echo off

echo.
echo * Build Docker Images
echo.

REM 1. Prepara imagem de banco de dados
echo # DATABASE IMAGE
cd database\postgresql
docker build -t rsi-db .
cd ..\..

REM 2. Prepara imagem da API oficial
echo # API IMAGE
cd webapi
docker build -t rsi-api .
cd ..

REM 3. Prepara imagem do UI
echo # GRAPH VIEW UI IMAGE
cd graph-view
docker build -t rsi-ui .
cd ..

REM 4. Prepara imagem do Kafka Consumer complex network
echo # COMPLEX NETWORK CONSUMER IMAGE
cd kafka-services\consumer-network
docker build -t rsi-consumer-network .
cd ..\..

REM 5. Prepara imagem do Kafka Consumer market trend
echo # TREND CONSUMER IMAGE
cd kafka-services\consumer-trend
docker build -t rsi-consumer-trend .
cd ..\..

REM 6. Prepara imagem do Kafka Producer
echo # KAFKA PRODUCER IMAGE
cd kafka-services\producer
docker build -t rsi-producer .
cd ..\..

REM 7. Prepara imagem dos bots de simulação
echo # BOTS SIMULATION IMAGE
cd complex-network\simulation
docker build -t rsi-investor-bot .
cd ..\..

REM 8. Prepara imagem dos Nginx
echo # NGINX PROXY IMAGE
cd reverse-proxy
docker build -t rsi-nginx-proxy .
cd ..

pause