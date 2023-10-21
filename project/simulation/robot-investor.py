import requests
import networkx as nx
import json

API_ENDPOINT = "http://localhost:5002/graph"

# Lê o arquivo de configuração que contém informações sobre os robôs
with open('config.json', 'r') as file:
    config = json.load(file)

def request_graph():
    """Realiza request na API e monta um objeto networkx.Graph.

    Returns:
        networkx.Graph: Rede de co-movimentos do mercado.
    """
    # Realiza o request à API para obter dados do gráfico
    response = requests.get(API_ENDPOINT)
    data = response.json()

    # Verifica se a resposta da API está em um formato adequado
    if not data or "graph" not in data:
        print("Resposta da API inválida!")
        exit()

    G = nx.Graph()

    # Adiciona os vértices (ou nós) ao gráfico
    for vertex in data["graph"]["vertices"]:
        G.add_node(vertex["id"], label=vertex["label"])

    # Adiciona as arestas ao gráfico
    for edge in data["graph"]["edges"]:
        G.add_edge(edge["source"], edge["target"], weight=edge["weight"])
        
    return G

def run_robot(robot_name, parameters, G):
    """Executa o robô para simular a tomada de decisão dos investidores.

    Args:
        robot_name (str): Nome do robô.
        parameters (dict): Parâmetros para métricas específicas.
        G (networkx.Graph): Grafo representando a rede de co-movimentos.

    """
    metrics = {}

    # Calcula as métricas de acordo com os parâmetros fornecidos
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
            counter += 1
        metric_value = acc_metric_value / counter
        threshold = acc_threshold / counter
        action = investment_strategy(metric_value, threshold)
        print(f"Ativo: {asset}, Métrica: {metric_name}, Valor: {metric_value:.3f}, Ação: {action}")

def investment_strategy(p, t):
    """Define a estratégia de investimento com base na métrica e no limite.

    Args:
        p (float): Valor da métrica.
        t (float): Valor do limite (threshold).

    Returns:
        str: Retorna "buy" se p > t, caso contrário retorna "sell".
    """
    if p > t:
        return "buy"
    else:
        return "sell"

# Executa cada robô de acordo com as configurações fornecidas
G = request_graph()  # Solicita o grafo da API
for robot in config["robots"]:
    run_robot(robot["name"], robot["parameters"][0], G)  # Assumindo que cada robô tem apenas um conjunto de parâmetros
