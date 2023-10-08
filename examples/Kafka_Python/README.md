# Kafka & Python Example

Este diretório contém exemplos básicos de um produtor e consumidor utilizando Apache Kafka e Python. Ele também inclui um `docker-compose.yaml` para facilitar a configuração e execução do Kafka e Zookeeper localmente usando Docker.

## Estrutura do diretório

- **producer.py**: Contém o código-fonte para um produtor Kafka básico escrito em Python.
- **consumer.py**: Contém o código-fonte para um consumidor Kafka básico escrito em Python.
- **docker-compose.yaml**: Arquivo de configuração do Docker Compose para iniciar os serviços Kafka e Zookeeper usando Docker.

## Pré-requisitos

- [Python](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- Bibliotecas Python: `confluent_kafka`. Você pode instalá-las usando pip:
  ```sh
  pip install confluent_kafka
  ```

## Como Usar

### Iniciar o Kafka e o Zookeeper

Para subir os serviços do Kafka e Zookeeper utilizando Docker, execute o seguinte comando no diretório raiz do projeto:

```sh
docker-compose up
```

### Executar o Produtor e o Consumidor

Navegue até o diretório do projeto e utilize os seguintes comandos para executar o produtor e o consumidor:

- **Produtor:**
  ```sh
  python producer.py
  ```
  
- **Consumidor:**
  ```sh
  python consumer.py
  ```
  
### Parar o Kafka e o Zookeeper

Para parar o Kafka e o Zookeeper, você pode pressionar `Ctrl+C` no terminal onde o Docker Compose está sendo executado. Para parar e remover os contêineres, você pode utilizar:

```sh
docker-compose down
```

## Configuração

- **Kafka**: Configurado para rodar localmente na porta `29092`. Pode ser acessado de fora do Docker na mesma porta.
- **Zookeeper**: Configurado para rodar localmente na porta `22181`.
