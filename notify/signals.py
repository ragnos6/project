# notify/signals.py
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
#from .kafka_producer import send_vehicle_event
from cars.models import Vehicle

@receiver(pre_save, sender=Vehicle)
def vehicle_pre_save(sender, instance, **kwargs):
    # Сохраняем снимок до сохранения, чтобы потом иметь изменённые поля
    if instance.pk:
        try:
            instance._pre_save_snapshot = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._pre_save_snapshot = None

def _serialize_vehicle(instance):
    """Возвращаем минимальный сериализуемый набор полей."""
    return {
        "id": instance.pk,
        "model_id": instance.model_id if hasattr(instance, 'model_id') else None,
        "color": instance.color,
        "mileage": instance.mileage,
        "enterprise_id": instance.enterprise_id if hasattr(instance, 'enterprise_id') else None,
        "active_driver_id": instance.active_driver_id if hasattr(instance, 'active_driver_id') else None,
        "purchase_date": instance.purchase_date.isoformat() if instance.purchase_date else None,
    }

@receiver(post_save, sender=Vehicle)
def vehicle_post_save(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    changed = {}
    if not created:
        orig = getattr(instance, '_pre_save_snapshot', None)
        if orig:
            for field in instance._meta.fields:
                name = field.name
                old = getattr(orig, name)
                new = getattr(instance, name)
                if old != new:
                    changed[name] = {'old': old, 'new': new}
    payload = _serialize_vehicle(instance)
    if changed:
        payload['changed_fields'] = changed
    #send_vehicle_event(action, payload)

@receiver(post_delete, sender=Vehicle)
def vehicle_post_delete(sender, instance, **kwargs):
    from .events import send_vehicle_event  # <-- импорт внутри функции
    payload = _serialize_vehicle(instance)
    send_vehicle_event('delete', payload)
