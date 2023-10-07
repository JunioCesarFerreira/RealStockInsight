# Kafka & C# Example

Este diretório fornece exemplos básicos de como implementar um produtor e um consumidor usando Apache Kafka e C#. Ele também inclui um arquivo `docker-compose.yaml` para subir facilmente instâncias locais do Kafka e do Zookeeper usando o Docker.

## Estrutura do diretório

- **Producer**: Contém o código-fonte para um produtor Kafka básico escrito em C#.
- **Consumer**: Contém o código-fonte para um consumidor Kafka básico escrito em C#.
- **docker-compose.yaml**: Arquivo de configuração do Docker Compose para iniciar os serviços Kafka e Zookeeper usando o Docker.

## Pré-requisitos

- [.NET SDK](https://dotnet.microsoft.com/download)
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Visual Studio Code](https://code.visualstudio.com/download) ou [Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

## Como Usar

### Iniciar o Kafka e o Zookeeper

Para iniciar o Kafka e o Zookeeper usando o Docker, você pode usar o seguinte comando no diretório raiz do projeto:

```sh
docker-compose up
```

### Compilar e Executar o Produtor e o Consumidor

Para compilar e executar o código, você pode utilizar a CLI do .NET ou um IDE de sua escolha (como Visual Studio ou Visual Studio Code). No terminal, navegue até os diretórios `Producer` ou `Consumer` e execute os seguintes comandos:

- **Para o Produtor:**
  ```sh
  cd Producer
  dotnet restore
  dotnet run
  ```
  
- **Para o Consumidor:**
  ```sh
  cd Consumer
  dotnet restore
  dotnet run
  ```

### Parar o Kafka e o Zookeeper

Para parar o Kafka e o Zookeeper, você pode pressionar `Ctrl+C` no terminal onde o Docker Compose está sendo executado. Para parar e remover os contêineres, você pode usar:

```sh
docker-compose down
```

## Configuração

- **Kafka**: Configurado para rodar localmente na porta `29092`. Pode ser acessado de fora do Docker na mesma porta.
- **Zookeeper**: Configurado para rodar localmente na porta `22181`.
