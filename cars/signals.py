from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Vehicle
from .kafka_service import kafka_service
import logging

logger = logging.getLogger(__name__)

def get_vehicle_data(instance):
    """Формирование данных автомобиля для Kafka"""
    return {
        'id': instance.id,
        'model': str(instance.model),
        'color': instance.color,
        'year_of_production': instance.year_of_production,
        'mileage': instance.mileage,
        'cost': str(instance.cost),
        'transmission': instance.get_transmission_display(),
        'fuel_type': instance.get_fuel_type_display(),
        'enterprise': str(instance.enterprise) if instance.enterprise else None,
        'active_driver': str(instance.active_driver) if instance.active_driver else None,
        'purchase_date': instance.local_purchase_date.strftime('%d.%m.%Y %H:%M') if hasattr(instance, 'local_purchase_date') else str(instance.purchase_date),
    }

@receiver(post_save, sender=Vehicle)
def vehicle_created_or_updated(sender, instance, created, **kwargs):
    try:
        event_type = 'vehicle_created' if created else 'vehicle_updated'
        vehicle_data = get_vehicle_data(instance)
        
        # Используем системного пользователя или пользователя из запроса
        system_user = User.objects.filter(is_staff=True).first()
        if system_user:
            kafka_service.send_vehicle_event(event_type, vehicle_data, system_user)
            logger.info(f"Sent {event_type} event for vehicle {instance.id}")
        
    except Exception as e:
        logger.error(f"Error in vehicle_created_or_updated signal: {e}")

@receiver(post_delete, sender=Vehicle)
def vehicle_deleted(sender, instance, **kwargs):
    try:
        vehicle_data = {
            'id': instance.id,
            'model': str(instance.model),
            'color': instance.color,
            'year_of_production': instance.year_of_production,
        }
        
        system_user = User.objects.filter(is_staff=True).first()
        if system_user:
            kafka_service.send_vehicle_event('vehicle_deleted', vehicle_data, system_user)
            logger.info(f"Sent vehicle_deleted event for vehicle {instance.id}")
            
    except Exception as e:
        logger.error(f"Error in vehicle_deleted signal: {e}")
