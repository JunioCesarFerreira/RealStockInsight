# Infraestrutura Docker

Neste diretório temos os seguintes arquivos:

`docker-compose.yaml`: Script de composição da infraestrutura docker a ser provida na VM.

`load.sh`: Script de automação para criar imagens Docker na VM.

### Pré-requisitos
- Docker e Docker Compose

### Modo de usar

Execute o script `load.sh` para gerar as imagens docker.

Em seguida execute `docker-compose up -d` para criar os containers e a rede docker.

Para remover os containers utilize `docker-compose down`.