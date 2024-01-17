import json
import psycopg2
from confluent_kafka import Consumer, KafkaException
    
def insert_data_row(cursor, ticker, trend, price):
    """Insere dados de tendencia e preço atual na tabela TRENDS."""
    query = """
            INSERT INTO TRENDS (ticker, trend, price) VALUES (%s, %s, %s);
            """
    cursor.execute(query, (ticker, trend, price))
    conn.commit()

def determine_trend(prices):
    """ Tendência com base na média móvel."""
    window_size = len(prices)

    moving_avg = sum(prices[-window_size:]) / window_size

    if prices[-1] > moving_avg:
        return 'up'
    else:
        return 'down'

def process_message(msg):
    """Processa mensagem do tópico 'stock-prices' do Kafka."""
    print("processando")
    msg_json = json.loads(msg.value().decode('utf-8'))
    for _, stock_data in enumerate(msg_json['stocks']):
        ticker = stock_data['ticker']
        prices = []
        for _, stock in enumerate(stock_data['price_data']):
            prices.append(stock['close'])
        trend = determine_trend(prices)
        price = prices[len(prices)-1]
        insert_data_row(cursor, ticker, trend, price)
        
if __name__ == '__main__':
    # Carrega as configurações
    with open('consumer_trend_config.json', 'r') as file:
        conf = json.load(file)

    # consumer Kafka
    consumer = Consumer({
        "bootstrap.servers": conf["bootstrap.servers"],
        "group.id": conf["group.id"],
        "auto.offset.reset": conf["auto.offset.reset"]
    })
    consumer.subscribe(['stock-prices'])

    # Banco de dados PostgreSQL
    db_conf = conf["database"]
    conn = psycopg2.connect(
        dbname=db_conf["dbname"],
        user=db_conf["user"],
        password=db_conf["password"],
        host=db_conf["host"],
        port=db_conf["port"]
    )
    cursor = conn.cursor()

    print("iniciando...")
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
                process_message(msg)

    except KeyboardInterrupt:
        pass

    finally:
        # Fecha o consumidor Kafka e a conexão PostgreSQL
        consumer.close()
        cursor.close()
        conn.close()
