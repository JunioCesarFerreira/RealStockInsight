import json
import uuid
from cassandra.cluster import Cluster
import networkx as nx
import random

def insert_data(session, data):
    # Gerando um TimeUUID
    timeuuid = uuid.uuid1()

    # Query de inserção
    query = "INSERT INTO graph_table (dummy_partition_key, id, json_data) VALUES (1, %s, %s)"
    
    # Convertendo o grafo para JSON e executando a query
    session.execute(query, (timeuuid, json.dumps(data)))

def generate_next_graph(G):
    new_node = max(G.nodes) + 1
    G.add_node(new_node)
    
    # Escolhendo um nó existente aleatoriamente para conectar o novo nó
    existing_node = random.choice(list(G.nodes))
    G.add_edge(new_node, existing_node, weight=1)
    
    return G

# Conectando ao cluster do Cassandra (local, por padrão)
cluster = Cluster()
session = cluster.connect()

# Selecionando o keyspace
session.set_keyspace('graph_keyspace')

# Dados de exemplo
data_to_insert = {
    "nodes": [1, 2, 3, 4, 5, 6, 7],
    "links": [
        {"source": 1, "target": 2, "weight": 1},
        {"source": 2, "target": 3, "weight": 1},
        {"source": 3, "target": 1, "weight": 1},
        {"source": 4, "target": 1, "weight": 1},
        {"source": 5, "target": 4, "weight": 1},
        {"source": 5, "target": 6, "weight": 1},
        {"source": 6, "target": 7, "weight": 1},
        {"source": 7, "target": 5, "weight": 1},
    ]
}

# Criando o grafo inicial com networkx
G = nx.Graph()
for node in data_to_insert["nodes"]:
    G.add_node(node)

for link in data_to_insert["links"]:
    G.add_edge(link["source"], link["target"], weight=link["weight"])

# Enviando 10 grafos, cada um adicionando um novo nó e uma nova aresta
for i in range(10):
    print("iteration ", i)
    # Gerando o próximo grafo
    G = generate_next_graph(G)
    
    # Preparando os dados para inserção
    data = {
        "nodes": list(G.nodes),
        "links": [{"source": u, "target": v, "weight": w['weight']} for u, v, w in G.edges(data=True)]
    }

    # Inserindo os dados no Cassandra
    insert_data(session, data)

# Encerrando a conexão com o Cassandra
cluster.shutdown()
