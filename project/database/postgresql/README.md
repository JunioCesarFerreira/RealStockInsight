# PostgreSQL

- **Dockerfile**: Defines the Docker image for PostgreSQL, exposing port 5432 and running PostgreSQL in the foreground.

- **schema.sql**: SQL script of the tables used in the project, being:

- COMPLEX_NETWORK_GRAPHS: Stores complex network of co-movements.

- TRENDS: Stores market trends and the reference price of each ticker.

- TRADERS: Stores investors registered on the network, plus the market liquidity pool (the counterparty of every order).

- ACCOUNTS: Cash of each investor's account on the decentralized market.

- HOLDINGS: Holdings of each account, including the initial position and its price when the account was opened.

- STOCK_EXCHANGES: Stores transactions made on the network as a hash-chained ledger (each record keeps the hash of the previous one).

The monitoring tables (SERVICE_STATUS and SERVICE_EVENTS) are created by the WebAPI on startup.
