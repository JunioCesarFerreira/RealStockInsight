import requests
import json
import time
from confluent_kafka import Producer

# Configurações do arquivo externo
with open('producer_config.json', 'r') as file:
    config = json.load(file)

ALPHA_VANTAGE_API_URL = config['ALPHA_VANTAGE_API_URL']
ALPHA_VANTAGE_API_KEY = config['ALPHA_VANTAGE_API_KEY']
KAFKA_BOOTSTRAP_SERVERS = config['KAFKA_BOOTSTRAP_SERVERS']
KAFKA_TOPIC = config['KAFKA_TOPIC']
ALPHA_VANTAGE_INTERVAL = config['ALPHA_VANTAGE_INTERVAL']
ALPHA_VANTAGE_DELAY = config['ALPHA_VANTAGE_DELAY']

def fetch_alpha_vantage_data(ticker):
    """Busca e transforma dados da API Alpha Vantage para um formato desejado.
    
    Args:
        ticker (str): O código do ativo (por exemplo, "AAPL" para Apple Inc.).
    
    Retorna:
        list: Lista de dados transformados para cada minuto do ticker fornecido.
    """
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": ALPHA_VANTAGE_INTERVAL,
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    response = requests.get(ALPHA_VANTAGE_API_URL, params=params)
    raw_data = response.json()
    
    #DEBUG
    print(json.dumps(raw_data, indent=4))
    
    transformed_data_list = []
    
    for item in raw_data[f'Time Series ({ALPHA_VANTAGE_INTERVAL})']:
        content = raw_data[f'Time Series ({ALPHA_VANTAGE_INTERVAL})'][item]
        transformed_data = {
            "time": item,
            "open": float(content['1. open']),
            "close": float(content['4. close']),
            "high": float(content['2. high']),
            "low": float(content['3. low']),
            "volume": int(content['5. volume'])
        }
        transformed_data_list.append(transformed_data)
    
    return transformed_data_list

def create_final_payload(tickers):
    """Cria a carga útil final para ser enviada para o Kafka.
    
    Args:
        tickers (list): Lista de códigos de ativos para os quais os dados devem ser buscados.
    
    Retorna:
        str: Carga útil em formato JSON para ser enviada para o Kafka.
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stocks_data = []
    
    for ticker in tickers:
        prices_data = fetch_alpha_vantage_data(ticker)
        stock_data = {
            "ticker": ticker,
            "price_data": prices_data
        }
        stocks_data.append(stock_data)
    
    final_payload = {
        "timestamp": timestamp,
        "stocks": stocks_data
    }
    
    return json.dumps(final_payload)

def delivery_report(err, msg):
    """Callback para indicar o resultado da entrega da mensagem ao Kafka.
    
    Args:
        err (Error): Erro ocorrido durante a entrega, se houver.
        msg (Message): Mensagem que foi entregue ou falhou.
    """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

   
def start_streaming(tickers):
    """Inicia o fluxo contínuo de dados para o Kafka.
    
    Args:
        tickers (list): Lista de códigos de ativos para os quais os dados devem ser buscados.
    """
    producer = Producer(KAFKA_BOOTSTRAP_SERVERS)
    
    while True:
        payload = create_final_payload(tickers)
        producer.produce(KAFKA_TOPIC, key=None, value=payload, callback=delivery_report)
        time.sleep(ALPHA_VANTAGE_DELAY)
        
# Ler tickers do arquivo JSON
with open('tickers.json', 'r') as file:
    data = json.load(file)
    tickers = data['tickers']
    
start_streaming(tickers)
