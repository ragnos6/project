from confluent_kafka import Producer, KafkaException
import json
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class KafkaService:
    def __init__(self):
        self.conf = {
            'bootstrap.servers': 'localhost:9092',
            'message.timeout.ms': 5000,
            'retries': 3,
        }
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Установка соединения с Kafka"""
        try:
            self.producer = Producer(self.conf)
            # Тестовое сообщение для проверки подключения
            self.producer.produce('test_connection', value='test')
            self.producer.flush(timeout=5)
            logger.info("✅ Successfully connected to Kafka")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            self.producer = None
    
    def send_vehicle_event(self, event_type, vehicle_data, user):
        """Отправка события автомобиля в Kafka"""
        if self.producer is None:
            logger.warning("Kafka producer not available, skipping message")
            return False
        
        try:
            message = {
                'event_type': event_type,
                'vehicle_data': vehicle_data,
                'user': {
                    'id': user.id,
                    'username': user.username,
                },
                'timestamp': str(timezone.now())
            }
            
            self.producer.produce(
                'vehicle_events', 
                value=json.dumps(message),
                callback=self._delivery_report
            )
            
            # Асинхронная отправка - не блокируем основной поток
            self.producer.poll(0)
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
            return False
    
    def _delivery_report(self, err, msg):
        """Callback для отслеживания доставки сообщений"""
        if err is not None:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')
    
    def flush(self):
        """Принудительная отправка всех сообщений"""
        if self.producer:
            self.producer.flush()

# Глобальный экземпляр сервиса
kafka_service = KafkaService()
