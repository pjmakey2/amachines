from django.apps import AppConfig

class OptsioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'OptsIO'

    def ready(self):
        import OptsIO.signals
