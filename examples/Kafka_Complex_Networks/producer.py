import requests
import json
import time

from confluent_kafka import Producer

# Configurações API
ALPHA_VANTAGE_API_URL = "https://www.alphavantage.co/query"
API_KEY = "YOUR_API_KEY"
# Configurações Kafka
KAFKA_BOOTSTRAP_SERVERS = {
    'bootstrap.servers': 'localhost:29092',
}

KAFKA_TOPIC = "stock_prices"

def fetch_alpha_vantage_data(ticker):
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": ticker,
        "interval": "1min",
        "apikey": API_KEY
    }
    response = requests.get(ALPHA_VANTAGE_API_URL, params=params)
    raw_data = response.json()
    
    #DEBUG
    #print(json.dumps(raw_data, indent=4))
    
    # Extrair e transformar dados brutos para obter os campos desejados.
    # A estrutura exata pode precisar ser ajustada com base na resposta real da API.
    last_refresh = raw_data['Meta Data']['3. Last Refreshed']
    last_data = raw_data['Time Series (1min)'][last_refresh]
    
    transformed_data = {
        "last_refresh": last_refresh,
        "open": float(last_data['1. open']),
        "close": float(last_data['4. close']),
        "high": float(last_data['2. high']),
        "low": float(last_data['3. low']),
        "volume": int(last_data['5. volume'])
    }
    
    return transformed_data

def create_final_payload(tickers):
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stocks_data = []
    
    for ticker in tickers:
        price_data = fetch_alpha_vantage_data(ticker)
        
        stock_data = {
            "ticker": ticker,
            "price_data": price_data
        }
        stocks_data.append(stock_data)
    
    final_payload = {
        "timestamp": timestamp,
        "stocks": stocks_data
    }
    
    return json.dumps(final_payload)

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

   
def start_streaming(tickers):
    producer = Producer(KAFKA_BOOTSTRAP_SERVERS)
    
    while True:
        payload = create_final_payload(tickers)
        producer.produce(KAFKA_TOPIC, key=None, value=payload, callback=delivery_report)
        # Intervalo de 1 minuto para estar em conformidade com o intervalo de tempo da API Alpha Vantage
        time.sleep(60)  
        
# Ler tickers do arquivo JSON
with open('tickers.json', 'r') as file:
    data = json.load(file)
    tickers = data['tickers']
    
start_streaming(tickers)
