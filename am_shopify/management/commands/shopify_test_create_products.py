"""
Management command para crear productos de prueba en Shopify
"""
from django.core.management.base import BaseCommand
from am_shopify.managers import ProductManager
import logging
import random

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Crea 10 productos de prueba en Shopify'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Número de productos a crear (default: 10)'
        )

    def handle(self, *args, **options):
        count = options['count']

        self.stdout.write(self.style.WARNING(f'Creando {count} productos de prueba en Shopify...'))

        # Datos aleatorios para productos
        product_names = [
            'Impresora 3D Ender',
            'Filamento PLA Premium',
            'Boquilla de Latón',
            'Cama Caliente Magnética',
            'Motor Paso a Paso NEMA 17',
            'Extrusor de Metal',
            'Kit de Herramientas',
            'Rodamiento Lineal',
            'Correa GT2',
            'Ventilador Radial',
            'Placa Controladora',
            'Sensor de Nivelación',
            'Pantalla LCD Touch',
            'Fuente de Poder 24V',
            'Cable de Silicona',
            'Resina UV Transparente',
            'Alcohol Isopropílico',
            'Guantes de Nitrilo',
            'Espátula Metálica',
            'Pinzas de Precisión'
        ]

        product_types = [
            'Impresoras 3D',
            'Filamentos',
            'Repuestos',
            'Accesorios',
            'Electrónica',
            'Herramientas',
            'Consumibles',
            'Kits'
        ]

        vendors = [
            'Creality',
            'Prusa Research',
            'Anycubic',
            'Elegoo',
            'AltaMachines',
            'Sovol',
            'Artillery',
            'Longer'
        ]

        descriptions = [
            'Producto de alta calidad, ideal para impresión 3D profesional.',
            'Compatible con la mayoría de impresoras FDM del mercado.',
            'Fabricado con materiales premium para máxima durabilidad.',
            'Fácil instalación y configuración. Incluye manual en español.',
            'Diseñado para obtener los mejores resultados en tus impresiones.',
            'Resistente y confiable, probado en miles de horas de uso.',
            'Excelente relación calidad-precio. Stock limitado.',
            'Tecnología de última generación para makers y profesionales.',
            'Garantía de 12 meses. Soporte técnico incluido.',
            'Ideal para principiantes y usuarios avanzados.'
        ]

        # URLs de imágenes placeholder (usando picsum.photos para imágenes aleatorias)
        image_urls = [
            f'https://picsum.photos/seed/{random.randint(1, 1000)}/800/800',
            f'https://picsum.photos/seed/{random.randint(1001, 2000)}/800/800',
            f'https://picsum.photos/seed/{random.randint(2001, 3000)}/800/800',
            f'https://picsum.photos/seed/{random.randint(3001, 4000)}/800/800',
            f'https://picsum.photos/seed/{random.randint(4001, 5000)}/800/800',
        ]

        manager = ProductManager()
        created = 0
        errors = 0

        for i in range(1, count + 1):
            # Seleccionar datos aleatorios
            name = random.choice(product_names)
            product_type = random.choice(product_types)
            vendor = random.choice(vendors)
            description = random.choice(descriptions)
            image = random.choice(image_urls)

            # Precio aleatorio entre 50,000 y 500,000 PYG
            price = random.randint(5, 50) * 10000

            # Inventario aleatorio entre 5 y 100
            inventory = random.randint(5, 100)

            product_data = {
                'title': f'{name} #{i}',
                'body_html': f'<p><strong>{name}</strong></p><p>{description}</p><p>Producto de prueba generado automáticamente.</p>',
                'vendor': vendor,
                'product_type': product_type,
                'status': 'draft',  # Crear como draft para no publicar en la tienda
                'tags': 'test, prueba, automatico',
                'variants': [
                    {
                        'price': f'{price}',
                        'sku': f'TEST-SKU-{i:03d}',
                        'barcode': f'7501234567{i:03d}',
                        'inventory_quantity': inventory,
                        'inventory_management': 'shopify',
                    }
                ],
                'images': [
                    {
                        'src': image,
                        'alt': f'Imagen de {name}'
                    }
                ]
            }

            try:
                product = manager.create_product(product_data)
                if product:
                    created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Producto {i}/{count} creado: {product.title} '
                            f'(ID: {product.shopify_id}, SKU: {product.sku})'
                        )
                    )
                else:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error al crear producto {i}/{count}')
                    )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Excepción al crear producto {i}/{count}: {str(e)}')
                )
                logger.exception(f'Error creando producto de prueba {i}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Creados: {created}'))
        if errors:
            self.stdout.write(self.style.ERROR(f'Errores: {errors}'))

        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'NOTA: Los productos fueron creados como "draft" para no publicarlos automáticamente. '
                'Puedes cambiarlos a "active" desde el admin de Shopify.'
            )
        )
