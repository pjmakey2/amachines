"""
Management command para convertir órdenes de Shopify a facturas SIFEN (DocumentHeader)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from am_shopify.models import ShopifyOrder
from Sifen.models import DocumentHeader, Clientes
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Convierte órdenes pagadas de Shopify a facturas SIFEN (DocumentHeader)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='ID de la orden de Shopify a convertir (opcional)'
        )
        parser.add_argument(
            '--all-paid',
            action='store_true',
            help='Convertir todas las órdenes pagadas que no han sido convertidas'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar conversión aunque ya exista factura'
        )

    def handle(self, *args, **options):
        order_id = options.get('order_id')
        all_paid = options.get('all_paid', False)
        force = options.get('force', False)

        if order_id:
            # Convertir orden específica
            try:
                order = ShopifyOrder.objects.get(shopify_id=order_id)
                self.convert_order(order, force)
            except ShopifyOrder.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'✗ No se encontró orden con ID: {order_id}')
                )
        elif all_paid:
            # Convertir todas las órdenes pagadas no convertidas
            if force:
                orders = ShopifyOrder.objects.filter(financial_status='paid')
            else:
                orders = ShopifyOrder.objects.filter(
                    financial_status='paid',
                    converted_to_invoice=False
                )

            self.stdout.write(f'Encontradas {orders.count()} órdenes pagadas para convertir...')

            converted = 0
            errors = 0

            for order in orders:
                try:
                    if self.convert_order(order, force):
                        converted += 1
                    else:
                        errors += 1
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error en orden {order.name}: {str(e)}')
                    )
                    logger.exception(f'Error convirtiendo orden {order.shopify_id}')

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(f'Convertidas: {converted}'))
            if errors:
                self.stdout.write(self.style.ERROR(f'Errores: {errors}'))
        else:
            self.stdout.write(
                self.style.ERROR('Debes especificar --order-id o --all-paid')
            )

    def convert_order(self, order, force=False):
        """
        Convierte una orden de Shopify a DocumentHeader de SIFEN
        Retorna True si se convirtió exitosamente, False si no
        """
        # Verificar si ya fue convertida
        if order.converted_to_invoice and not force:
            self.stdout.write(
                self.style.WARNING(f'○ Orden {order.name} ya fue convertida a factura')
            )
            return False

        # Verificar que la orden esté pagada
        if not order.is_paid:
            self.stdout.write(
                self.style.WARNING(
                    f'○ Orden {order.name} no está pagada (estado: {order.get_financial_status_display()})'
                )
            )
            return False

        # Verificar duplicado por ext_link
        existing = DocumentHeader.objects.filter(ext_link=order.shopify_id).first()
        if existing and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'○ Ya existe factura para orden {order.name} '
                    f'(DocumentHeader ID: {existing.id}, ext_link: {existing.ext_link})'
                )
            )
            # Vincular si no estaba vinculada
            if not order.document_header:
                order.document_header = existing
                order.converted_to_invoice = True
                order.save()
            return False

        try:
            with transaction.atomic():
                # Buscar o crear cliente
                cliente = self.get_or_create_cliente(order)

                # Crear DocumentHeader
                doc = DocumentHeader()
                doc.doc_fecha = order.created_at_shopify.date() if order.created_at_shopify else None
                doc.doc_numero = 0  # Se asignará automáticamente por SIFEN
                doc.doc_tipo = 1  # Factura
                doc.doc_condicion = 1  # Contado (la mayoría de Shopify son contado)

                # Cliente
                doc.doc_cliente = cliente

                # Montos
                doc.doc_total_bruto = order.subtotal_price
                doc.doc_descuento_global = order.total_discounts
                doc.doc_total_iva = order.total_tax
                doc.doc_total_neto = order.total_price

                # Moneda
                if order.currency == 'PYG':
                    doc.doc_moneda = 1  # PYG
                elif order.currency == 'USD':
                    doc.doc_moneda = 2  # USD
                else:
                    doc.doc_moneda = 1  # Default PYG

                # Observaciones
                doc.doc_obs = f'Orden Shopify: {order.name}'
                if order.note:
                    doc.doc_obs += f'\n{order.note}'

                # Enlace externo - IMPORTANTE para evitar duplicados
                doc.ext_link = order.shopify_id

                # Estado inicial
                doc.ek_estado = None  # Pendiente de envío a SIFEN

                doc.save()

                # Vincular orden con factura
                order.document_header = doc
                order.converted_to_invoice = True
                order.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Orden {order.name} convertida a DocumentHeader (ID: {doc.id})\n'
                        f'  Cliente: {cliente.pdv_nombre_fantasia}\n'
                        f'  Total: {order.currency} {order.total_price:,.0f}\n'
                        f'  ext_link: {doc.ext_link}'
                    )
                )

                return True

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error al convertir orden {order.name}: {str(e)}')
            )
            logger.exception(f'Error convirtiendo orden {order.shopify_id} a DocumentHeader')
            return False

    def get_or_create_cliente(self, order):
        """
        Busca o crea un cliente basado en los datos de la orden de Shopify
        """
        # Buscar por email
        if order.customer_email:
            cliente = Clientes.objects.filter(pdv_email=order.customer_email).first()
            if cliente:
                return cliente

        # Si no existe, crear nuevo cliente
        cliente = Clientes()

        # Nombre
        if order.customer_first_name or order.customer_last_name:
            nombre = f'{order.customer_first_name} {order.customer_last_name}'.strip()
            cliente.pdv_nombre_fantasia = nombre
            cliente.pdv_razon_social = nombre
        else:
            cliente.pdv_nombre_fantasia = order.customer_email or 'Cliente Shopify'
            cliente.pdv_razon_social = order.customer_email or 'Cliente Shopify'

        # Contacto
        cliente.pdv_email = order.customer_email or ''
        cliente.pdv_telefono = order.customer_phone or ''

        # Tipo de cliente (B2C por defecto para Shopify)
        cliente.pdv_type_business = 'B2C'
        cliente.pdv_tipocontribuyente = 3  # No contribuyente
        cliente.pdv_es_contribuyente = False

        # RUC innominado
        cliente.pdv_innominado = True
        cliente.pdv_ruc = '0'
        cliente.pdv_ruc_dv = '0'

        cliente.save()

        self.stdout.write(
            self.style.SUCCESS(f'  → Cliente creado: {cliente.pdv_nombre_fantasia}')
        )

        return cliente
