from django.core.management.base import BaseCommand
from am_shopify.managers import ProductManager


class Command(BaseCommand):
    help = 'Sincroniza productos desde Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=250,
            help='Número máximo de productos a sincronizar'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        
        self.stdout.write(self.style.WARNING(f'Sincronizando productos (límite: {limit})...'))
        
        manager = ProductManager()
        result = manager.sync_products(limit=limit)
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Sincronización completada:\n'
            f'  - Procesados: {result["processed"]}\n'
            f'  - Creados: {result["created"]}\n'
            f'  - Actualizados: {result["updated"]}\n'
            f'  - Fallidos: {result["failed"]}'
        ))
