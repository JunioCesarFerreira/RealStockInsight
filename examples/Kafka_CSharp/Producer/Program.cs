using Confluent.Kafka;

var config = new ProducerConfig { BootstrapServers = "localhost:29092" };

using (var producer = new ProducerBuilder<Null, string>(config).Build())
{
    try
    {
        var dr = producer.ProduceAsync("test-topic", new Message<Null, string> { Value = "Hello, Kafka" }).Result;
        Console.WriteLine($"Delivered '{dr.Value}' to '{dr.TopicPartitionOffset}'");
    }
    catch (ProduceException<Null, string> e)
    {
        Console.WriteLine($"Delivery failed: {e.Error.Reason}");
    }
}