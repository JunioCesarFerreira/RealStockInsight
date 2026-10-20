# Financial Co-Movement Network Project

🌍 *[Português](README_pt.md) ∙ [**English**](README.md)*

## Description

This project involves building a distributed application to capture, process, and visualize real-time financial data, representing it as an interactive co-movement network. Using a microservices-based architecture, the application is divided into various components that manage the collection, processing, and visualization of financial data.

The project includes a producer that interacts with an API to fetch stock values or, in a simulated case, uses a local database with historical market data. The producer sends the data to a Kafka topic. Subsequently, a consumer processes this data, converting it into a co-movement network that is stored in a database. Additionally, an API serves these data to a user interface, which visualizes the network interactively.

Investor simulation is carried out by bots using different investment strategies based on complex network centrality measures.

The simulation analysis is performed on the bot interaction data stored in the database.

### Project Workflow
1. **Producer (kafka-services/producer.py):** Uses a financial API to fetch real-time stock data and sends it to a Kafka topic.
2. **Consumer (kafka-services/consumer-network.py):** Consumes data from the Kafka topic, processes it to construct a co-movement network, and stores this network in the database.
2. **Consumer (kafka-services/consumer-trend.py):** Consumes data from the Kafka topic, processes it to construct a trends table, and stores it in the database.
3. **WebAPI (webapi/main.go):** A Go-based API that provides endpoints to access the co-movement network data stored in the database.
4. **Graph-View (graph-view):** A React-based user interface that visualizes the co-movement network interactively, communicating with the WebAPI to fetch necessary data. It also hosts the monitoring dashboard for the whole pipeline.

## Quick Start (Docker)

Prerequisite: Docker with Docker Compose v2.

```bash
cd project
cp .env.example .env          # set DB_PASSWORD (required)
docker compose up -d --build
```

Open **https://localhost:8298/** (or `https://<machine-ip>:8298/` from another computer). The certificate is self-signed, so accept the browser warning. To issue the certificate for the right name, set `CERT_HOST` in `.env` before building.

The first build takes a few minutes. After that, everything can be followed on the dashboard: within about a minute the producer sends its first message, the consumers build the network and the trends, and the bots start trading about 60s after the API is ready.

### Monitoring Dashboard

The home page shows the state of the whole system, refreshed every 5s:

- **Pipeline**: producer → Kafka → consumers → PostgreSQL → API → bots, with the status of each step. When a step fails, the following ones usually wait for it; fix the leftmost one first.
- **Services**: state and metrics of the producer and of each consumer (messages sent and consumed, Kafka backlog, networks built, processing time, etc.).
- **Infrastructure & data**: connectivity to PostgreSQL, Kafka and Kafka UI; count and age of the stored networks and trends.
- **Investor bots**: strategy, cycles run and decisions (buy, sell, hold) of each bot.
- **Event log**: recent events from every service, filterable by service and level.

| Status | Meaning |
|---|---|
| OK | Running and reporting normally |
| Attention | Starting, waiting for upstream data, or heartbeats are late |
| Error | The last operation failed (details in the event log) |
| Down | No heartbeat for a while: the container is probably stopped or restarting |

Other addresses behind the same proxy: the network view at `/#/network`, Kafka UI at `/kafka-ui/` and the API at `/api/`.

For command-line diagnostics:

```bash
docker compose ps                  # state and healthcheck of each container
docker compose logs -f producer    # or consumer-net, consumer-trend, investor-bots, api
```

**How it works:** each Python service uses the `monitor.py` module to send heartbeats (every 10 to 15s) and events to the WebAPI (`POST /monitor/heartbeat` and `POST /monitor/event`). The WebAPI stores them in PostgreSQL (tables `SERVICE_STATUS` and `SERVICE_EVENTS`) and serves them at `GET /monitor/status` and `GET /monitor/events`. The reverse proxy only allows reads on these endpoints from outside Docker.

**Simulation length:** the producer's historical data (`database.db`) yields about 6,700 messages, one every 60s (roughly 4.7 days). Once exhausted, the producer stays in the `idle` state. To restart the whole simulation (prices, networks, accounts and ledger): `docker compose down && docker compose up -d`.

### Decentralized Market

As proposed in the paper *An automated decision-making system employing complex networks and blockchain for the decentralized stock market* (Garcia et al., Expert Systems with Applications, 2024), decisions come from the complex network (centrality measures and trend), while assets are exchanged on a decentralized market. Here the market is simulated by the WebAPI:

