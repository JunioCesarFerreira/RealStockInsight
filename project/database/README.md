# PostgreSQL Database

This directory contains the files needed to configure and run a PostgreSQL Docker container. The Dockerfile creates an image with Postgres installed and exposes port 5432. The `schema.sql` script is used to create the table used.

## Configuration and Execution

Follow the instructions below to configure and run the project:

### 1. Configure the environment

Make sure you have the following tools and dependencies installed:

- Docker

### 2. Configure and start postgreSQL

In the `postgresql` directory, run the following commands to configure and start Cassandra in a Docker container:

```sh
docker build -t postgres-db .
docker run -d --name postgres-db -p 5432:5432 postgres-db
```