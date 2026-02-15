from django.core.management.base import BaseCommand
from am_shopify.shopify_client import ShopifyAPIClient
from am_shopify.mng_shopify import MShopify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Comando mainline para sincronización de Shopify'

    def add_arguments(self, parser):
        # Opciones de sincronización
        parser.add_argument('--clientes', action='store_true', help='Sincronizar clientes')
        parser.add_argument('--productos', action='store_true', help='Sincronizar productos')
        parser.add_argument('--ordenes', action='store_true', help='Sincronizar órdenes')
        parser.add_argument('--pagos', action='store_true', help='Sincronizar pagos (órdenes pagadas)')

        # Filtros
        parser.add_argument('--fecha-desde', type=str, help='Fecha desde (YYYY-MM-DD)')
        parser.add_argument('--fecha-hasta', type=str, help='Fecha hasta (YYYY-MM-DD)')
        parser.add_argument('--limit', type=int, default=250, help='Límite de registros por sincronización')

    def handle(self, *args, **options):
        client = ShopifyAPIClient()
        manager = MShopify()

        # Sincronización de clientes
        if options['clientes']:
            self.stdout.write(self.style.WARNING('Sincronizando clientes...'))
            stats = client.sync_customers(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS(
                f"✓ Clientes: {stats['created']} creados, {stats['updated']} actualizados, {stats['errors']} errores"
            ))

        # Sincronización de productos
        if options['productos']:
            self.stdout.write(self.style.WARNING('Sincronizando productos...'))
            stats = client.sync_products(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS(
                f"✓ Productos: {stats['created']} creados, {stats['updated']} actualizados, {stats['errors']} errores"
            ))

        # Sincronización de órdenes
        if options['ordenes']:
            self.stdout.write(self.style.WARNING('Sincronizando órdenes...'))
            stats = client.sync_orders(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS(
                f"✓ Órdenes: {stats['created']} creados, {stats['updated']} actualizados, {stats['errors']} errores"
            ))

        # Sincronización de pagos
        if options['pagos']:
            self.stdout.write(self.style.WARNING('Sincronizando pagos...'))
            stats = client.sync_paid_orders(limit=options['limit'])
            self.stdout.write(self.style.SUCCESS(
                f"✓ Pagos: {stats['created']} creados, {stats['updated']} actualizados, {stats['errors']} errores"
            ))
