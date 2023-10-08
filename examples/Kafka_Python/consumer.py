from confluent_kafka import Consumer, KafkaException

# Configuração do consumidor
conf = {
    'bootstrap.servers': 'localhost:29092',  # Substitua se o seu servidor estiver em um endereço diferente
    'group.id': 'python-consumer',
    'auto.offset.reset': 'earliest',  # Começa a ler o tópico do início se o offset não for encontrado
}

consumer = Consumer(conf)

# Subscrever ao tópico
consumer.subscribe(['test-topic'])

try:
    while True:
        msg = consumer.poll(1.0)  # Tempo em segundos

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaException._PARTITION_EOF:
                continue
            else:
                print(f'Error: {msg.error()}')
        else:
            print(f'Received message: {msg.value().decode("utf-8")}')

except KeyboardInterrupt:
    pass

finally:
    # Fechar o consumidor
    consumer.close()
