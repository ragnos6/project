import os
import django
import json
import logging
from django.core.management.base import BaseCommand
from confluent_kafka import Consumer, KafkaException

# Настройка Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Kafka Consumer for vehicle notifications'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚗 Starting Kafka vehicle notification consumer...')
        )

        conf = {
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'vehicle_notification_group',
            'auto.offset.reset': 'earliest',
            'session.timeout.ms': 6000,
        }
        
        consumer = Consumer(conf)
        
        try:
            consumer.subscribe(['vehicle_events'])
            
            self.stdout.write('✅ Consumer subscribed to vehicle_events topic')
            self.stdout.write('📝 Waiting for messages...')

            while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    if msg.error().code() == KafkaException._PARTITION_EOF:
                        continue
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'Kafka error: {msg.error()}')
                        )
                        continue

                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                    self.process_vehicle_message(message_data)
                    
                except json.JSONDecodeError as e:
                    self.stdout.write(
                        self.style.ERROR(f'JSON decode error: {e}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing message: {e}')
                    )

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('🛑 Stopping consumer...'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}'))
        finally:
            consumer.close()
            self.stdout.write('✅ Consumer closed')

    def process_vehicle_message(self, message_data):
        """Обработка сообщения из Kafka"""
        event_type = message_data.get('event_type')
        vehicle_data = message_data.get('vehicle_data')
        
        self.stdout.write(
            self.style.SUCCESS(f'📨 Received event: {event_type}')
        )
        self.stdout.write(f'   Vehicle: {vehicle_data.get("model", "Unknown")}')
        self.stdout.write(f'   Color: {vehicle_data.get("color", "Unknown")}')
        self.stdout.write(f'   Year: {vehicle_data.get("year_of_production", "Unknown")}')
        
        # Здесь позже добавим отправку в Telegram
        # Пока просто логируем
        
        if event_type == 'vehicle_created':
            self.stdout.write('   Action: 🚗 Vehicle created')
        elif event_type == 'vehicle_updated':
            self.stdout.write('   Action: ✏️ Vehicle updated')
        elif event_type == 'vehicle_deleted':
            self.stdout.write('   Action: 🗑️ Vehicle deleted')
