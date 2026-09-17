from django.core.management.base import BaseCommand

from OptsIO.events import process_pending


class Command(BaseCommand):
    help = 'Recuperacion manual de eventos de negocio pendientes o con error (el flujo normal es por Celery)'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200)

    def handle(self, *args, **options):
        result = process_pending(limit=options['limit'])
        self.stdout.write(f"Eventos: {result['processed']} procesados, {result['done']} ok, {result['error']} con error")
