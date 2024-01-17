# Serviços Kafka

Este diretório contém os serviços relacionadas à construção da rede de co-movimentos que utilizam o Apache Kafka.

## Descrição

- `consumer-network`: Consumer Kafka, consome o tópico *stock-prices* calcula as correlações dos ativos, gera a rede complexa de co-movimentos e registra seu grafo no banco de dados.

- `consumer-trend`: Consumer Kafka, consome o tópico *stock-prices* calcula tendência com base na média móvel e registra na tabela de tendências no banco de dados.

- `producer`: Producer Kafka, acessa a API e produz dados no tópico *stock-prices*.

---
	
## Tópicos Kafka

- `stock-prices`: Preços obtidos via API e consumidos para construção de tendênicas e rede de co-movimentos.

- `purchase-and-sale`: Compras e vendas realizadas via API.

---
   
### Pré-requisitos
- Docker e Docker Compose
- Python (para os serviços Kafka)

### Executando o Projeto

Para execução do projeto é necessário estar com os contêiners do Kafka e do Postgres em execução.

Os scripts Python do Producer e Consumer podem ser executados no VS Code.

Utilize o Kafka UI para verificar se houve efeito na execução do Producer e do Consumer.
