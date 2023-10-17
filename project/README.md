# Projeto de Rede de Co-Movimentos Financeiros

## Descrição

Este projeto envolve a construção de uma aplicação distribuída para capturar, processar e visualizar dados financeiros em tempo real, representando-os como uma rede de co-movimentos interativa. Utilizando uma arquitetura baseada em microserviços e ferramentas como Apache Kafka e Cassandra, a aplicação é dividida em várias partes que gerenciam a coleta, o processamento e a visualização dos dados financeiros.

O projeto engloba um produtor que interage com uma API para obter valores de ações, inserindo esses dados em um tópico no Kafka. Posteriormente, um consumidor processa esses dados, convertendo-os em uma rede de co-movimentos que é armazenada no banco de dados. Adicionalmente, uma API é encarregada de disponibilizar esses dados para uma interface de usuário, a qual visualiza a rede de maneira interativa e visual.

### Fluxo do Projeto
1. **Producer (kafka-services/producer.py)**: Utiliza uma API financeira para obter dados de valores de ações em tempo real e os envia a um tópico no Kafka.
2. **Consumer (kafka-services/consumer.py)**: Consome os dados do tópico Kafka, processa-os para construir uma rede de co-movimentos e armazena essa rede no banco de dados Cassandra.
3. **WebAPI (webapi/main.go)**: Uma API escrita em Golang que fornece endpoints para acessar os dados da rede de co-movimentos armazenados no Cassandra.
4. **Graph-View (graph-view)**: Uma interface de usuário construída com React que visualiza a rede de co-movimentos de uma maneira interativa, comunicando-se com a WebAPI para obter os dados necessários.

## Estrutura do Projeto

### 1. `cassandra-db`
- **Dockerfile**: Define a imagem Docker para o Cassandra, expondo a porta 9042 e executando o Cassandra em primeiro plano.
- **init-script.cql**: Script CQL para inicialização do banco de dados, criando e utilizando um keyspace chamado `graph_keyspace`.
- **run-cql-script.sh**: Script shell para executar o script CQL, possivelmente dentro do contêiner Docker.

### 2. `graph-view`
- **src/App.js**: Componente principal que provavelmente gerencia o estado e renderiza a visualização do gráfico.
- **src/components**: Contém os componentes de Graph e GraphControlPanel, que são possivelmente utilizados para controlar e visualizar os dados do gráfico.

### 3. `kafka-services`
- **producer.py**: Script Python que atua como um produtor Kafka, possivelmente buscando dados de ações usando uma API financeira.
- **consumer.py**: Script Python que atua como um consumidor Kafka, processando dados de ações e possivelmente armazenando-os no Cassandra.
- **tickers.json**: Contém uma lista de tickers que são usados para buscar dados da API financeira.

### 4. `webapi`
- **main.go**: Ponto de entrada para a API Go que serve os dados do Cassandra para o front-end React.

## Como Rodar o Projeto

### Pré-requisitos
- Docker e Docker Compose
- Go (para a WebAPI)
- Python (para os serviços Kafka)
- Node.js e NPM (para o front-end React)

### Configuração e Instalação

1. **Configurando o Cassandra**
   - Veja [Exemplo Cassandra DB](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Cassandra_DB)
   - Navegue até o diretório `cassandra-db`.
   - Execute o script `run-cql-script.sh` para inicializar o Cassandra com as configurações necessárias. 
   - (Opcional) Se necessário, ajuste as configurações no `Dockerfile` e no `init-script.cql` conforme suas necessidades.

2. **Configurando e Iniciando os Serviços Kafka**
   - Veja [Examplo Rede Co-movimento com Kafka](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Kafka_Complex_Networks)
   - Navegue até o diretório `kafka-services`.
   - Ajuste os tickers no arquivo `tickers.json` para buscar os dados desejados.
   - Execute os scripts `producer.py` e `consumer.py` para começar a produzir e consumir mensagens. Certifique-se de ter as dependências Python instaladas e o Kafka rodando.

3. **Configurando e Iniciando a WebAPI**
   - Para detalhes de bibliotecas veja [Exemplo API com UI React](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React) e [Exemplo API com Cassandra](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Cassandra_DB)
   - Navegue até o diretório `webapi`.
   - Execute `go run main.go` para iniciar a API. Certifique-se de ter o Go instalado e configurado corretamente.
   - (Opcional) Ajuste as configurações de conexão com o Cassandra no código, se necessário.

4. **Configurando e Iniciando o Front-End React**
   - Mais detalhes de instalação e execução veja [Exemplo Graph UI com D3 no React](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React)
   - Navegue até o diretório `graph-view`.
   - Execute `npm install` para instalar as dependências do projeto.
   - Execute `npm start` para iniciar a aplicação React. Ajuste as configurações de API no código, se necessário.
   
   **Nota**: Certifique-se de que todos os serviços estejam rodando e configurados para se comunicar corretamente entre si. O sistema deve ser inicializado na ordem: Cassandra -> Kafka Services -> WebAPI -> Front-End React para garantir que todos os serviços estejam disponíveis quando necessários.


### Executando o Projeto
Para execução do projeto é necessário estar com os contêiners do Kafka e do Cassandra em execução. Detalhes de como fazer isso são apresentados nos exemplos:
- [Cassandra DB](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Cassandra_DB)
- [Kafka e Complex Networks](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Kafka_Complex_Networks)

Os scripts Python do Producer e Consumer podem ser executados no VS Code.

Utilize o Kafka UI para verificar se houve efeito na execução do Producer e do Consumer.

Utilize o comando `go run main.go` no diretório da API Go para disponibilizar o backend.

Utilize o comando `nmp start` no diretório da UI graph-view para disponibilizar o frontend.

Para mais detalhes de execução consulte os READMEs dos exemplos supracitados.

