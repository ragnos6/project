from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notify"

    def ready(self):
        import notify.signals 
