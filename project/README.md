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
4. **Graph-View (graph-view):** A React-based user interface that visualizes the co-movement network interactively, communicating with the WebAPI to fetch necessary data.

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

### Local Docker Environment

1. **Preparing Docker Images**

   To build all Docker images, use the [`dockerBuildImages.bat`](./dockerBuildImages.bat) script for Windows or [`dockerBuildImages.sh`](./dockerBuildImages.sh) for Linux distributions.

2. **Running the Containers**

   After building the Docker images, navigate to the `docker-images` directory and execute:

```bash
   docker-compose --project-name realstockinsight up -d
```

3. **Removing Containers**

   To remove the containers, use:

```bash
   docker-compose --project-name realstockinsight down
```