import json

from kafka import KafkaConsumer


def main():
    consumer = KafkaConsumer(
        "warty-odom",
        bootstrap_servers=["10.0.0.82:9092"],
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
    )

    for message in consumer:
        print(f"Received message: {message.value}")
