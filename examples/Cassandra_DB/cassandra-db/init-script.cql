CREATE KEYSPACE IF NOT EXISTS graph_keyspace WITH REPLICATION = {
    'class' : 'SimpleStrategy', 'replication_factor' : 1
    };

USE graph_keyspace;

CREATE TABLE graph_table (
    dummy_partition_key INT,
    id TIMEUUID,
    json_data TEXT,
    PRIMARY KEY (dummy_partition_key, id)
) WITH CLUSTERING ORDER BY (id DESC);
