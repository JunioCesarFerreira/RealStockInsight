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
consumer.subscribe(['stock_prices'])

# DataFrame de preços
closing_prices = pd.DataFrame()

# Grafo
G = nx.Graph()

# Conectando ao cluster do Cassandra (local, por padrão)
cluster = Cluster()
session = cluster.connect()

# Selecionando o keyspace
session.set_keyspace('graph_keyspace')

# Método de inserção de dados ao banco
def insert_data(session, data):
    # Gerando um TimeUUID
    timeuuid = uuid.uuid1()

    # Query de inserção
    query = "INSERT INTO graph_table (dummy_partition_key, id, json_data) VALUES (1, %s, %s)"
    
    # Convertendo o grafo para JSON e executando a query
    session.execute(query, (timeuuid, json.dumps(data)))

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
            
            timestamp = msg_json['timestamp']
            labelId = {}
            for i, stock_data in enumerate(msg_json['stocks']):
                ticker = stock_data['ticker']
                close_price = stock_data['price_data']['close']
                closing_prices.at[timestamp, ticker] = close_price
                G.add_node(i, label=ticker)
                labelId[ticker] = i
            
            print("closing_prices\n", closing_prices)
            
            # Matriz de correlação de Pearson
            correlation_matrix = closing_prices.corr(method ='pearson')
            
            print("correlation_matrix\n", correlation_matrix)
            
            # Atualizando a rede de co-movimento
            for ticker in correlation_matrix.columns:
                for other_ticker in correlation_matrix.columns:
                    if ticker != other_ticker:
                        corr = correlation_matrix.loc[ticker, other_ticker]
                        
                        if corr > 0.8:  # Limiar de correlação
                            if G.has_edge(labelId[ticker], labelId[other_ticker]):
                                # Incrementa o peso da aresta existente
                                G[labelId[ticker]][labelId[other_ticker]]['weight'] += 1
                            else:
                                # Adiciona uma nova aresta
                                G.add_edge(labelId[ticker], labelId[other_ticker], weight=1)
                        elif G.has_edge(labelId[ticker], labelId[other_ticker]):
                            # Diminui o peso da aresta existente
                            G[labelId[ticker]][labelId[other_ticker]]['weight'] -= 1
                            
                            # Remove a aresta se o peso for <= 0
                            if G[labelId[ticker]][labelId[other_ticker]]['weight'] <= 0:
                                G.remove_edge(labelId[ticker], labelId[other_ticker])
            
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
