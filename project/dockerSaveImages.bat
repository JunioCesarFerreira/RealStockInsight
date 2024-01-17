@echo off

echo.
echo * Save Docker Images
echo.

REM Gerando arquivos de imagens

if not exist "docker-images" (
    mkdir "docker-images"
)
echo.
echo * Saving image files. Please wait...
echo.

cd docker-images

echo 1/8 saving rsi-db
docker save rsi-db -o rsi-db.tar

echo 2/8 saving rsi-api
docker save rsi-api -o rsi-api.tar

echo 3/8 save rsi-ui
docker save rsi-ui -o rsi-ui.tar

echo 4/8 saving rsi-consumer-network
docker save rsi-consumer-network -o rsi-consumer-network.tar

echo 5/8 saving rsi-consumer-trend
docker save rsi-consumer-trend -o rsi-consumer-trend.tar

echo 6/8 saving rsi-producer
docker save rsi-producer -o rsi-producer.tar

echo 7/8 saving rsi-investor-bot
docker save rsi-investor-bot -o rsi-investor-bot.tar

echo 8/8 saving rsi-nginx-proxy 
docker save rsi-nginx-proxy -o rsi-nginx-proxy.tar

echo.
echo Finished process!
echo.

pause