## Construção da Rede de Co-Movimentos

A construção da rede de co-movimentos envolve vários passos importantes, conforme detalhado abaixo:

1. **Aquisição e Processamento de Dados:**
   Utilizamos o Kafka para consumir dados de preços de ações em tempo real. As mensagens são processadas para extrair os preços de abertura, fechamento e volumes de negociação, que são então armazenados em DataFrames do Pandas.
   
   ```python
   def process_message(msg):
       msg_json = json.loads(msg.value().decode('utf-8'))
       for i, stock_data in enumerate(msg_json['stocks']):
           ticker = stock_data['ticker']
           G.add_node(i, label=ticker)
           map_label_id[ticker] = i
           for _, stock in enumerate(stock_data['price_data']):
               data_frames['opening_prices'].at[stock["time"], ticker] = stock['open']
               data_frames['closing_prices'].at[stock["time"], ticker] = stock['close']
               data_frames['volumes'].at[stock["time"], ticker] = stock['volume']
   ```

2. **Filtragem e Preenchimento de Dados:**
   Após a coleta dos dados, removemos colunas com variação zero e preenchemos valores faltantes com a média da coluna para garantir que a matriz de correlação possa ser calculada corretamente.
   
   ```python
   for key in data_frames_keys:                
       # Remove colunas com variação zero
       data_frames[key] = data_frames[key].loc[:, data_frames[key].var() > 0]
       # Trata valores faltantes, preenchendo com a média
       data_frames[key] = data_frames[key].fillna(data_frames[key].mean())
       clean_data_frame = data_frames[key].dropna()
   ```

3. **Cálculo da Matriz de Correlação:**
   Utilizamos a correlação de Pearson para calcular a matriz de correlação entre as diferentes ações. Esta matriz é usada para identificar as relações de co-movimento entre as ações.
   
   ```python
   correlation_matrix = clean_data_frame.corr(method='pearson')
   print(correlation_matrix)
   ```

4. **Construção da Rede:**
   Construímos a rede de co-movimentos utilizando a matriz de correlação. Adicionamos arestas entre nós (ações) se a correlação entre elas exceder um determinado limiar (threshold). O peso das arestas é ajustado dinamicamente com base na correlação.
   
   ```python
   def build_edge(G, map, t1, t2, corr, threshold):
       if corr > threshold:
           if G.has_edge(map[t1], map[t2]):
               G[map[t1]][map[t2]]['weight'] += 1
           else:
               G.add_edge(map[t1], map[t2], weight=1)
       elif G.has_edge(map[t1], map[t2]):
           G[map[t1]][map[t2]]['weight'] -= 1
           if G[map[t1]][map[t2]]['weight'] <= 0:
               G.remove_edge(map[t1], map[t2])
   ```

5. **Atualização da Rede:**
   A função `building_network` é usada para atualizar ou construir a rede com base na matriz de correlação calculada. Esta função percorre a matriz e ajusta as arestas da rede de acordo com as correlações observadas.
   
   ```python
   def building_network(M, G, map_label_id, threshold=0.001):
       for ticker in M.columns:
           for other_ticker in M.columns:
               if ticker != other_ticker:
                   build_edge(G, map_label_id, ticker, other_ticker, M.loc[ticker, other_ticker], threshold)
       return G
   ```

6. **Armazenamento dos Dados da Rede:**
   Os dados da rede, incluindo nós e arestas, são armazenados em um banco de dados PostgreSQL para análise posterior. Este processo é realizado periodicamente para garantir que a rede esteja sempre atualizada com os dados mais recentes do mercado.
   
   ```python
   def insert_data(cursor, data):
       query = "INSERT INTO COMPLEX_NETWORK_GRAPHS (graph_json) VALUES (%s)"
       cursor.execute(query, (json.dumps(data),))
       conn.commit()
   ```

Este processo garante que nossa rede de co-movimentos seja construída e atualizada continuamente com base nos dados de preços das ações, permitindo uma análise detalhada das relações de co-movimento no mercado de ações.