import os

import django
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amachine.settings')

app = Celery('Amachine')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_plugin_periodic_tasks(sender, **kwargs):
    """Registra en beat las tareas periodicas declaradas por cada plugin (get_beat_schedule)."""
    django.setup()
    from OptsIO.plugin_manager import plugin_manager  # requiere apps cargadas
    if not plugin_manager.get_all_plugins():
        plugin_manager.discover_plugins()
    for plugin in plugin_manager.get_all_plugins().values():
        for name, entry in plugin.get_beat_schedule().items():
            sender.add_periodic_task(entry['schedule'], sender.signature(entry['task']), name=name)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
