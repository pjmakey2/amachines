"""
Management command para actualizar inventario de productos en Shopify
"""
from django.core.management.base import BaseCommand
from am_shopify.models import ShopifyProduct
from am_shopify.managers import ProductManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Actualiza el inventario de productos en Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sku',
            type=str,
            help='SKU del producto a actualizar (opcional)'
        )
        parser.add_argument(
            '--quantity',
            type=int,
            default=100,
            help='Nueva cantidad de inventario (default: 100)'
        )
        parser.add_argument(
            '--test-products',
            action='store_true',
            help='Actualizar solo productos de prueba (con tag "test")'
        )

    def handle(self, *args, **options):
        sku = options.get('sku')
        quantity = options['quantity']
        test_only = options.get('test_products', False)

        manager = ProductManager()

        if sku:
            # Actualizar producto específico por SKU
            try:
                product = ShopifyProduct.objects.get(sku=sku)
                self.stdout.write(f'Actualizando inventario de {product.title} (SKU: {sku})...')

                success = manager.update_inventory(product.shopify_id, quantity)

                if success:
                    product.refresh_from_db()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Inventario actualizado: {product.title} - '
                            f'Nueva cantidad: {product.inventory_quantity}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error al actualizar inventario de {product.title}')
                    )
            except ShopifyProduct.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ No se encontró producto con SKU: {sku}')
                )
        else:
            # Actualizar múltiples productos
            if test_only:
                products = ShopifyProduct.objects.filter(sku__startswith='TEST-SKU-')
                self.stdout.write(f'Actualizando inventario de {products.count()} productos de prueba...')
            else:
                products = ShopifyProduct.objects.all()[:10]
                self.stdout.write(f'Actualizando inventario de los primeros {products.count()} productos...')

            updated = 0
            errors = 0

            for product in products:
                try:
                    success = manager.update_inventory(product.shopify_id, quantity)
                    if success:
                        product.refresh_from_db()
                        updated += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ {product.title} (SKU: {product.sku}) - '
                                f'Nuevo inventario: {product.inventory_quantity}'
                            )
                        )
                    else:
                        errors += 1
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error: {product.title}')
                        )
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Excepción en {product.title}: {str(e)}')
                    )
                    logger.exception(f'Error actualizando inventario de {product.shopify_id}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Actualizados: {updated}'))
            if errors:
                self.stdout.write(self.style.ERROR(f'Errores: {errors}'))
