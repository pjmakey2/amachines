"""
Management command para actualizar descripción y código de barra de productos en Shopify
"""
from django.core.management.base import BaseCommand
from am_shopify.models import ShopifyProduct
from am_shopify.managers import ProductManager
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Actualiza descripción y/o código de barra de productos en Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sku',
            type=str,
            help='SKU del producto a actualizar (opcional)'
        )
        parser.add_argument(
            '--description',
            type=str,
            help='Nueva descripción del producto'
        )
        parser.add_argument(
            '--barcode',
            type=str,
            help='Nuevo código de barras (EAN)'
        )
        parser.add_argument(
            '--test-products',
            action='store_true',
            help='Actualizar solo productos de prueba (con SKU TEST-SKU-*)'
        )

    def handle(self, *args, **options):
        sku = options.get('sku')
        description = options.get('description')
        barcode = options.get('barcode')
        test_only = options.get('test_products', False)

        if not description and not barcode:
            self.stdout.write(
                self.style.ERROR('Debes especificar al menos --description o --barcode')
            )
            return

        manager = ProductManager()

        if sku:
            # Actualizar producto específico
            try:
                product = ShopifyProduct.objects.get(sku=sku)
                self.stdout.write(f'Actualizando {product.title} (SKU: {sku})...')

                update_data = {}
                if description:
                    update_data['body_html'] = f'<p>{description}</p>'

                # Actualizar producto
                if update_data:
                    success = manager.update_product(product.shopify_id, update_data)
                    if success:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Descripción actualizada')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'✗ Error al actualizar descripción')
                        )

                # Actualizar barcode en la variante
                if barcode:
                    from am_shopify.shopify_client import ShopifyAPIClient
                    client = ShopifyAPIClient()

                    # Obtener el producto completo para acceder a las variantes
                    product_data = client.get_product(product.shopify_id)
                    if product_data and 'variants' in product_data:
                        variant = product_data['variants'][0]  # Primera variante
                        variant_id = variant['id']

                        variant_update = {'barcode': barcode}
                        variant_result = client.update_variant(variant_id, variant_update)

                        if variant_result:
                            self.stdout.write(
                                self.style.SUCCESS(f'✓ Código de barras actualizado: {barcode}')
                            )
                            # Actualizar en BD local
                            product.barcode = barcode
                            product.save()
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'✗ Error al actualizar código de barras')
                            )

                product.refresh_from_db()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Producto actualizado: {product.title}')
                )

            except ShopifyProduct.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ No se encontró producto con SKU: {sku}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error: {str(e)}')
                )
                logger.exception(f'Error actualizando producto {sku}')
        else:
            # Actualizar múltiples productos
            if test_only:
                products = ShopifyProduct.objects.filter(sku__startswith='TEST-SKU-')
                self.stdout.write(f'Actualizando {products.count()} productos de prueba...')
            else:
                products = ShopifyProduct.objects.all()[:5]
                self.stdout.write(f'Actualizando los primeros {products.count()} productos...')

            updated = 0
            errors = 0

            for i, product in enumerate(products, 1):
                try:
                    update_data = {}
                    new_barcode = None

                    if description:
                        desc = f'{description} (actualizado producto #{i})'
                        update_data['body_html'] = f'<p>{desc}</p>'

                    if barcode:
                        # Generar código de barras único para cada producto
                        new_barcode = f'{barcode}{i:04d}'

                    # Actualizar producto
                    if update_data:
                        success = manager.update_product(product.shopify_id, update_data)
                        if not success:
                            errors += 1
                            continue

                    # Actualizar barcode
                    if new_barcode:
                        from am_shopify.shopify_client import ShopifyAPIClient
                        client = ShopifyAPIClient()

                        product_data = client.get_product(product.shopify_id)
                        if product_data and 'variants' in product_data:
                            variant = product_data['variants'][0]
                            variant_id = variant['id']
                            variant_update = {'barcode': new_barcode}
                            variant_result = client.update_variant(variant_id, variant_update)

                            if variant_result:
                                product.barcode = new_barcode
                                product.save()

                    updated += 1
                    product.refresh_from_db()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {product.title} (SKU: {product.sku})'
                            + (f' - Barcode: {product.barcode}' if new_barcode else '')
                        )
                    )

                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error en {product.title}: {str(e)}')
                    )
                    logger.exception(f'Error actualizando {product.shopify_id}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Actualizados: {updated}'))
            if errors:
                self.stdout.write(self.style.ERROR(f'Errores: {errors}'))
