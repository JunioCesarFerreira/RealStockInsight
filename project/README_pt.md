# Projeto de Rede de Co-Movimentos Financeiros

🌍 *[**Português**](README_pt.md) ∙ [English](README.md)*

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
4. **Graph-View (graph-view)**: Uma interface de usuário construída com React que visualiza a rede de co-movimentos de uma maneira interativa, comunicando-se com a WebAPI para obter os dados necessários. Inclui também o painel de monitoramento de todo o pipeline.

## Início rápido (Docker)

Pré-requisito: Docker com Docker Compose v2.

```bash
cd project
cp .env.example .env          # defina DB_PASSWORD (obrigatória)
docker compose up -d --build
```

Abra **https://localhost:8298/** (ou `https://<ip-da-máquina>:8298/` a partir de outro computador). O certificado é autoassinado, então aceite o aviso do navegador. Para emitir o certificado com o nome correto, defina `CERT_HOST` no `.env` antes do build.

O primeiro build leva alguns minutos. Depois disso, tudo pode ser acompanhado pelo painel: em cerca de um minuto o producer envia a primeira mensagem, os consumers geram a rede e as tendências, e os bots começam a operar cerca de 60s após a API ficar pronta.

### Painel de monitoramento

A página inicial mostra o estado de todo o sistema, atualizado a cada 5s:

- **Pipeline**: producer → Kafka → consumers → PostgreSQL → API → bots, com o status de cada etapa. Quando uma etapa falha, as seguintes normalmente ficam aguardando; corrija primeiro a etapa mais à esquerda.
- **Serviços**: estado e métricas do producer e de cada consumer (mensagens enviadas e consumidas, backlog no Kafka, redes geradas, tempo de processamento etc.).
- **Infraestrutura e dados**: conectividade com PostgreSQL, Kafka e Kafka UI; quantidade e idade das redes e tendências armazenadas.
- **Bots investidores**: estratégia, ciclos executados e decisões (compra, venda, manter) de cada bot.
- **Log de eventos**: eventos recentes de todos os serviços, filtráveis por serviço e nível.

| Status | Significado |
|---|---|
| OK | Executando e reportando normalmente |
| Attention | Iniciando, aguardando dados de uma etapa anterior ou com heartbeats atrasados |
| Error | A última operação falhou (detalhes no log de eventos) |
| Down | Sem heartbeat há algum tempo: o contêiner provavelmente parou ou está reiniciando |

Outros endereços pelo mesmo proxy: visualização da rede em `/graph-view/#/network`, Kafka UI em `/kafka-ui/` e a API em `/api/`.

Para diagnóstico pela linha de comando:

```bash
docker compose ps                  # estado e healthcheck de cada contêiner
docker compose logs -f producer    # ou consumer-net, consumer-trend, investor-bots, api
```

**Como funciona:** cada serviço Python usa o módulo `monitor.py` para enviar heartbeats (a cada 10 a 15s) e eventos à WebAPI (`POST /monitor/heartbeat` e `POST /monitor/event`). A WebAPI grava esses dados no PostgreSQL (tabelas `SERVICE_STATUS` e `SERVICE_EVENTS`) e os expõe em `GET /monitor/status` e `GET /monitor/events`. O proxy reverso aceita apenas leitura nesses endpoints a partir de fora do Docker.

**Duração da simulação:** os dados históricos do producer (`database.db`) rendem cerca de 6.700 mensagens, uma a cada 60s (aproximadamente 4,7 dias). Ao esgotá-los, o producer fica no estado `idle`. Para reiniciar a simulação: `docker compose up -d --force-recreate producer`.

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

   **Variáveis de ambiente em debug:**
   - `DB_PASSWORD`: senha do PostgreSQL, usada pela WebAPI e pelos consumers.
   - `MONITOR_API_URL=http://localhost:5002`: para que os serviços Python reportem ao painel (o padrão `http://api:5002` só resolve dentro do Docker). Use `MONITOR_DISABLED=1` para desativar o envio.
   - `REACT_APP_API_BASE=http://localhost:5002`: URL da WebAPI usada pela UI em `npm start`.


### Ambiente Docker local

Toda a stack está descrita em um único [`docker-compose.yaml`](./docker-compose.yaml) que constrói cada imagem diretamente a partir do código-fonte. Não são necessários scripts de build separados.

1. **Construindo as imagens**

   No diretório `project`, crie o arquivo `.env` a partir de [`.env.example`](./.env.example) (a variável `DB_PASSWORD` é obrigatória) e construa todas as imagens com:

```bash
   docker compose build
```

2. **Execução dos containers**

   Suba toda a stack (as imagens são construídas automaticamente se não existirem):

```bash
   docker compose -p realstockinsight up -d
```

   Para forçar a reconstrução antes de subir, adicione `--build`:

```bash
   docker compose -p realstockinsight up -d --build
```

3. **Removendo containers**

   Para remover os containers e a rede Docker:

```bash
   docker compose -p realstockinsight down
```