import os
import requests
import json
import time
import math
import sqlite3
import networkx as nx
from queue import Queue
from threading import Lock, Thread
from market import MarketClient, MarketNotReady, OrderRejected
from monitor import Monitor

API_GRAPH_ENDPOINT = "http://localhost:5002/api/graph"
API_TREND_ENDPOINT = "http://localhost:5002/api/trend"
API_MARKET_URL = "http://localhost:5002"

# Serializa as escritas no SQLite: todos os bots (threads) gravam no mesmo arquivo
log_lock = Lock()

# Classe Robô Investidor
class Bot:
    """Investidor simulado. Saldo e carteira ficam na conta do mercado; o bot guarda apenas
    a dotação inicial usada para abrir a conta."""
    def __init__(self, id, name, initial_money, initial_assets):
        self.id = id
        self.name = name
        self.initial_money = initial_money
        self.initial_assets = initial_assets


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
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with log_lock:
        conn = sqlite3.connect("bot_log.db", timeout=30)

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
    # Realiza o request à API para obter rede complexa atualizada
    response = requests.get(API_GRAPH_ENDPOINT, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Verifica se a resposta da API está em um formato adequado
    if not isinstance(data, dict) or "nodes" not in data or "links" not in data:
        raise ValueError("Resposta da API de grafo inválida")

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
    headers = {
        'accept': 'application/json'
    }
    response = requests.get(API_TREND_ENDPOINT, headers=headers, timeout=30)
    response.raise_for_status()

    trends_list = response.json() or []

    trends_dict = {
        item['ticker']: {
            "trend": item['trend'],
            "price": item['price']
            } for item in trends_list}

    return trends_dict

def place_order(market, side, bot, ticker, amount, holdings, execution):
    """Envia a ordem ao mercado e atualiza a carteira local com o resultado da liquidação.

    Returns:
        float: Caixa após a ordem, ou None se o mercado recusou a ordem.
    """
    try:
        if side == "buy":
            result = market.buy(bot.id, ticker, amount)
        else:
            result = market.sell(bot.id, ticker, amount)
    except OrderRejected:
        execution["rejected"] += 1
        return None
    holdings[ticker] = result["holding"]
    execution[side] += 1
    execution["volume"] += float(result["trade"]["total"])
    return float(result["cash"])

def run_robot(bot, parameters, G, trends, market):
    """Executa o robô para simular a tomada de decisão dos investidores.

    Args:
        bot (object): Atributos do robô.
        parameters (dict): Parâmetros para métricas específicas.
        G (networkx.Graph): Grafo representando a rede de co-movimentos.
        trends (dict): Tendência e preço de referência de cada ativo.
        market (MarketClient): Mercado onde as ordens são executadas.

    Returns:
        tuple: Decisões de cada tipo (buy, sell, hold) e ativos sem tendência (skipped);
               ordens executadas (buy, sell), recusadas (rejected) e volume negociado (volume).
    """
    metrics = {}
    decisions = {"buy": 0, "sell": 0, "hold": 0, "skipped": 0}
    execution = {"buy": 0, "sell": 0, "rejected": 0, "volume": 0.0}

    # Posição atual da conta no mercado
    account = market.account(bot.id)
    cash = float(account["cash"])
    holdings = dict(account.get("holdings", {}))

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
        if ticker not in trends:
            # Tendência ainda não calculada pelo consumer-trend
            decisions["skipped"] += 1
            continue
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
            decisions[action] += 1

            new_cash = None
            if action == "buy":
                if cash > price:
                    # Compra porcentagem fixa! Pensar em estratégias mais dinâmicas!
                    value = (cash / price) * 0.15
                    amount = math.floor(value)
                    if amount==0:
                        amount = 1
                    new_cash = place_order(market, "buy", bot, ticker, amount, holdings, execution)

            elif action == "sell":
                # Vende tudo! Pensar em estratégias mais dinâmicas!
                amount = holdings.get(ticker, 0)
                if amount > 0:
                    new_cash = place_order(market, "sell", bot, ticker, amount, holdings, execution)

            if new_cash is not None:
                cash = new_cash

            assets_txt = json.dumps(holdings)
            insert_log_repository(bot.name, bot.id, ticker, metric_value, action, cash, assets_txt)
        else:
            raise ValueError(f"Nenhuma métrica foi selecionada para o bot {bot.name}")

    return decisions, execution


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


def describe_strategy(parameters):
    """Descrição curta das métricas habilitadas e seus limites."""
    enabled = [f"{name} > {p['threshold']}" for name, p in parameters.items() if p["enable"]]
    return ", ".join(enabled) if enabled else "nenhuma métrica"


def thread_run_robot(robot, queue, mon):
    """Função de thread para executar um robô."""
    with open('initial_assets.json', 'r') as file:
        initial_assets = json.load(file)

    bot = Bot(robot["id"], robot["name"], robot["initialMoney"], initial_assets)
    market = MarketClient(API_MARKET_URL)
    account_opened = False
    totals = {"buy": 0, "sell": 0, "hold": 0}
    cycles = 0

    while True:
        # Verifica se a thread deve ser encerrada
        if queue.empty():
            break

        try:
            G = request_graph()  # Solicita o grafo da API
            if G.number_of_nodes() == 0:
                mon.state("waiting", "Aguardando a primeira rede de co-movimento (consumer-network)")
            else:
                trends = request_trend() # Solicita tendências da API
                if not trends:
                    mon.state("waiting", "Aguardando tendências (consumer-trend)")
                else:
                    if not account_opened:
                        # Abre a conta (ou retoma a existente, após reinício do bot)
                        account = market.open_account(bot.id, bot.initial_money, bot.initial_assets)
                        account_opened = True
                        mon.info(f"Conta no mercado: caixa US$ {float(account['cash']):,.2f}, "
                                 f"patrimônio US$ {float(account['net_worth']):,.2f}")

                    decisions, execution = run_robot(bot, robot["parameters"][0], G, trends, market)
                    account = market.account(bot.id)
                    cycles += 1
                    for action in totals:
                        totals[action] += decisions[action]
                    mon.set(cycles=cycles, last_cycle_at=time.time(),
                            last_buy=decisions["buy"], last_sell=decisions["sell"], last_hold=decisions["hold"],
                            total_buy=totals["buy"], total_sell=totals["sell"], total_hold=totals["hold"],
                            last_trades_buy=execution["buy"], last_trades_sell=execution["sell"],
                            last_rejected=execution["rejected"],
                            cash=float(account["cash"]), net_worth=float(account["net_worth"]),
                            result_pct=account["result_pct"])
                    mon.state("running", f"Avaliando {G.number_of_nodes()} ativos a cada {robot['interval']}s")
                    mon.info(f"Ciclo {cycles}: decisões {decisions['buy']} compra, {decisions['sell']} venda, "
                             f"{decisions['hold']} manter" +
                             (f", {decisions['skipped']} sem tendência" if decisions["skipped"] else "") +
                             f"; executadas {execution['buy']} compras e {execution['sell']} vendas "
                             f"(US$ {execution['volume']:,.2f})" +
                             (f", {execution['rejected']} recusadas" if execution["rejected"] else "") +
                             f"; patrimônio US$ {float(account['net_worth']):,.2f} ({account['result_pct']:+.2f}%)")
        except MarketNotReady as e:
            mon.state("waiting", f"Mercado ainda sem preços: {e}")
        except Exception as e:
            mon.incr("errors")
            mon.state("error", str(e))
            mon.error(f"Falha no ciclo do bot: {e}")

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
                API_MARKET_URL = apiEndpoints["market"]
    except Exception as e:
        print(f"Falha ao ler configurações: {e}")
        exit(1)

    # Um monitor por bot, para que cada um apareça no painel
    monitors = {}
    for robot in config["robots"]:
        mon = Monitor("investor-bot", instance=robot["name"], interval=15)
        mon.set(trader_id=robot["id"], strategy=describe_strategy(robot["parameters"][0]),
                interval_s=robot["interval"], initial_money=robot["initialMoney"])
        monitors[robot["name"]] = mon

    # Atraso na inicialização
    print("waiting...")
    if is_debug == False:
        for mon in monitors.values():
            mon.state("starting", "Aguardando 60s para os demais serviços iniciarem")
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
        t = Thread(target=thread_run_robot, args=(robot, queue, monitors[robot["name"]]))
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
