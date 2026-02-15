"""
Management command para ejecutar todos los tests de Shopify
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from am_shopify.models import ShopifyOrder
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ejecuta todos los tests de Shopify en secuencia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-products',
            action='store_true',
            help='Saltar creación de productos de prueba'
        )
        parser.add_argument(
            '--skip-inventory',
            action='store_true',
            help='Saltar actualización de inventario'
        )
        parser.add_argument(
            '--skip-description',
            action='store_true',
            help='Saltar actualización de descripción/EAN'
        )
        parser.add_argument(
            '--skip-orders',
            action='store_true',
            help='Saltar sincronización de órdenes'
        )
        parser.add_argument(
            '--skip-conversion',
            action='store_true',
            help='Saltar conversión a facturas'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('SHOPIFY - SUITE DE TESTS COMPLETA'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 1. Test de renovación de token
        self.run_test(
            'Renovación de Token',
            lambda: call_command('shopify_refresh_token')
        )

        # 2. Crear productos de prueba
        if not options.get('skip_products'):
            self.run_test(
                'Crear Productos de Prueba',
                lambda: call_command('shopify_test_create_products', count=5)
            )

        # 3. Actualizar inventario
        if not options.get('skip_inventory'):
            self.run_test(
                'Actualizar Inventario',
                lambda: call_command('shopify_test_update_inventory', test_products=True, quantity=50)
            )

        # 4. Actualizar descripción/EAN
        if not options.get('skip_description'):
            self.run_test(
                'Actualizar Descripción y EAN',
                lambda: call_command(
                    'shopify_test_update_description',
                    test_products=True,
                    description='Producto de prueba actualizado automáticamente',
                    barcode='750000'  # Se agregará sufijo único
                )
            )

        # 5. Sincronizar órdenes
        if not options.get('skip_orders'):
            self.run_test(
                'Sincronizar Órdenes',
                lambda: call_command('shopify_sync_orders', limit=10)
            )

        # 6. Mostrar órdenes pagadas
        if not options.get('skip_orders'):
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('─' * 80))
            self.stdout.write(self.style.WARNING('ÓRDENES PAGADAS'))
            self.stdout.write(self.style.WARNING('─' * 80))

            paid_orders = ShopifyOrder.objects.filter(financial_status='paid')
            if paid_orders.exists():
                for order in paid_orders[:5]:
                    self.stdout.write(
                        f'  • {order.name} - {order.customer_email} - '
                        f'{order.currency} {order.total_price:,.0f} - '
                        f'Convertida: {"Sí" if order.converted_to_invoice else "No"}'
                    )
                self.stdout.write(f'\nTotal órdenes pagadas: {paid_orders.count()}')
            else:
                self.stdout.write('  No hay órdenes pagadas')

        # 7. Convertir órdenes a facturas
        if not options.get('skip_conversion'):
            self.run_test(
                'Convertir Órdenes a Facturas SIFEN',
                lambda: call_command('shopify_convert_order_to_invoice', all_paid=True)
            )

        # Resumen final
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('TESTS COMPLETADOS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Estadísticas
        self.show_stats()

    def run_test(self, test_name, test_func):
        """Ejecuta un test individual con manejo de errores"""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('─' * 80))
        self.stdout.write(self.style.WARNING(f'TEST: {test_name}'))
        self.stdout.write(self.style.WARNING('─' * 80))

        try:
            test_func()
            self.stdout.write(self.style.SUCCESS(f'✓ {test_name} - OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ {test_name} - ERROR: {str(e)}'))
            logger.exception(f'Error en test: {test_name}')

    def show_stats(self):
        """Muestra estadísticas del sistema"""
        from am_shopify.models import ShopifyProduct, ShopifyOrder, ShopifyAccessToken, ShopifySyncLog

        self.stdout.write('ESTADÍSTICAS:')
        self.stdout.write('')

        # Tokens
        tokens = ShopifyAccessToken.objects.all()
        valid_tokens = [t for t in tokens if t.is_valid()]
        self.stdout.write(f'  Tokens: {tokens.count()} total, {len(valid_tokens)} válidos')

        # Productos
        products = ShopifyProduct.objects.all()
        test_products = products.filter(sku__startswith='TEST-SKU-')
        self.stdout.write(f'  Productos: {products.count()} total, {test_products.count()} de prueba')

        # Órdenes
        orders = ShopifyOrder.objects.all()
        paid_orders = orders.filter(financial_status='paid')
        converted_orders = orders.filter(converted_to_invoice=True)
        self.stdout.write(
            f'  Órdenes: {orders.count()} total, {paid_orders.count()} pagadas, '
            f'{converted_orders.count()} convertidas a factura'
        )

        # Logs
        logs = ShopifySyncLog.objects.all()
        success_logs = logs.filter(status='success')
        self.stdout.write(
            f'  Sincronizaciones: {logs.count()} total, {success_logs.count()} exitosas'
        )

        self.stdout.write('')
