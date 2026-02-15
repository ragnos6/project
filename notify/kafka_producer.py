# notifications/kafka_producer.py
import json
import time
from kafka import KafkaProducer
from django.conf import settings

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    linger_ms=10
)

def send_vehicle_event(action: str, payload: dict):
    """
    action: 'create'|'update'|'delete'
    payload: serializable dict with minimal info
    """
    event = {
        'action': action,
        'ts': int(time.time()),
        'payload': payload
    }
    producer.send(settings.KAFKA_VEHICLE_TOPIC, value=event)
    producer.flush()
