# Teste inicial de Rede de Co-Movimento com Kafka e Python

Este diretório contém um exemplo de como construir uma rede de co-movimento de ações utilizando Apache Kafka e Python. O produtor recupera dados financeiros através da API Alpha Vantage e os publica em um tópico Kafka, enquanto o consumidor processa esses dados para construir e visualizar uma rede de co-movimento.

## Estrutura do Repositório

- **producer.py**: Script do produtor que busca dados da API Alpha Vantage e os envia para um tópico Kafka.
- **consumer.py**: Script do consumidor que lê dados do tópico Kafka, calcula as correlações entre ações e visualiza uma rede de co-movimento.
- **docker-compose.yaml**: Configuração do Docker Compose para iniciar os serviços Kafka e Zookeeper usando Docker.
- **tickers.json**: Lista de tickers de ações para as quais os dados serão buscados e processados.

## Pré-requisitos

- [Python](https://www.python.org/downloads/)
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- Bibliotecas Python: `confluent_kafka`, `requests`, `pandas`, `matplotlib`, `networkx`. Instale usando:
  ```sh
  pip install confluent_kafka requests pandas matplotlib networkx
  ```

## Configuração

- **API**: É necessário obter uma chave API do Alpha Vantage e inseri-la no script `producer.py`.
- **Kafka**: Configurado para rodar localmente na porta `29092`.
- **Zookeeper**: Configurado para rodar localmente na porta `22181`.

## Como Usar

1. **Inicie o Kafka e o Zookeeper** usando Docker Compose:
   ```sh
   docker-compose up
   ```
   
   Acompanhe o funcionamento do Kafka em sua UI em `localhost:8080`.
   
2. **Execute o Produtor** para buscar dados e enviá-los ao tópico Kafka:
   ```sh
   python producer.py
   ```
   
3. **Execute o Consumidor** para processar os dados e visualizar a rede de co-movimento:
   ```sh
   python consumer.py
   ```
   
4. **Pare o Kafka e o Zookeeper** usando:
   ```sh
   docker-compose down
   ```

### Notas Adicionais
- **Chave API**: Lembre-se de que os usuários precisarão substituir "YOUR_API_KEY" no script `producer.py` pela chave API real obtida do Alpha Vantage.
