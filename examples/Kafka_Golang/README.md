# Kafka & Golang Example

Este diretório contém exemplos básicos para criar um produtor e um consumidor usando Apache Kafka e Golang. Ele também inclui um `docker-compose.yaml` para facilitar a configuração e execução de instâncias locais do Kafka e Zookeeper usando Docker.

## Estrutura do diretório

- **Consumer**: Contém o código-fonte para um consumidor Kafka básico escrito em Golang.
- **Producer**: Contém o código-fonte para um produtor Kafka básico escrito em Golang.
- **docker-compose.yaml**: Arquivo de configuração do Docker Compose para rodar o Kafka e o Zookeeper localmente usando Docker.

## Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Golang](https://golang.org/doc/install)
- Um editor de código ou IDE de sua escolha.

## Como Usar

### Iniciar o Kafka e o Zookeeper

Para iniciar o Kafka e o Zookeeper usando Docker, execute o seguinte comando no diretório raiz do projeto:

```sh
docker-compose up
```

### Executar o Produtor e o Consumidor

Navegue até os diretórios `Producer` e `Consumer`, e execute os seguintes comandos em duas janelas de terminal separadas:

Para o produtor:
```sh
cd Producer
go run main.go
```

Para o consumidor:
```sh
cd Consumer
go run main.go
```

O produtor enviará mensagens para o tópico Kafka, e o consumidor receberá e imprimirá essas mensagens no console.

### Parar o Kafka e o Zookeeper

Para parar o Kafka e o Zookeeper, pressione `Ctrl+C` no terminal onde o Docker Compose está sendo executado. Para remover os contêineres, execute:

```sh
docker-compose down
```

## Configuração

- **Kafka**: Configurado para rodar localmente na porta `29092`. Pode ser acessado de fora do Docker na mesma porta.
- **Zookeeper**: Configurado para rodar localmente na porta `22181`.

Ambos os serviços podem ser ajustados modificando o arquivo `docker-compose.yaml`.
