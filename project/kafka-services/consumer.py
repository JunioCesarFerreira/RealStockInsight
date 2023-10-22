import json
import uuid
import time
import pandas as pd
import networkx as nx
from cassandra.cluster import Cluster
from confluent_kafka import Consumer, KafkaException

# Carrega as configurações de um arquivo externo
with open('consumer_config.json', 'r') as file:
    conf = json.load(file)

consumer = Consumer(conf)
consumer.subscribe(['stock-prices'])

# DataFrames
data_frames_keys = ['opening_prices', 'closing_prices', 'volumes']
data_frames = {
    'opening_prices': pd.DataFrame(),
    'closing_prices': pd.DataFrame(),
    'volumes': pd.DataFrame()
}

# Grafo
G = nx.Graph()
map_label_id = {}

# Conectando ao cluster do Cassandra (local, por padrão)
cluster = Cluster()
session = cluster.connect()

# Selecionando o keyspace
session.set_keyspace('graph_keyspace')

def insert_data(session, data):
    """Insere os dados em formato JSON no banco de dados Cassandra."""
    timeuuid = uuid.uuid1()
    query = "INSERT INTO graph_table (dummy_partition_key, id, json_data) VALUES (1, %s, %s)"
    session.execute(query, (timeuuid, json.dumps(data)))

def build_edge(G, map, t1, t2, corr, threshold):
    """Constrói ou atualiza uma aresta com base na correlação."""
    if corr > threshold:
        if G.has_edge(map[t1], map[t2]):
            G[map[t1]][map[t2]]['weight'] += 1
        else:
            G.add_edge(map[t1], map[t2], weight=1)
    elif G.has_edge(map[t1], map[t2]):
        G[map[t1]][map[t2]]['weight'] -= 1
        if G[map[t1]][map[t2]]['weight'] <= 0:
            G.remove_edge(map[t1], map[t2])

def building_network(M, G, map_label_id, threshold=0.01):
    """Atualiza ou constrói a rede de co-movimento baseada em uma matriz de correlação."""
    for ticker in M.columns:
        for other_ticker in M.columns:
            if ticker != other_ticker:
                build_edge(G, map_label_id, ticker, other_ticker, M.loc[ticker, other_ticker], threshold)
    return G

def process_message(msg):
    """Processa mensagem do tópico 'stock-prices' do Kafka."""
    msg_json = json.loads(msg.value().decode('utf-8'))
    for i, stock_data in enumerate(msg_json['stocks']):
        ticker = stock_data['ticker']
        G.add_node(i, label=ticker)
        map_label_id[ticker] = i
        for _, stock in enumerate(stock_data['price_data']):
            data_frames['opening_prices'].at[stock["time"], ticker] = stock['open']
            data_frames['closing_prices'].at[stock["time"], ticker] = stock['close']
            data_frames['volumes'].at[stock["time"], ticker] = stock['volume']

try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaException._PARTITION_EOF:
                continue
            else:
                print(f'Error: {msg.error()}')
        else:
            start_time = time.time() # Inicio do processamento
            process_message(msg)
            for key in data_frames_keys:
                clean_data_frame = data_frames[key].dropna()
                correlation_matrix = clean_data_frame.corr(method='pearson')
                building_network(correlation_matrix, G, map_label_id)

            if len(G.nodes) > 0:
                data = {
                    "nodes": [{"id": n, "label": G.nodes[n]["label"]} for n in G.nodes],
                    "links": [{"source": u, "target": v, "weight": w['weight']} for u, v, w in G.edges(data=True)]
                }
                end_time = time.time() # Termino do processamento com construção da rede complexa
                print(f"runtime: {end_time - start_time} s")
                insert_data(session, data)

except KeyboardInterrupt:
    pass

finally:
    # Fecha o consumidor Kafka e a sessão do Cassandra
    consumer.close()
    session.shutdown()
