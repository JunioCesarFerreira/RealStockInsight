from confluent_kafka import Producer

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result. """
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

# Configuração do produtor
conf = {
    'bootstrap.servers': 'localhost:29092',  # Substitua se o seu servidor estiver em um endereço diferente
}

producer = Producer(conf)

# Enviar mensagem
producer.produce('test-topic', key=None, value='Hello, Kafka', callback=delivery_report)

# Esperar que as mensagens sejam enviadas
producer.flush(10)  # Tempo em segundos
