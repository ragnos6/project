from django.db import models
from django.contrib.auth.models import User

class ManagerTelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Менеджер")
    telegram_chat_id = models.BigIntegerField(unique=True, verbose_name="ID чата в Telegram")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    receive_vehicle_notifications = models.BooleanField(default=True, verbose_name="Уведомления об автомобилях")
    receive_driver_notifications = models.BooleanField(default=True, verbose_name="Уведомления о водителях")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Телеграм профиль менеджера'
        verbose_name_plural = 'Телеграм профили менеджеров'

    def __str__(self):
        return f"{self.user.username} - {self.telegram_chat_id}"
