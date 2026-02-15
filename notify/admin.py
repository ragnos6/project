from django.contrib import admin
from .models import ManagerTelegramProfile

@admin.register(ManagerTelegramProfile)
class ManagerTelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'telegram_chat_id', 'is_active', 'created_at')
    list_filter = ('is_active', 'receive_vehicle_notifications', 'receive_driver_notifications')
    search_fields = ('user__username', 'telegram_chat_id')
