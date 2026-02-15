from django.core.management.base import BaseCommand
from am_shopify.managers import OrderManager


class Command(BaseCommand):
    help = 'Sincroniza órdenes desde Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=250,
            help='Número máximo de órdenes a sincronizar'
        )
        parser.add_argument(
            '--status',
            type=str,
            default='any',
            choices=['open', 'closed', 'cancelled', 'any'],
            help='Estado de las órdenes a sincronizar'
        )
        parser.add_argument(
            '--financial-status',
            type=str,
            choices=['pending', 'authorized', 'paid', 'partially_paid', 'refunded', 'voided'],
            help='Estado financiero de las órdenes'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        status = options['status']
        financial_status = options['financial_status']
        
        self.stdout.write(self.style.WARNING(f'Sincronizando órdenes (límite: {limit}, estado: {status})...'))
        
        manager = OrderManager()
        result = manager.sync_orders(limit=limit, status=status, financial_status=financial_status)
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Sincronización completada:\n'
            f'  - Procesadas: {result["processed"]}\n'
            f'  - Creadas: {result["created"]}\n'
            f'  - Actualizadas: {result["updated"]}\n'
            f'  - Fallidas: {result["failed"]}'
        ))
