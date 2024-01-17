import os
import requests
import json
import time
import sqlite3
from confluent_kafka import Producer

db_file = "database.db"

def build_repository(ticker, data):
  """
  Registra dados no banco local.

  Args:
    ticker(string): Ticker do ativo
    data(array): Array de dados a serem registrados.

  Returns:
    None.
  """
  conn = sqlite3.connect(db_file)

  conn.execute("CREATE TABLE IF NOT EXISTS datatable (ticker TEXT, time_stamp TEXT, open REAL, high REAL, low REAL, close REAL, volume INTEGER)")

  for d in data:
    conn.execute("INSERT INTO datatable VALUES (?, ?, ?, ?, ?, ?, ?)", (ticker, d["time_stamp"], d["open"], d["high"], d["low"], d["close"], d["volume"]))

  conn.commit()
  conn.close()
  
def pop_repository(ticker):
  """
  Recupera os dados do banco local em ordem crescente pelo time stamp.

  Returns:
    Array de dados.
  """
  conn = sqlite3.connect(db_file)

  cursor = conn.cursor()
  
  cursor.execute("SELECT * FROM datatable WHERE ticker = ? ORDER BY time_stamp ASC", (ticker,))
  
  data = cursor.fetchall()
  
  result = []
  for i in range(60):
    top = data[i]
  
    if i==0:
        print(f"delete: {top[1]} {top[0]}")
        cursor.execute("DELETE FROM datatable WHERE time_stamp = ? AND ticker= ?", (top[1], top[0],))
        conn.commit()
  
    result.append({
      "time":top[1],
      "open":top[2],
      "close":top[5],
      "high":top[3],
      "low":top[4],
      "volume":top[6]
    })

  conn.close()
  return result

def has_data_repository():
    conn = sqlite3.connect(db_file)

    cursor = conn.cursor()
  
    cursor.execute("SELECT COUNT(*) FROM datatable")
      
    rows_count = cursor.fetchone()[0]
    
    conn.close()
    
    if rows_count == 0:
        os.remove("./" + db_file)
        return False
    else:
        return True
    

def get_daily_time_series(ticker, uri, apiKey):
    """Realiza request na API

    Args:
        ticker (string): Ativo a ser consultado
        uri (string): URI de acesso à API
        apiKey (string): Chave da API

    Returns:
        string: JSON resultante do request
    """
    headers = {
        'accept': 'application/json',
        'ApiKey': apiKey
    }
    params = {
        'ticker': ticker,
        'compact': 'false'
    }
    
    response = requests.get(uri, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def create_database(tickers, uri, apiKey):
    """Cria a base de dados para ser enviada aos poucos para o Kafka.
    
    Args:
        tickers (list): Lista de códigos de ativos para os quais os dados devem ser buscados.
        uri (string): URI de acesso à API de dados de ativos.
        apiKey (string): Chave de acesso à API de dados de ativos.
    
    Retorna:
        str: Carga útil em formato JSON para ser enviada para o Kafka.
    """    
    for ticker in tickers:
        prices_data = get_daily_time_series(ticker, uri, apiKey)
        build_repository(ticker, prices_data)
      
  
def create_final_payload(tickers):
    """Cria a carga útil final para ser enviada para o Kafka.
    
    Args:
        tickers (list): Lista de códigos de ativos para os quais os dados devem ser buscados.
    
    Retorna:
        str: Carga útil em formato JSON para ser enviada para o Kafka.
    """
    stocks_data = []
    
    for ticker in tickers:
        prices_data = pop_repository(ticker)
        stock_data = {
            "ticker": ticker,
            "price_data": prices_data
        }
        stocks_data.append(stock_data)
    
    final_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stocks": stocks_data
    }
    
    return json.dumps(final_payload)

   
def start_streaming(tickers, config):
    """Inicia o fluxo contínuo de dados para o Kafka.
    
    Args:
        tickers (list): Lista de códigos de ativos para os quais os dados devem ser buscados.
        configs (dict): Dicionário de configurações de acesso API e KAFKA
    """
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
            
    producer = Producer(config['KAFKA_BOOTSTRAP_SERVERS'])
    
    # Se banco de dados não existe realiza sequência de requests na API e monta banco de dados
    if os.path.exists("./" + db_file) == False:
        uri = config["API"]["URL"] + config["API"]["URN"]
        create_database(tickers, uri, config["API"]["TOKEN"])        
        
    # Enquanto houver dados no banco insere tópicos no Kafka
    while has_data_repository():
        payload = create_final_payload(tickers)   
        print("payload", payload)
        
        producer.produce(config['KAFKA_TOPIC'], key=None, value=payload, callback=delivery_report)
        
        time.sleep(config["TIME_SLEEP"])
        
        
# Inicio do processo
if __name__=="__main__":
    
    print("starting producer")
    
    with open('producer_config.json', 'r') as file:
        config = json.load(file)

    is_debug = os.getenv('PROD') == None

    if is_debug:
        print("is debug")
        config["API"]["URL"] = "http://localhost:5054"
        config['KAFKA_BOOTSTRAP_SERVERS'] = {
            "bootstrap.servers": "localhost:29092"
        }
    else:
        print("not is debug")
        
    with open('tickers.json', 'r') as file:
        data = json.load(file)
        tickers = data['tickers']
    
    start_streaming(tickers, config)
