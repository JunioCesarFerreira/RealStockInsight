import os
import requests
import json
import time
import math
import sqlite3
import networkx as nx
from queue import Queue
from threading import Thread

API_GRAPH_ENDPOINT = "http://localhost:5002/api/graph"
API_TREND_ENDPOINT = "http://localhost:5002/api/trend"

# Classe Robô Investidor
class Bot:
    def __init__(self, id, name, initial_money, initial_assets={}):
        self.id = id
        self.name = name
        self.money = initial_money
        self.assets = initial_assets


def create_table_repository():
    """Cria o banco de dados de log"""
    conn = sqlite3.connect("bot_log.db")

    conn.execute('''
        CREATE TABLE IF NOT EXISTS log_table (
            bot_name TEXT,
            bot_id TEXT,
            ticker TEXT,
            time_stamp TEXT,
            metric_value REAL,
            action TEXT,
            available_resources REAL,
            assets TEXT)
        ''')
    
    conn.execute("DELETE FROM log_table")

    conn.close()
  
def insert_log_repository(bot_name, bot_id, ticker, metric_value, action, available_resources, assets):
    """Insere dados no log

    Args:
        bot_name (text):  Nome do bot
        bot_id (text): Id do bot
        ticker (text): Ticker em escopo
        metric_value (real): Valor da métrica utilizada
        action (text): Ação que o bot realizou
        available_resources (real): Quantidade de recursos do bot
    """
    conn = sqlite3.connect("bot_log.db")

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    conn.execute("INSERT INTO log_table VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                 (bot_name, bot_id, ticker, timestamp, metric_value, action, available_resources, assets))
    
    conn.commit()
    
    conn.close()

def request_graph():
    """Realiza request na API e monta um objeto networkx.Graph.

    Returns:
        networkx.Graph: Rede de co-movimentos do mercado.
    """
    headers = {
        'accept': 'application/json'
    }
    print("request:", API_GRAPH_ENDPOINT)
    # Realiza o request à API para obter rede complexa atualizada
    response = requests.get(API_GRAPH_ENDPOINT, headers=headers)
    data = json.loads(response.text)
    
    print("response.json.length:", len(data))

    # Verifica se a resposta da API está em um formato adequado
    if not data or "nodes" not in data or "links" not in data:
        print("Resposta da API inválida!")
        exit(1)

    G = nx.Graph()

    # Adiciona os vértices à rede complexa atualizada
    for vertex in data["nodes"]:
        G.add_node(vertex["id"], label=vertex["label"])

    # Adiciona as arestas ao gráfico
    for edge in data["links"]:
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
    return G


def request_trend():
    """Obtém tendências e preços da API e retorna como um dicionário."""
    print("request:", API_TREND_ENDPOINT)
    headers = {
        'accept': 'application/json'
    }
    response = requests.get(API_TREND_ENDPOINT, headers=headers)
    
    if response.status_code != 200:
        print(f"Erro ao acessar a API. Código de status: {response.status_code}")
        return {}
    
    trends_list = response.json()
    
    print("response.length:", len(trends_list))
    
    trends_dict = {
        item['ticker']: {
            "trend": item['trend'],
            "price": item['price']
            } for item in trends_list}
    
    return trends_dict

def run_robot(bot, parameters, G, trends):
    """Executa o robô para simular a tomada de decisão dos investidores.

    Args:
        bot (object): Atributos do robô.
        parameters (dict): Parâmetros para métricas específicas.
        G (networkx.Graph): Grafo representando a rede de co-movimentos.

    """
    metrics = {}

    # Calcula as métricas de acordo com os parâmetros fornecidos
    if parameters["degreeCentrality"]["enable"]:
        metrics["degreeCentrality"] = nx.degree_centrality(G)
        
    if parameters["pagerank"]["enable"]:
        metrics["pagerank"] = nx.pagerank(G)
        
    if parameters["closenessCentrality"]["enable"]:
        metrics["closenessCentrality"] = nx.closeness_centrality(G)
        
    if parameters["betweennessCentrality"]["enable"]:
        metrics["betweennessCentrality"] = nx.betweenness_centrality(G)    
        
    if parameters["eigenvectorCentrality"]["enable"]:
        metrics["eigenvectorCentrality"] = nx.eigenvector_centrality(G)
         
    for asset, data in G.nodes(data=True):
        ticker = data['label']
        trend = trends[ticker]["trend"] 
        price = trends[ticker]["price"]
        acc_metric_value = 0
        acc_threshold = 0
        counter = 0
        
        for metric_name, metric_values in metrics.items():
            acc_metric_value += metric_values[asset]
            acc_threshold += parameters[metric_name]["threshold"]
            counter += 1
            
        if counter > 0:
            metric_value = acc_metric_value / counter
            threshold = acc_threshold / counter
            
            action = investment_strategy(metric_value, threshold, trend=trend)
            
            if action == "buy":
                if bot.money > price:
                    # Compra porcentagem fixa! Pensar em estratégias mais dinâmicas!
                    value = (bot.money / price) * 0.15
                    amount = math.floor(value)
                    if amount==0:
                        amount = 1
                    #bot.buy_active(ticker, amount, price)
                    
            elif action == "sell":
                # Vende tudo! Pensar em estratégias mais dinâmicas!
                if ticker not in bot.assets:
                    print('O bot não tem ativo para vender.')
                else:
                    amount = bot.assets[ticker]
                    #bot.sell_active(ticker, amount, price)
            
            assets_txt = json.dumps(bot.assets)
            insert_log_repository(bot.name, bot.id, ticker, metric_value, action, bot.money, assets_txt)
        else:
            print(f"Nenhuma métrica foi selecionada para o bot {bot.name}")


def investment_strategy(p, t, trend=None):
    """
    Define a estratégia de investimento com base na métrica, no limite e na tendência atual.
    
    Args:
        p (float): Valor da métrica.
        t (float): Valor do limite (threshold).
        trend (str, optional): Tendência atual, pode ser 'up', 'down' ou None.

    Returns:
        str: Retorna "buy" se p > t e a tendência é ascendente, "sell" se p < t e a tendência é descendente,
             ou "hold" caso contrário.
    """
    if p > t and (trend is None or trend == 'up'):
        return "buy"
    elif p < t and (trend is None or trend == 'down'):
        return "sell"
    else:
        return "hold"
   

def thread_run_robot(robot, queue):
    """Função de thread para executar um robô."""
    print(f"bot:{robot['name']}")
    
    with open('initial_assets.json', 'r') as file:
        initial_assets = json.load(file)
    
    bot = Bot(robot["id"], robot["name"], robot["initialMoney"], initial_assets=initial_assets)
    
    while True:
        # Verifica se a thread deve ser encerrada
        if queue.empty():
            break
    
        G = request_graph()  # Solicita o grafo da API
        trends = request_trend() # Solicita tendências da API
        
        run_robot(bot, robot["parameters"][0], G, trends)
        
        time.sleep(robot["interval"])


# MAIN
if __name__=="__main__":
    print("starting investor bots...")

    is_debug = os.getenv('PROD') == None

    if is_debug:
        print("is debug")
    else:
        print("not is debug")
        
    create_table_repository()
        
    # Lê o arquivo de configuração que contém informações sobre os robôs
    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            if is_debug == False:
                apiEndpoints = config["apiEndpoints"]
                API_GRAPH_ENDPOINT = apiEndpoints["graph"]
                API_TREND_ENDPOINT = apiEndpoints["trend"]
    except Exception as e:
        print(f"Falha ao ler configurações: {e}")
        exit(1)

    # Atraso na inicialização
    print("waiting...")
    if is_debug == False:
        time.sleep(60) # Espera um minuto para garantir que outras partes já estejam em execução.

    # Inicializa a fila e as threads
    queue = Queue()
    threads = []

    # Adiciona um item na fila para cada robô
    for _ in config["robots"]:
        queue.put(None)
        
    print("starting bots...")

    # Cria e inicia as threads
    for robot in config["robots"]:
        t = Thread(target=thread_run_robot, args=(robot, queue))
        threads.append(t)
        t.start()

    # Aguarda a finalização das threads
    for t in threads:
        t.join()

    print("finishing threads...")
    # Finaliza as threads
    for _ in range(len(threads)):
        queue.put(None)

    for t in threads:
        t.join()
