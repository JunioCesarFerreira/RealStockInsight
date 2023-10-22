import json
import uuid
import pandas as pd
import networkx as nx
from cassandra.cluster import Cluster
from confluent_kafka import Consumer, KafkaException

# Configuração do consumidor Kafka
conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'build-graph-consumer',
    'auto.offset.reset': 'earliest',
}
consumer = Consumer(conf)
consumer.subscribe(['stock-prices'])

# DataFrames
opening_prices = pd.DataFrame()
closing_prices = pd.DataFrame()
volumes = pd.DataFrame()

data_frames_keys = ['opening_prices', 'closing_prices', 'volumes']
data_frames = {
    'opening_prices': opening_prices,
    'closing_prices': closing_prices,
    'volumes': volumes
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
    """
    Insere os dados em formato JSON no banco de dados Cassandra.

    Args:
        session (cassandra.cluster.Session): Sessão ativa do Cassandra.
        data (dict): Dados em formato de dicionário a serem inseridos no banco.

    """
    # Gerando um TimeUUID
    timeuuid = uuid.uuid1()

    # Query de inserção
    query = "INSERT INTO graph_table (dummy_partition_key, id, json_data) VALUES (1, %s, %s)"
    
    # Convertendo o grafo para JSON e executando a query
    session.execute(query, (timeuuid, json.dumps(data)))

def building_network(M, G, map_label_id, threshold=0.01):
    """
    Atualiza ou constrói a rede de co-movimento baseada em uma matriz de correlação.

    Args:
        M (pd.DataFrame): Matriz de correlações.
        G (nx.Graph): Rede de co-movimento em construção ou atualização.
        map_label_id (dict): Mapeamento entre os rótulos dos 'tickers' e seus IDs no grafo.
        threshold (float, optional): Limiar de correlação para considerar conexão entre nós. Defaults to 0.01.

    Returns:
        nx.Graph: Grafo atualizado.
    """
    # Atualizando a rede de co-movimento
    for ticker in M.columns:
        for other_ticker in M.columns:
            if ticker != other_ticker:
                corr = M.loc[ticker, other_ticker]

                if corr > threshold:  # Limiar de correlação
                    if G.has_edge(map_label_id[ticker], map_label_id[other_ticker]):
                        # Incrementa o peso da aresta existente
                        G[map_label_id[ticker]][map_label_id[other_ticker]]['weight'] += 1
                    else:
                        # Adiciona uma nova aresta
                        G.add_edge(map_label_id[ticker], map_label_id[other_ticker], weight=1)
                elif G.has_edge(map_label_id[ticker], map_label_id[other_ticker]):
                    # Diminui o peso da aresta existente
                    G[map_label_id[ticker]][map_label_id[other_ticker]]['weight'] -= 1
                    
                    # Remove a aresta se o peso for <= 0
                    if G[map_label_id[ticker]][map_label_id[other_ticker]]['weight'] <= 0:
                        G.remove_edge(map_label_id[ticker], map_label_id[other_ticker])

# Processo
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
            msg_json = json.loads(msg.value().decode('utf-8'))
            
            #DEBUG
            print(json.dumps(msg_json, indent=4))
            
            for i, stock_data in enumerate(msg_json['stocks']):
                ticker = stock_data['ticker']
                G.add_node(i, label=ticker)
                map_label_id[ticker] = i
                for _, stock in enumerate(stock_data['price_data']):
                    opening_prices.at[stock["time"], ticker] = stock['open']
                    closing_prices.at[stock["time"], ticker] = stock['close']
                    volumes.at[stock["time"], ticker] = stock['volume']
            
            for key in data_frames_keys:
                print(f"data_frames[{key}]\n", data_frames[key])
            
                # Limpeza do dataframe removendo linhas que contém NaN
                clean_data_frame = data_frames[key].dropna()
                
                # Matriz de correlação de Pearson
                correlation_matrix = clean_data_frame.corr(method ='pearson')
            
                print("correlation_matrix\n", correlation_matrix)
            
                # Atualizando a rede de co-movimento
                building_network(correlation_matrix, G, map_label_id)
            
            if len(G.nodes) > 0:
                # Preparando os dados para inserção
                data = {
                    "nodes": [{"id": n, "label": G.nodes[n]["label"]} for n in G.nodes],
                    "links": [{"source": u, "target": v, "weight": w['weight']} for u, v, w in G.edges(data=True)]
                }
                # Insere os dados no Cassandra
                insert_data(session, data)

except KeyboardInterrupt:
    pass

finally:
    consumer.close()
