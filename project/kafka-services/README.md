# Kafka Services

This directory contains the services related to building the co-movement network that use Apache Kafka.

## Description

- `consumer-network`: Kafka Consumer, consumes the *stock-prices* topic, calculates the correlations of the assets, generates the complex co-movement network and registers its graph in the database.

- `consumer-trend`: Kafka Consumer, consumes the *stock-prices* topic, calculates the trend based on the moving average and registers it in the trends table in the database.

- `producer`: Kafka Producer, accesses the API and produces data in the *stock-prices* topic.

---

## Kafka Topics

- `stock-prices`: Prices obtained via API and consumed to build trends and co-movement network.

- `purchase-and-sale`: Purchases and sales made via API.

---

### Prerequisites
- Docker and Docker Compose
- Python (for Kafka services)

### Running the Project

To run the project, you must have the Kafka and Postgres containers running.

The Producer and Consumer Python scripts can be run in VS Code.

Use the Kafka UI to check if the Producer and Consumer have had any effect.