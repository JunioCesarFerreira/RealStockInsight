import requests
import networkx as nx
import json

API_ENDPOINT = "http://localhost:5002/graph"

# Lê o arquivo de configuração
with open('config.json', 'r') as file:
    config = json.load(file)

def request_graph():
    """Realiza request na api e monta networkx.Graph

    Returns:
        networkx.Graph: Rede de co-movimentos do mercado
    """
    # Realiza o request à API
    response = requests.get(API_ENDPOINT)
    data = response.json()

    # Verifica se a resposta da API está em um formato adequado
    if not data or "graph" not in data:
        print("Resposta da API inválida!")
        exit()

    G = nx.Graph()

    # Adicione os vértices ao gráfico
    for vertex in data["graph"]["vertices"]:
        G.add_node(vertex["id"], label=vertex["label"])

    # Adicione as arestas ao gráfico
    for edge in data["graph"]["edges"]:
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
    return G

def calc_local_metrics(G):
    # Calcula as métricas locais da rede
    degree_centrality = nx.degree_centrality(G)
    pagerank_centrality = nx.pagerank(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)
    return degree_centrality, pagerank_centrality, eigenvector_centrality

def run_robot(robot_name, parameters, G):
    metrics = {}
    if parameters["degreeCentrality"]["enable"]:
        metrics["degreeCentrality"] = nx.degree_centrality(G)

    if parameters["pagerank"]["enable"]:
        metrics["pagerank"] = nx.pagerank(G)

    if parameters["eigenvectorCentrality"]["enable"]:
        metrics["eigenvectorCentrality"] = nx.eigenvector_centrality(G)
        
    print(f"\n{robot_name} Results:")
    for asset in G.nodes():
        acc_metric_value = 0
        acc_threshold = 0
        counter = 1
        for metric_name, metric_values in metrics.items():
            acc_metric_value += parameters[metric_name]["threshold"]
            acc_threshold += metric_values[asset]
            counter+=1
        metric_value = acc_metric_value / counter
        threshold = acc_threshold / counter
        action = "buy" if metric_value > threshold else "sell"
        print(f"Ativo: {asset}, Métrica: {metric_name}, Valor: {metric_value:.3f}, Ação: {action}")




# Define a estratégia de investimento
def investment_strategy(p, t):
  if p > t:
    return "buy"
  else:
    return "sell"

# Simula os investimentos
for asset in G.nodes():
  dc = degree_centrality[asset]
  action = investment_strategy(dc, 0.5)
  print("Ativo:", asset, "Ação:", action)
  
  
  
import requests
import networkx as nx
import json

API_ENDPOINT = "http://localhost:5002/graph"  # Defina sua URL da API aqui

def run_robot(robot_config):
    # Obtenha os dados da API
    response = requests.get(API_ENDPOINT)
    data = response.json()

    if not data or "graph" not in data:
        print("Resposta da API inválida!")
        return

    G = nx.Graph()

    for vertex in data["graph"]["vertices"]:
        G.add_node(vertex["id"], label=vertex["label"])

    for edge in data["graph"]["edges"]:
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])

    metrics = {}

    if robot_config["parameters"][0]["degreeCentrality"]["enable"]:
        metrics["degreeCentrality"] = nx.degree_centrality(G)

    if robot_config["parameters"][0]["pagerank"]["enable"]:
        metrics["pagerank"] = nx.pagerank

