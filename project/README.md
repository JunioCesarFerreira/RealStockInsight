# Projeto de Rede de Co-Movimentos Financeiros

## Descrição

Este projeto envolve a construção de uma aplicação distribuída para capturar, processar e visualizar dados financeiros em tempo real, representando-os como uma rede de co-movimentos interativa. Utilizando uma arquitetura baseada em microserviços, a aplicação é dividida em várias partes que gerenciam a coleta, o processamento e a visualização dos dados financeiros.

O projeto engloba um produtor que interage com uma API para obter valores de ações, ou no caso simulado utiliza um banco de dados local com dados históricos do mercado. O Produtor insere os dados em um tópico no Kafka. Posteriormente, um consumidor processa esses dados, convertendo-os em uma rede de co-movimentos que é armazenada no banco de dados. Adicionalmente, uma API é encarregada de disponibilizar esses dados para uma interface de usuário, a qual visualiza a rede de maneira interativa e visual.

A simulação dos investidores é realizada por bots que utilizam diferentes estratégias de investimentos baseadas nas medidas de centralidade de redes complexas.

A análise das simulações é realizada sobre os dados das interações dos bots que ficam registrados no banco de dados.

### Fluxo do Projeto
1. **Producer (kafka-services/producer.py)**: Utiliza uma API financeira para obter dados de valores de ações em tempo real e os envia a um tópico no Kafka.
2. **Consumer (kafka-services/consumer-network.py)**: Consome os dados do tópico Kafka, processa-os para construir uma rede de co-movimentos e armazena essa rede no banco de dados.
2. **Consumer (kafka-services/consumer-trend.py)**: Consome os dados do tópico Kafka, processa-os para construir uma tabela de tendencias que é armazenada banco de dados.
3. **WebAPI (webapi/main.go)**: Uma API escrita em Golang que fornece endpoints para acessar os dados da rede de co-movimentos armazenados no banco de dados.
4. **Graph-View (graph-view)**: Uma interface de usuário construída com React que visualiza a rede de co-movimentos de uma maneira interativa, comunicando-se com a WebAPI para obter os dados necessários.

## Como executar o Projeto em Debug

### Pré-requisitos
- Docker e Docker Compose
- Go (para a WebAPI)
- Python (para os serviços Kafka)
- Node.js e NPM (para o front-end React)

### Configuração e Instalação

1. **Configurando e Iniciando os Serviços Kafka**
   - Veja [Examplo Rede Co-movimento com Kafka](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Kafka_Complex_Networks)
   - Navegue até o diretório `kafka-services`.
   - Ajuste os tickers no arquivo `tickers.json` para buscar os dados desejados.
   - Execute os scripts `producer.py` e `consumer.py` para começar a produzir e consumir mensagens. Certifique-se de ter as dependências Python instaladas e o Kafka rodando.

2. **Configurando e Iniciando a WebAPI**
   - Para detalhes de bibliotecas veja [Exemplo API com UI React](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React) e [Exemplo API com Cassandra](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Cassandra_DB)
   - Navegue até o diretório `webapi`.
   - Execute `go run main.go` para iniciar a API. Certifique-se de ter o Go instalado e configurado corretamente.
   - (Opcional) Ajuste as configurações de conexão com o Cassandra no código, se necessário.

3. **Configurando e Iniciando a UI React**
   - Mais detalhes de instalação e execução veja [Exemplo Graph UI com D3 no React](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React)
   - Navegue até o diretório `graph-view`.
   - Execute `npm install` para instalar as dependências do projeto.
   - Execute `npm start` para iniciar a aplicação React. Ajuste as configurações de API no código, se necessário.
   
4. **Configurando e Iniciando robôs de simulação de investidores**
   - Robôs são definidos no arquivo de configuração `config.json`. Cada robô pode ser configurado para usar diferentes métricas (por exemplo, centralidade de grau, PageRank, centralidade de autovetor) para simular decisões de investimento.
   - O simulador faz uma solicitação à API especificada para obter dados da rede.

   **Nota**: Certifique-se de que todos os serviços estejam rodando e configurados para se comunicar corretamente entre si. O sistema deve ser inicializado na ordem: Cassandra -> Kafka Services -> WebAPI -> Front-End React para garantir que todos os serviços estejam disponíveis quando necessários.


### Ambiente Docker local

1. **Preparando imagens docker**

Para gerar todas as imagens docker utilize o script [`dockerBuildImages.bat`](./dockerBuildImages.bat) para Windows ou [`dockerBuildImages.sh`](./dockerBuildImages.sh) para distribuições Linux. 

2. **Execução dos containers**

Após gerar as imagens docker, no diretório `docker-images` execute:

```bash
docker-compose --project-name realstockinsight up -d
```

Para remover os containers utilize:

```bash
docker-compose --project-name realstockinsight down
```