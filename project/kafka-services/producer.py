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
KAFKA_TOPIC = "stock-prices"

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
    print(json.dumps(raw_data, indent=4))
    
    transformed_data_list = []
    
    for item in raw_data['Time Series (1min)']:
        content = raw_data['Time Series (1min)'][item]
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
        time.sleep(7200) # Intervalo de 2 horas
        
# Ler tickers do arquivo JSON
with open('tickers.json', 'r') as file:
    data = json.load(file)
    tickers = data['tickers']
    
start_streaming(tickers)