- **Accounts:** each bot opens an account with its initial endowment (`initialMoney` in `config.json` and `initial_assets.json`). Cash and holdings are kept by the market, which is the source of truth, not by the bot.
- **Orders:** buy and sell orders are validated and settled atomically at the latest reference price of the ticker (the last price of the feed). The counterparty is the market liquidity pool, as in oracle-priced decentralized exchanges. Orders without enough cash or holdings are rejected (HTTP 422).
- **Ledger:** every trade is appended to `STOCK_EXCHANGES` with the hash of the previous record (SHA-256 chain), so changing, removing or reordering any past trade is detected by `GET /market/ledger/verify`. This reproduces, on a single node, the transparency and immutability role of the blockchain in the paper; it is not a distributed blockchain.
- **Strategy:** unchanged. A buy decision buys 15% of the available cash in the ticker and a sell decision sells the whole position, as in the original bots. The bots' SQLite log (`bot_log.db`) is still written, so `complex-network/results-analysis/analysis.py` keeps working.
- **Evaluation:** the **Market** tab shows, for each bot, cash, stocks value, net worth, the result since the account was opened and the comparison with buy & hold, plus the recent trades and the ledger verification.

| Endpoint | Description |
|---|---|
| `POST /market/accounts` | Opens an account `{trader_id, initial_cash, initial_holdings}` (idempotent) |
| `GET /market/accounts` | Accounts valued at the latest prices |
| `GET /market/accounts/{trader_id}` | One account, including its holdings |
| `POST /stocks/buy`, `POST /stocks/sell` | Orders `{trader_id, ticker, amount}` |
| `GET /market/trades` | Latest trades (`limit`, `trader_id`) |
| `GET /market/ledger` | Ledger summary (records, volume, head hash) |
| `GET /market/ledger/verify` | Recomputes the whole hash chain |

Through the public proxy only reads are allowed on `/api/market/`; orders and account opening are accepted only from the Docker internal network.

## How to Run the Project in Debug Mode

### Prerequisites
- Docker and Docker Compose
- Go (for the WebAPI)
- Python (for the Kafka services)
- Node.js and NPM (for the React front-end)

### Setup and Installation

1. **Setting Up and Starting Kafka Services**
   - See [Example Co-Movement Network with Kafka](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Kafka_Complex_Networks)
   - Navigate to the `kafka-services` directory.
   - Adjust the tickers in the `tickers.json` file to fetch the desired data.
   - Run the `producer.py` and `consumer.py` scripts to start producing and consuming messages. Ensure that Python dependencies are installed and Kafka is running.

2. **Setting Up and Starting the WebAPI**
   - For library details, see [Example API with React UI](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React) and [Example API with Cassandra](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Cassandra_DB).
   - Navigate to the `webapi` directory.
   - Run `go run main.go` to start the API. Ensure that Go is installed and configured correctly.
   - (Optional) Adjust Cassandra connection settings in the code, if necessary.

3. **Setting Up and Starting the React UI**
   - For more installation and execution details, see [Example Graph UI with D3 in React](https://github.com/JunioCesarFerreira/RealStockInsight/tree/main/examples/Graph_React).
   - Navigate to the `graph-view` directory.
   - Run `npm install` to install project dependencies.
   - Run `npm start` to start the React application. Adjust the API configurations in the code, if necessary.

4. **Setting Up and Running Investor Simulation Bots**
   - Bots are defined in the `config.json` configuration file. Each bot can be configured to use different metrics (e.g., degree centrality, PageRank, eigenvector centrality) to simulate investment decisions.
   - The simulator makes API requests to fetch network data.

   **Note:** Ensure all services are running and properly configured to communicate with each other. The system should be initialized in the following order: Cassandra -> Kafka Services -> WebAPI -> React Front-End to ensure all services are available when needed.

   **Environment variables in debug mode:**
   - `DB_PASSWORD`: PostgreSQL password, used by the WebAPI and the consumers.
   - `MONITOR_API_URL=http://localhost:5002`: lets the Python services report to the dashboard (the default `http://api:5002` only resolves inside Docker). Set `MONITOR_DISABLED=1` to turn reporting off.
   - `REACT_APP_API_BASE=http://localhost:5002`: WebAPI URL used by the UI under `npm start`.

### Local Docker Environment

The entire stack is described in a single [`docker-compose.yaml`](./docker-compose.yaml) that builds every image directly from its source. No separate build scripts are needed.

1. **Building the Images**

   From the `project` directory, create the `.env` file from [`.env.example`](./.env.example) (`DB_PASSWORD` is required) and build all images with:

```bash
   docker compose build
```

2. **Running the Containers**

   Start the whole stack (images are built automatically if missing):

```bash
   docker compose -p realstockinsight up -d
```

   To force a rebuild before starting, add `--build`:

```bash
   docker compose -p realstockinsight up -d --build
```

3. **Removing Containers**

   To remove the containers and the Docker network:

```bash
   docker compose -p realstockinsight down
```