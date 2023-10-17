#!/bin/bash

CQL_PATH="./init-script.cql"

CASSANDRA_CONTAINER="cassandra-db"

docker cp ${CQL_PATH} ${CASSANDRA_CONTAINER}:/init-script.cql

docker exec -it ${CASSANDRA_CONTAINER} cqlsh -f /init-script.cql
