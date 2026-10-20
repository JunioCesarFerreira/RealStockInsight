import json
import os
import time
import psycopg2
from confluent_kafka import Consumer, KafkaError
from monitor import Monitor, kafka_lag

mon = Monitor("consumer-trend")

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
    """Processa mensagem do tópico 'stock-prices' do Kafka.

    Returns:
        dict: Quantidade de ativos em cada tendência.
    """
    msg_json = json.loads(msg.value().decode('utf-8'))
    counts = {'up': 0, 'down': 0}
    for _, stock_data in enumerate(msg_json['stocks']):
        ticker = stock_data['ticker']
        prices = []
        for _, stock in enumerate(stock_data['price_data']):
            prices.append(stock['close'])
        if not prices:
            continue
        trend = determine_trend(prices)
        price = prices[len(prices)-1]
        insert_data_row(cursor, ticker, trend, price)
        counts[trend] += 1
    return counts

def connect_db(db_conf):
    """Conecta ao PostgreSQL, aguardando enquanto o banco estiver indisponível."""
    while True:
        try:
            return psycopg2.connect(
                dbname=db_conf["dbname"],
                user=db_conf["user"],
                password=os.environ["DB_PASSWORD"],
                host=db_conf["host"],
                port=db_conf["port"]
            )
        except psycopg2.OperationalError as e:
            mon.state("waiting", "Waiting for PostgreSQL")
            mon.warn(f"Database unavailable, retrying in 5s: {e}")
            time.sleep(5)

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
    conn = connect_db(conf["database"])
    cursor = conn.cursor()

    mon.state("waiting", "Waiting for messages on topic 'stock-prices'")
    last_lag_check = 0
    try:
        while True:
            # Atualiza periodicamente o backlog de mensagens no Kafka
            if time.time() - last_lag_check > mon.interval:
                mon.set(kafka_lag=kafka_lag(consumer))
                last_lag_check = time.time()

            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    mon.state("waiting", "Topic 'stock-prices' does not exist yet: waiting for the producer")
                else:
                    mon.error(f"Kafka error: {msg.error()}")
            else:
                mon.incr("messages_consumed")
                mon.set(last_message_at=time.time())
                try:
                    counts = process_message(msg)
                    mon.incr("trend_rows_written", counts['up'] + counts['down'])
                    mon.set(tickers_up=counts['up'], tickers_down=counts['down'])
                    mon.state("running", "Computing moving-average trends on every message")
                    mon.info(f"Trends updated: {counts['up']} up, {counts['down']} down")
                except Exception as e:
                    mon.incr("processing_errors")
                    mon.state("error", str(e))
                    mon.error(f"Failed to process message: {e}")
                    if conn.closed:
                        raise
                    conn.rollback()

    except KeyboardInterrupt:
        pass

    finally:
        # Fecha o consumidor Kafka e a conexão PostgreSQL
        consumer.close()
        cursor.close()
        conn.close()
