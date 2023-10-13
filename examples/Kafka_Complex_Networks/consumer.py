import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from confluent_kafka import Consumer, KafkaException

# Configuração do consumidor
conf = {
    'bootstrap.servers': 'localhost:29092',
    'group.id': 'build-complex-network-consumer',
    'auto.offset.reset': 'earliest',
}

consumer = Consumer(conf)
consumer.subscribe(['stock_prices'])

closing_prices = pd.DataFrame()

G = nx.Graph()

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
            #print(json.dumps(msg_json, indent=4))
            
            timestamp = msg_json['timestamp']
            for stock_data in msg_json['stocks']:
                ticker = stock_data['ticker']
                close_price = stock_data['price_data']['close']
                closing_prices.at[timestamp, ticker] = close_price
            
            #print("closing_prices\n", closing_prices)
            
            # Matriz de correlação de Pearson
            correlation_matrix = closing_prices.corr(method ='pearson')
            
            #print("correlation_matrix\n", correlation_matrix)
            
            # Atualizando a rede de co-movimento
            for ticker in correlation_matrix.columns:
                for other_ticker in correlation_matrix.columns:
                    if ticker != other_ticker:
                        corr = correlation_matrix.loc[ticker, other_ticker]
                        
                        if corr > 0.8:  # Limiar de correlação
                            if G.has_edge(ticker, other_ticker):
                                # Incrementa o peso da aresta existente
                                G[ticker][other_ticker]['weight'] += 1
                            else:
                                # Adiciona uma nova aresta
                                G.add_edge(ticker, other_ticker, weight=1)
                        elif G.has_edge(ticker, other_ticker):
                            # Diminui o peso da aresta existente
                            G[ticker][other_ticker]['weight'] -= 1
                            
                            # Remove a aresta se o peso for <= 0
                            if G[ticker][other_ticker]['weight'] <= 0:
                                G.remove_edge(ticker, other_ticker)
            
            if len(G.nodes) > 0:
                # Visualizando a rede
                plt.figure(figsize=(10, 10))
                pos = nx.spring_layout(G)  
                nx.draw(G, pos, with_labels=True)
                edge_labels = nx.get_edge_attributes(G, 'weight')
                nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
                plt.title('Co-movement Network')
                plt.draw()  
                plt.show()

except KeyboardInterrupt:
    pass

finally:
    consumer.close()
