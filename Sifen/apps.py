from django.apps import AppConfig


class SifenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Sifen'

    def ready(self):
        import Sifen.signals  # noqa
