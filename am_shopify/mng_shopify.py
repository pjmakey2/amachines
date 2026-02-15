from OptsIO.io_serial import IoS
from OptsIO import io_json
from django.forms import model_to_dict
from django.utils import timezone
from decimal import Decimal
from .models import ShopifyCustomer, ShopifyProduct, ShopifyOrder, ShopifyPayment
from .shopify_client import ShopifyAPIClient, extract_ruc_from_tags
from Sifen.models import Clientes, DocumentHeader, DocumentDetail, Producto, Distrito, Ciudades
from Sifen.mng_sifen import MSifen
from Sifen import mng_gmdata
import logging

logger = logging.getLogger(__name__)


class MShopify:
    """Métodos de backend para gestión de Shopify"""

    def __init__(self):
        self.client = ShopifyAPIClient()

    # ==================== SINCRONIZACIÓN ====================

    def sync_customers_from_ui(self, *args, **kwargs) -> tuple:
        """Sincroniza clientes desde la UI"""
        try:
            stats = self.client.sync_customers()
            msg = (
                f"Sincronización completada:\n"
                f"- Creados: {stats['created']}\n"
                f"- Actualizados: {stats['updated']}\n"
                f"- Errores: {stats['errors']}"
            )
            return {'success': msg}, args, kwargs
        except Exception as e:
            return {'error': f'Error en sincronización: {str(e)}'}, args, kwargs

    def sync_products_from_ui(self, *args, **kwargs) -> tuple:
        """Sincroniza productos desde la UI"""
        try:
            stats = self.client.sync_products()
            msg = (
                f"Sincronización completada:\n"
                f"- Creados: {stats['created']}\n"
                f"- Actualizados: {stats['updated']}\n"
                f"- Errores: {stats['errors']}"
            )
            return {'success': msg}, args, kwargs
        except Exception as e:
            return {'error': f'Error en sincronización: {str(e)}'}, args, kwargs

    def sync_orders_from_ui(self, *args, **kwargs) -> tuple:
        """Sincroniza órdenes desde la UI"""
        try:
            stats = self.client.sync_orders()
            msg = (
                f"Sincronización completada:\n"
                f"- Creados: {stats['created']}\n"
                f"- Actualizados: {stats['updated']}\n"
                f"- Errores: {stats['errors']}"
            )
            return {'success': msg}, args, kwargs
        except Exception as e:
            return {'error': f'Error en sincronización: {str(e)}'}, args, kwargs

    def sync_payments_from_ui(self, *args, **kwargs) -> tuple:
        """Sincroniza pagos desde la UI"""
        try:
            stats = self.client.sync_paid_orders()
            msg = (
                f"Sincronización completada:\n"
                f"- Creados: {stats['created']}\n"
                f"- Actualizados: {stats['updated']}\n"
                f"- Errores: {stats['errors']}"
            )
            return {'success': msg}, args, kwargs
        except Exception as e:
            return {'error': f'Error en sincronización: {str(e)}'}, args, kwargs

    # ==================== MIGRACIÓN A SIFEN ====================

    def migrate_customers_to_sifen(self, *args, **kwargs) -> dict:
        """
        Migra clientes seleccionados de Shopify a SIFEN.

        Reglas:
        - Si RUC ya existe en SIFEN: NO actualizar (es contribuyente verificado)
        - Si shopify_id ya existe en pdv_codigo: NO duplicar
        - Si es RUC nuevo: Marcar como "NO CONTRIBUYENTE", B2C, tipo=3
        - cargado_usuario = "SHOPIFY"
        """
        q: dict = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        ids = io_json.from_json(q.get('ids'))
        dbcon = q.get('dbcon', 'default')
        msgs = []

        for pk in ids:
            try:
                shopify_customer = ShopifyCustomer.objects.get(pk=pk)

                # Extraer RUC de tags
                ruc = extract_ruc_from_tags(shopify_customer.tags)

                # Verificar si RUC ya existe (contribuyente verificado)
                if ruc:
                    existing_by_ruc = Clientes.objects.using(dbcon).filter(pdv_ruc=ruc).first()
                    if existing_by_ruc:
                        msgs.append({
                            'info': f'Cliente {shopify_customer.full_name} ya existe con RUC {ruc}'
                        })
                        continue

                # Verificar si ya existe por shopify_id (pdv_codigo)
                existing_by_codigo = Clientes.objects.using(dbcon).filter(pdv_codigo=shopify_customer.shopify_id).first()
                if existing_by_codigo:
                    msgs.append({
                        'info': f'Cliente {shopify_customer.full_name} ya existe (pdv_codigo={shopify_customer.shopify_id})'
                    })
                    continue

                # Preparar datos del cliente
                cliente_data = {
                    'pdv_innominado': False if ruc else True,
                    'pdv_pais_cod': 'PRY',
                    'pdv_pais': 'Paraguay',
                    'pdv_tipocontribuyente': '3',  # No Contribuyente (B2C)
                    'pdv_es_contribuyente': False,
                    'pdv_type_business': 'B2C',
                    'pdv_codigo': shopify_customer.shopify_id,
                    'pdv_ruc': ruc or '0',
                    'pdv_ruc_dv': 0,
                    'pdv_nombrefantasia': shopify_customer.full_name or 'Sin Nombre',
                    'pdv_nombrefactura': shopify_customer.full_name or 'Sin Nombre',
                    'pdv_direccion_entrega': shopify_customer.default_address_address1 or '',
                    'pdv_numero_casa': 0,
                    'pdv_dpto_cod': 1,
                    'pdv_dpto_nombre': 'CAPITAL',
                    'pdv_distrito_cod': 1,
                    'pdv_distrito_nombre': shopify_customer.default_address_province or 'ASUNCION',
                    'pdv_ciudad_cod': 1,
                    'pdv_ciudad_nombre': shopify_customer.default_address_city or 'ASUNCION',
                    'pdv_telefono': shopify_customer.phone or '',
                    'pdv_celular': shopify_customer.phone or '',
                    'pdv_email': shopify_customer.email or '',
                    'cargado_usuario': 'SHOPIFY',
                }

                # Crear cliente
                Clientes.objects.using(dbcon).create(**cliente_data)
                msgs.append({
                    'success': f'Cliente {shopify_customer.full_name} migrado exitosamente'
                })

            except Exception as e:
                msgs.append({
                    'error': f'Error migrando cliente {pk}: {str(e)}'
                })
                logger.error(f"Error migrando cliente {pk}: {str(e)}")

        return {'msgs': msgs}

    def migrate_payments_to_invoices(self, *args, **kwargs) -> dict:
        """
        Migra pagos seleccionados a facturas SIFEN (DocumentHeader).

        Usa MSifen.create_documentheader para crear la factura usando
        el proceso de validación existente.
        """
        q: dict = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        ids = io_json.from_json(q.get('ids'))
        dbcon = q.get('dbcon', 'default')
        msgs = []

        # Instanciar MSifen
        msifen = MSifen()

        for pk in ids:
            try:
                payment = ShopifyPayment.objects.get(pk=pk)

                # Verificar si ya fue convertido
                if payment.is_converted:
                    msgs.append({
                        'info': f'Pago {payment.order_name} ya fue convertido'
                    })
                    continue

                # Verificar si ya existe factura con este ext_link
                existing_doc = DocumentHeader.objects.filter(
                    ext_link=payment.shopify_order_id
                ).first()
                if existing_doc:
                    payment.conversion_status = 'skipped'
                    payment.conversion_error = f'Ya existe factura con ext_link={payment.shopify_order_id}'
                    payment.document_header = existing_doc
                    payment.save()
                    msgs.append({
                        'info': f'Pago {payment.order_name} ya tiene factura asociada'
                    })
                    continue

                # Preparar datos del cliente
                # Valores por defecto para campos que no pueden estar vacíos
                nombre = payment.customer_full_name or 'Sin Nombre'
                telefono = payment.customer_phone or '00000'
                email = payment.customer_email or 'nomail@nomail.com'
                direccion = 'ND'

                # Extraer dirección del shipping_address si existe
                shipping = payment.shipping_address
                if shipping:
                    direccion = (shipping.get('address1', '') or 'ND')[:200] or 'ND'

                # Obtener ubicación desde la DB (default: ASUNCION)
                distobj = Distrito.objects.filter(nombre_distrito='ASUNCION (DISTRITO)').first()
                ciudadobj = Ciudades.objects.filter(distritoobj=distobj).first() if distobj else None

                # Valores de ubicación
                pdv_dpto_cod = distobj.dptoobj.codigo_departamento if distobj else 1
                pdv_dpto_nombre = distobj.dptoobj.nombre_departamento if distobj else 'CAPITAL'
                pdv_distrito_cod = distobj.codigo_distrito if distobj else 1
                pdv_distrito_nombre = distobj.nombre_distrito if distobj else 'ASUNCION (DISTRITO)'
                pdv_ciudad_cod = ciudadobj.codigo_ciudad if ciudadobj else 1
                pdv_ciudad_nombre = ciudadobj.nombre_ciudad if ciudadobj else 'ASUNCION (DISTRITO)'

                # Extraer RUC de customer_tags
                try:
                    ruc = extract_ruc_from_tags(payment.customer_tags)
                except:
                    ruc = None

                # Buscar si el RUC existe en Clientes
                clienteobj = None
                ruc_cargado = False
                if ruc and ruc != '0':
                    msifen.validate_ruc(qdict={'ruc': ruc})
                    clienteobj = Clientes.objects.filter(pdv_ruc=ruc).first()
                    ruc_cargado = True
                    if clienteobj:
                        pdv_tipocontribuyente =  str(clienteobj.pdv_tipocontribuyente)
                        pdv_es_contribuyente =  clienteobj.pdv_es_contribuyente
                        pdv_type_business =  clienteobj.pdv_type_business or 'B2C'
                        pdv_ruc_dv = clienteobj.pdv_ruc_dv or 0
                        pdv_nombrefantasia = clienteobj.pdv_nombrefantasia or nombre[:300]
                        pdv_nombrefactura = clienteobj.pdv_nombrefactura or nombre[:300]
                    else:
                        gdata = mng_gmdata.Gdata()
                        pdv_tipocontribuyente =  3
                        pdv_es_contribuyente =  False
                        pdv_type_business =  'B2C'
                        pdv_ruc_dv = gdata.calculate_dv(ruc)
                        pdv_nombrefantasia = nombre[:300]
                        pdv_nombrefactura = nombre[:300]

                # INNOMINADO = Sin RUC válido en Clientes (no importa si tiene nombre)
                if ruc_cargado:
                    # Cliente con RUC válido en DB → usar sus valores
                    send_save = False
                    if payment.financial_status == 'paid':
                        send_save = True
                    pdv_data = {
                        'pdv_innominado': False,
                        'pdv_pais_cod': 'PRY',
                        'pdv_pais': 'Paraguay',
                        'pdv_tipocontribuyente': pdv_tipocontribuyente,
                        'pdv_es_contribuyente': pdv_es_contribuyente,
                        'pdv_type_business': pdv_type_business,
                        'pdv_codigo': 0,
                        'pdv_ruc': ruc,
                        'pdv_ruc_dv': pdv_ruc_dv,
                        'pdv_nombrefantasia': pdv_nombrefantasia,
                        'pdv_nombrefactura': pdv_nombrefactura,
                        'pdv_direccion_entrega': direccion,
                        'pdv_numero_casa': 0,
                        'pdv_dpto_cod': pdv_dpto_cod,
                        'pdv_dpto_nombre': pdv_dpto_nombre,
                        'pdv_distrito_cod': pdv_distrito_cod,
                        'pdv_distrito_nombre': pdv_distrito_nombre,
                        'pdv_ciudad_cod': pdv_ciudad_cod,
                        'pdv_ciudad_nombre': pdv_ciudad_nombre,
                        'pdv_telefono': telefono,
                        'pdv_celular': telefono,
                        'pdv_email': email,
                    }
                else:
                    # Sin RUC válido → INNOMINADO
                    send_save = False
                    pdv_data = {
                        'pdv_innominado': True,
                        'pdv_pais_cod': 'PRY',
                        'pdv_pais': 'Paraguay',
                        'pdv_tipocontribuyente': '3',
                        'pdv_es_contribuyente': False,
                        'pdv_type_business': 'B2C',
                        'pdv_codigo': 999,
                        'pdv_ruc': '0',
                        'pdv_ruc_dv': 0,
                        'pdv_nombrefantasia': 'Sin Nombre',
                        'pdv_nombrefactura': 'Sin Nombre',
                        'pdv_direccion_entrega': direccion,
                        'pdv_numero_casa': 0,
                        'pdv_dpto_cod': pdv_dpto_cod,
                        'pdv_dpto_nombre': pdv_dpto_nombre,
                        'pdv_distrito_cod': pdv_distrito_cod,
                        'pdv_distrito_nombre': pdv_distrito_nombre,
                        'pdv_ciudad_cod': pdv_ciudad_cod,
                        'pdv_ciudad_nombre': pdv_ciudad_nombre,
                        'pdv_telefono': telefono,
                        'pdv_celular': telefono,
                        'pdv_email': email,
                    }
                # Preparar detalles (line_items) con descuento por ítem
                details = []
                for idx, item in enumerate(payment.line_items, start=1):
                    item_price = Decimal(str(item.get('price', 0)))
                    item_qty = Decimal(str(item.get('quantity', 1)))
                    # Usar los últimos 6 dígitos del ID de Shopify como prod_cod
                    item_id = str(item.get('id', 0))
                    prod_cod = int(item_id[-6:]) if item_id else 999000 + idx

                    # Obtener descuento específico del ítem desde discount_allocations
                    discount_allocations = item.get('discount_allocations', [])
                    item_discount = sum(Decimal(str(d.get('amount', 0))) for d in discount_allocations)

                    # Calcular bruto y porcentaje de descuento
                    bruto = item_price * item_qty
                    per_descuento = float(item_discount / bruto * 100) if bruto > 0 and item_discount > 0 else 0

                    details.append({
                        'prod_cod': prod_cod,
                        'prod_descripcion': (item.get('title', 'Producto') or 'Producto')[:500],
                        'precio_unitario': float(item_price),
                        'cantidad': float(item_qty),
                        'prod_unidad_medida_desc': '77',
                        'prod_unidad_medida_desc_text': 'UNI',
                        'exenta': 0,
                        'g5': 0,
                        'g10': 100,
                        'descuento': float(item_discount),
                        'per_descuento': per_descuento,
                        'descuento_global_item': 0,
                    })

                # Agregar shipping como ítem adicional (sin descuento)
                total_shipping = Decimal(str(payment.total_shipping or 0))
                if total_shipping > 0:
                    details.append({
                        'prod_cod': 999999,
                        'prod_descripcion': 'Envío / Shipping',
                        'precio_unitario': float(total_shipping),
                        'cantidad': 1,
                        'prod_unidad_medida_desc': '77',
                        'prod_unidad_medida_desc_text': 'UNI',
                        'exenta': 0,
                        'g5': 0,
                        'g10': 100,
                        'descuento': 0,
                        'per_descuento': 0,
                        'descuento_global_item': 0,
                    })

                # Preparar uc_fields para create_documentheader
                uc_fields = {
                    **pdv_data,
                    'doc_tipo': 'FE',
                    'doc_tipo_cod': '1',
                    'doc_tipo_desc': 'Factura electrónica',
                    'doc_op': 'VTA',
                    'doc_motivo': 'VTA',
                    'doc_moneda': 'GS',
                    'doc_tipo_ope': 1,
                    'doc_tipo_ope_desc': 'Venta de mercadería',
                    'doc_cre_tipo': 1,
                    'doc_tipo_pago_cod': 1,
                    'doc_tipo_pago': 'Efectivo',
                    'observacion': f'Orden Shopify: {payment.order_name}',
                    'details': details,
                    'send_save': send_save,
                }

                # Llamar a create_documentheader
                result, _, _ = msifen.create_documentheader(
                    userobj=userobj,
                    qdict={
                        'dbcon': dbcon,
                        'uc_fields': io_json.to_json(uc_fields),

                    }
                )

                if result.get('success'):
                    # Obtener el DocumentHeader creado y actualizar source/ext_link
                    record_id = result.get('record_id')
                    docobj = DocumentHeader.objects.get(pk=record_id)
                    docobj.source = 'SHOPIFY'
                    docobj.ext_link = payment.shopify_order_id
                    docobj.save()

                    # Actualizar el ShopifyPayment
                    payment.conversion_status = 'converted'
                    payment.conversion_error = ''
                    payment.document_header = docobj
                    payment.converted_at = timezone.now()
                    payment.save()

                    msgs.append({
                        'success': f'Pago {payment.order_name} convertido a factura #{docobj.doc_numero}'
                    })
                else:
                    payment.conversion_status = 'error'
                    payment.conversion_error = result.get('error', 'Error desconocido')[:500]
                    payment.save()
                    msgs.append({
                        'error': f'Error al convertir pago {payment.order_name}: {result.get("error")}'
                    })

            except Exception as e:
                # Marcar como error
                try:
                    payment = ShopifyPayment.objects.get(pk=pk)
                    payment.conversion_status = 'error'
                    payment.conversion_error = str(e)[:500]
                    payment.save()
                except:
                    pass
                msgs.append({
                    'error': f'Error migrando pago {pk}: {str(e)}'
                })
                logger.error(f"Error migrando pago {pk}: {str(e)}")

        return {'msgs': msgs}

    def migrate_products_to_sifen(self, *args, **kwargs) -> dict:
        """
        Migra productos seleccionados de Shopify a SIFEN.

        Reglas:
        - Verificar por EAN (código de barras) primero
        - Si no tiene EAN, verificar por descripción exacta
        - Si existe: Actualizar precio e inventario
        - Si es nuevo: Crear producto
        - cargado_usuario = "SHOPIFY"
        """
        q: dict = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        ids = io_json.from_json(q.get('ids'))
        dbcon = q.get('dbcon', 'default')
        msgs = []

        for pk in ids:
            try:
                shopify_product = ShopifyProduct.objects.get(pk=pk)

                # Buscar por EAN (código de barras) primero
                existing = None
                if shopify_product.barcode:
                    existing = Producto.objects.using(dbcon).filter(ean=shopify_product.barcode).first()

                # Si no encontró por EAN, buscar por descripción exacta (solo productos de SHOPIFY)
                if not existing:
                    existing = Producto.objects.using(dbcon).filter(
                        descripcion=shopify_product.title[:300],
                        cargado_usuario='SHOPIFY'
                    ).first()

                if existing:
                    # Actualizar precio y stock
                    existing.precio = shopify_product.price
                    existing.stock = shopify_product.inventory_quantity
                    existing.actualizado_usuario = 'SHOPIFY'
                    existing.save()
                    msgs.append({
                        'info': f'Producto {shopify_product.title} actualizado (ID: {existing.id})'
                    })
                else:
                    # Crear nuevo producto
                    producto_data = {
                        'descripcion': shopify_product.title[:300],
                        'ean': shopify_product.barcode or '',
                        'precio': shopify_product.price,
                        'stock': shopify_product.inventory_quantity,
                        'moneda': 'PYG',
                        'activo': shopify_product.status == 'active',
                        'cargado_usuario': 'SHOPIFY',
                    }

                    nuevo = Producto.objects.using(dbcon).create(**producto_data)
                    msgs.append({
                        'success': f'Producto {shopify_product.title} creado (ID: {nuevo.id})'
                    })

            except Exception as e:
                msgs.append({
                    'error': f'Error migrando producto {pk}: {str(e)}'
                })
                logger.error(f"Error migrando producto {pk}: {str(e)}")

        return {'msgs': msgs}
