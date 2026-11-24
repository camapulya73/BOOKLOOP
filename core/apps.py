from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основная модель буккроссинга'

    def ready(self):
        from .sqlite_unicode import connect
        connect()
