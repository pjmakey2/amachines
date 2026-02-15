import requests
import logging
from django.conf import settings
from .services import ShopifyTokenService

logger = logging.getLogger(__name__)


class ShopifyAPIClient:
    """
    Cliente para interactuar con la API de Shopify
    """
    
    API_VERSION = '2024-10'
    
    def __init__(self, store_name=None):
        if not store_name:
            self.store_name = settings.SHOPIFY_STORE.replace('.myshopify.com', '').replace('https://', '').replace('http://', '')
        else:
            self.store_name = store_name
        
        self.base_url = f"https://{self.store_name}.myshopify.com/admin/api/{self.API_VERSION}"
        self.token_service = ShopifyTokenService()
    
    def _get_headers(self):
        """Obtiene los headers con el token de acceso"""
        token = self.token_service.get_valid_token()
        return {
            'X-Shopify-Access-Token': token,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, params=None, data=None):
        """Realiza una petición a la API de Shopify"""
        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error en {endpoint}: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en petición a {endpoint}: {str(e)}")
            raise
    
    # ==================== PRODUCTOS ====================
    
    def get_products(self, limit=50, page_info=None, **filters):
        """
        Obtiene productos de Shopify
        
        Args:
            limit: Número de productos por página (máx 250)
            page_info: Token de paginación
            **filters: Filtros adicionales (status, ids, etc.)
        """
        params = {'limit': min(limit, 250)}
        params.update(filters)
        
        if page_info:
            params['page_info'] = page_info
        
        return self._make_request('GET', 'products.json', params=params)
    
    def get_product(self, product_id):
        """Obtiene un producto específico por ID"""
        return self._make_request('GET', f'products/{product_id}.json')
    
    def create_product(self, product_data):
        """
        Crea un nuevo producto en Shopify
        
        Args:
            product_data: Diccionario con los datos del producto
                {
                    "title": "Nombre del producto",
                    "body_html": "Descripción HTML",
                    "vendor": "Fabricante",
                    "product_type": "Tipo",
                    "variants": [{
                        "price": "100.00",
                        "sku": "SKU123",
                        "barcode": "123456789",
                        "inventory_quantity": 10
                    }],
                    "images": [{
                        "src": "https://example.com/image.jpg"
                    }]
                }
        """
        data = {'product': product_data}
        return self._make_request('POST', 'products.json', data=data)
    
    def update_product(self, product_id, product_data):
        """Actualiza un producto existente"""
        data = {'product': product_data}
        return self._make_request('PUT', f'products/{product_id}.json', data=data)
    
    def delete_product(self, product_id):
        """Elimina un producto"""
        return self._make_request('DELETE', f'products/{product_id}.json')
    
    # ==================== VARIANTES ====================
    
    def get_variant(self, variant_id):
        """Obtiene una variante específica"""
        return self._make_request('GET', f'variants/{variant_id}.json')
    
    def update_variant(self, variant_id, variant_data):
        """
        Actualiza una variante de producto
        
        Útil para actualizar precio, inventario, SKU, código de barras, etc.
        """
        data = {'variant': variant_data}
        return self._make_request('PUT', f'variants/{variant_id}.json', data=data)
    
    # ==================== INVENTARIO ====================
    
    def get_inventory_levels(self, inventory_item_ids=None, location_ids=None, limit=50):
        """Obtiene niveles de inventario"""
        params = {'limit': min(limit, 250)}
        
        if inventory_item_ids:
            params['inventory_item_ids'] = ','.join(map(str, inventory_item_ids))
        if location_ids:
            params['location_ids'] = ','.join(map(str, location_ids))
        
        return self._make_request('GET', 'inventory_levels.json', params=params)
    
    def set_inventory_level(self, inventory_item_id, location_id, available):
        """Establece el nivel de inventario"""
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available': available
        }
        return self._make_request('POST', 'inventory_levels/set.json', data=data)
    
    def adjust_inventory_level(self, inventory_item_id, location_id, available_adjustment):
        """Ajusta el nivel de inventario (incremento o decremento)"""
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available_adjustment': available_adjustment
        }
        return self._make_request('POST', 'inventory_levels/adjust.json', data=data)
    
    # ==================== ÓRDENES ====================
    
    def get_orders(self, limit=50, status='any', financial_status=None, fulfillment_status=None, **filters):
        """
        Obtiene órdenes de Shopify
        
        Args:
            limit: Número de órdenes por página
            status: 'open', 'closed', 'cancelled', 'any'
            financial_status: 'pending', 'authorized', 'paid', 'partially_paid', etc.
            fulfillment_status: 'shipped', 'partial', 'unshipped', 'unfulfilled', etc.
        """
        params = {
            'limit': min(limit, 250),
            'status': status
        }
        
        if financial_status:
            params['financial_status'] = financial_status
        if fulfillment_status:
            params['fulfillment_status'] = fulfillment_status
        
        params.update(filters)
        
        return self._make_request('GET', 'orders.json', params=params)
    
    def get_order(self, order_id):
        """Obtiene una orden específica por ID"""
        return self._make_request('GET', f'orders/{order_id}.json')
    
    def cancel_order(self, order_id, reason=None):
        """Cancela una orden"""
        data = {}
        if reason:
            data['reason'] = reason  # 'customer', 'fraud', 'inventory', 'declined', 'other'
        
        return self._make_request('POST', f'orders/{order_id}/cancel.json', data=data)
    
    # ==================== IMÁGENES ====================
    
    def get_product_images(self, product_id):
        """Obtiene las imágenes de un producto"""
        return self._make_request('GET', f'products/{product_id}/images.json')
    
    def create_product_image(self, product_id, image_data):
        """
        Crea una nueva imagen para un producto
        
        Args:
            image_data: {
                "src": "https://example.com/image.jpg",
                "position": 1,
                "alt": "Texto alternativo"
            }
        """
        data = {'image': image_data}
        return self._make_request('POST', f'products/{product_id}/images.json', data=data)
    
    def update_product_image(self, product_id, image_id, image_data):
        """Actualiza una imagen de producto"""
        data = {'image': image_data}
        return self._make_request('PUT', f'products/{product_id}/images/{image_id}.json', data=data)
    
    def delete_product_image(self, product_id, image_id):
        """Elimina una imagen de producto"""
        return self._make_request('DELETE', f'products/{product_id}/images/{image_id}.json')
    
    # ==================== LOCATIONS ====================
    
    def get_locations(self):
        """Obtiene todas las ubicaciones/locaciones de la tienda"""
        return self._make_request('GET', 'locations.json')
    
    # ==================== SHOP INFO ====================
    
    def get_shop_info(self):
        """Obtiene información de la tienda"""
        return self._make_request('GET', 'shop.json')
    
    # ==================== WEBHOOKS ====================
    
    def get_webhooks(self):
        """Obtiene todos los webhooks configurados"""
        return self._make_request('GET', 'webhooks.json')
    
    def create_webhook(self, topic, address, format='json'):
        """
        Crea un webhook
        
        Args:
            topic: 'orders/create', 'products/update', etc.
            address: URL donde se enviará el webhook
            format: 'json' o 'xml'
        """
        data = {
            'webhook': {
                'topic': topic,
                'address': address,
                'format': format
            }
        }
        return self._make_request('POST', 'webhooks.json', data=data)
    
    def delete_webhook(self, webhook_id):
        """Elimina un webhook"""
        return self._make_request('DELETE', f'webhooks/{webhook_id}.json')

    # ==================== PAGOS (Sincronización) ====================

    def sync_paid_orders(self, limit=50):
        """
        Sincroniza órdenes de Shopify al modelo ShopifyPayment.
        Importa todas las órdenes (pagadas y no pagadas).

        Returns:
            dict: Estadísticas de sincronización {created, updated, skipped, errors}
        """
        from .models import ShopifyPayment, ShopifySyncLog
        from dateutil import parser

        sync_log = ShopifySyncLog.objects.create(
            sync_type='payments',
            status='success'
        )

        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

        try:
            # Obtener todas las órdenes (sin filtro de financial_status)
            response = self.get_orders(limit=limit, status='any')
            orders = response.get('orders', [])

            logger.info(f"Sincronizando {len(orders)} órdenes desde Shopify")

            for order in orders:
                try:
                    shopify_order_id = order.get('id')

                    # Extraer información del cliente
                    customer = order.get('customer') or {}
                    customer_email = customer.get('email') or order.get('email') or ''
                    customer_phone = customer.get('phone') or order.get('phone') or ''
                    customer_first_name = customer.get('first_name', '') or ''
                    customer_last_name = customer.get('last_name', '') or ''

                    # Construir nombre completo
                    customer_name = f"{customer_first_name} {customer_last_name}".strip()

                    # Determinar si es innominado (sin datos de cliente identificables)
                    is_innominado = not customer_email and not customer_phone and not customer_name

                    # Extraer gateway de pago
                    gateways = order.get('payment_gateway_names', [])
                    payment_gateway = ', '.join(gateways) if gateways else 'unknown'

                    # Determinar método de pago (todo es cash porque no hay info de tarjeta)
                    payment_method = 'cash'

                    # Parsear fechas
                    order_created_at = parser.parse(order.get('created_at'))
                    order_processed_at = None
                    if order.get('processed_at'):
                        order_processed_at = parser.parse(order.get('processed_at'))

                    # Preparar datos
                    customer_tags = customer.get('tags', '') or ''

                    # Calcular total shipping desde shipping_lines
                    shipping_lines = order.get('shipping_lines', [])
                    total_shipping = sum(float(line.get('price', 0)) for line in shipping_lines)

                    payment_data = {
                        'order_number': order.get('order_number', 0),
                        'order_name': order.get('name', ''),
                        'customer_email': customer_email or None,
                        'customer_phone': customer_phone or None,
                        'customer_first_name': customer_first_name or None,
                        'customer_last_name': customer_last_name or None,
                        'customer_name': customer_name or None,
                        'customer_tags': customer_tags,
                        'is_innominado': is_innominado,
                        'total_price': order.get('total_price', 0),
                        'subtotal_price': order.get('subtotal_price', 0),
                        'total_tax': order.get('total_tax', 0),
                        'total_discounts': order.get('total_discounts', 0),
                        'total_shipping': total_shipping,
                        'currency': order.get('currency', 'PYG'),
                        'payment_gateway': payment_gateway,
                        'payment_method': payment_method,
                        'financial_status': order.get('financial_status', 'paid'),
                        'line_items': order.get('line_items', []),
                        'shipping_address': order.get('shipping_address') or {},
                        'billing_address': order.get('billing_address') or {},
                        'note': order.get('note', '') or '',
                        'tags': order.get('tags', '') or '',
                        'order_created_at': order_created_at,
                        'order_processed_at': order_processed_at,
                    }

                    # Crear o actualizar
                    payment_obj, created = ShopifyPayment.objects.update_or_create(
                        shopify_order_id=shopify_order_id,
                        defaults=payment_data
                    )

                    if created:
                        stats['created'] += 1
                        logger.info(f"✓ Pago creado: {payment_obj.order_name} - {payment_obj.customer_full_name}")
                    else:
                        stats['updated'] += 1
                        logger.debug(f"↻ Pago actualizado: {payment_obj.order_name}")

                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"✗ Error sincronizando orden {order.get('name')}: {str(e)}")

            sync_log.items_processed = len(orders)
            sync_log.items_created = stats['created']
            sync_log.items_updated = stats['updated']
            sync_log.items_failed = stats['errors']
            sync_log.complete(status='success' if stats['errors'] == 0 else 'partial')

            logger.info(f"Sincronización completada: {stats}")
            return stats

        except Exception as e:
            error_msg = f"Error en sincronización de pagos: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise

    def get_pending_payments_count(self):
        """Retorna el número de pagos pendientes de conversión"""
        from .models import ShopifyPayment
        return ShopifyPayment.objects.filter(conversion_status='pending').count()

    def get_payments_summary(self):
        """Retorna un resumen de todos los pagos"""
        from .models import ShopifyPayment
        from django.db.models import Count, Sum

        return {
            'total': ShopifyPayment.objects.count(),
            'pending': ShopifyPayment.objects.filter(conversion_status='pending').count(),
            'converted': ShopifyPayment.objects.filter(conversion_status='converted').count(),
            'errors': ShopifyPayment.objects.filter(conversion_status='error').count(),
            'skipped': ShopifyPayment.objects.filter(conversion_status='skipped').count(),
            'innominados': ShopifyPayment.objects.filter(is_innominado=True).count(),
            'total_amount': ShopifyPayment.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0,
        }

    # ==================== CLIENTES ====================

    def get_customers(self, limit=50, page_info=None, **filters):
        """
        Obtiene clientes de Shopify

        Args:
            limit: Número de clientes por página (máx 250)
            page_info: Token de paginación
            **filters: Filtros adicionales (ids, since_id, created_at_min, etc.)
        """
        params = {'limit': min(limit, 250)}
        params.update(filters)

        if page_info:
            params['page_info'] = page_info

        return self._make_request('GET', 'customers.json', params=params)

    def get_customer(self, customer_id):
        """Obtiene un cliente específico por ID"""
        return self._make_request('GET', f'customers/{customer_id}.json')

    def get_customer_orders(self, customer_id, limit=50):
        """Obtiene las órdenes de un cliente"""
        params = {'limit': min(limit, 250)}
        return self._make_request('GET', f'customers/{customer_id}/orders.json', params=params)

    def search_customers(self, query):
        """
        Busca clientes por email, nombre, etc.

        Args:
            query: Texto de búsqueda
        """
        params = {'query': query}
        return self._make_request('GET', 'customers/search.json', params=params)

    def sync_customers(self, limit=250):
        """
        Sincroniza TODOS los clientes de Shopify al modelo ShopifyCustomer.
        Guarda todos los datos disponibles sin importar si parecen relevantes.

        Args:
            limit: Número de clientes por página (máx 250)

        Returns:
            dict: Estadísticas de sincronización {created, updated, skipped, errors}
        """
        from .models import ShopifyCustomer, ShopifySyncLog
        from dateutil import parser
        from decimal import Decimal

        sync_log = ShopifySyncLog.objects.create(
            sync_type='customers',
            status='success'
        )

        stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        total_processed = 0

        try:
            # Obtener todos los clientes (paginado)
            page_info = None
            has_more = True

            while has_more:
                response = self.get_customers(limit=limit, page_info=page_info)
                customers = response.get('customers', [])

                if not customers:
                    break

                logger.info(f"Sincronizando {len(customers)} clientes desde Shopify")

                for customer in customers:
                    try:
                        shopify_id = customer.get('id')

                        # Parsear fechas
                        created_at_shopify = None
                        if customer.get('created_at'):
                            created_at_shopify = parser.parse(customer.get('created_at'))

                        updated_at_shopify = None
                        if customer.get('updated_at'):
                            updated_at_shopify = parser.parse(customer.get('updated_at'))

                        # Email marketing consent
                        email_consent = customer.get('email_marketing_consent') or {}
                        email_consent_state = email_consent.get('state', '')
                        email_consent_opt_in = email_consent.get('opt_in_level', '')
                        email_consent_updated = None
                        if email_consent.get('consent_updated_at'):
                            email_consent_updated = parser.parse(email_consent.get('consent_updated_at'))

                        # SMS marketing consent
                        sms_consent = customer.get('sms_marketing_consent') or {}
                        sms_consent_state = sms_consent.get('state', '')
                        sms_consent_opt_in = sms_consent.get('opt_in_level', '')
                        sms_consent_source = sms_consent.get('consent_collected_from', '')
                        sms_consent_updated = None
                        if sms_consent.get('consent_updated_at'):
                            sms_consent_updated = parser.parse(sms_consent.get('consent_updated_at'))

                        # Dirección por defecto
                        default_addr = customer.get('default_address') or {}

                        # Preparar datos del cliente
                        customer_data = {
                            # Identificadores
                            'admin_graphql_api_id': customer.get('admin_graphql_api_id', ''),

                            # Datos básicos
                            'first_name': customer.get('first_name') or None,
                            'last_name': customer.get('last_name') or None,
                            'email': customer.get('email') or None,
                            'phone': customer.get('phone') or None,

                            # Estado y verificación
                            'state': customer.get('state', 'disabled'),
                            'verified_email': customer.get('verified_email', False),

                            # Estadísticas
                            'orders_count': customer.get('orders_count', 0),
                            'total_spent': Decimal(str(customer.get('total_spent', '0'))),
                            'currency': customer.get('currency', 'PYG'),

                            # Última orden
                            'last_order_id': customer.get('last_order_id'),
                            'last_order_name': customer.get('last_order_name') or '',

                            # Notas y etiquetas
                            'note': customer.get('note'),
                            'tags': customer.get('tags', ''),

                            # Impuestos
                            'tax_exempt': customer.get('tax_exempt', False),
                            'tax_exemptions': customer.get('tax_exemptions', []),

                            # Marketing - Email
                            'email_marketing_consent_state': email_consent_state,
                            'email_marketing_consent_opt_in_level': email_consent_opt_in,
                            'email_marketing_consent_updated_at': email_consent_updated,

                            # Marketing - SMS
                            'sms_marketing_consent_state': sms_consent_state,
                            'sms_marketing_consent_opt_in_level': sms_consent_opt_in,
                            'sms_marketing_consent_updated_at': sms_consent_updated,
                            'sms_marketing_consent_source': sms_consent_source,

                            # Multipass
                            'multipass_identifier': customer.get('multipass_identifier'),

                            # Direcciones (JSON completo)
                            'addresses': customer.get('addresses', []),
                            'default_address': default_addr,

                            # Dirección por defecto desnormalizada (usar or '' para convertir None a vacío)
                            'default_address_id': default_addr.get('id'),
                            'default_address_first_name': default_addr.get('first_name') or '',
                            'default_address_last_name': default_addr.get('last_name') or '',
                            'default_address_company': default_addr.get('company') or '',
                            'default_address_address1': default_addr.get('address1') or '',
                            'default_address_address2': default_addr.get('address2') or '',
                            'default_address_city': default_addr.get('city') or '',
                            'default_address_province': default_addr.get('province') or '',
                            'default_address_province_code': default_addr.get('province_code') or '',
                            'default_address_country': default_addr.get('country') or '',
                            'default_address_country_code': default_addr.get('country_code') or '',
                            'default_address_country_name': default_addr.get('country_name') or '',
                            'default_address_zip': default_addr.get('zip') or '',
                            'default_address_phone': default_addr.get('phone') or '',

                            # Fechas
                            'created_at_shopify': created_at_shopify,
                            'updated_at_shopify': updated_at_shopify,
                        }

                        # Crear o actualizar
                        customer_obj, created = ShopifyCustomer.objects.update_or_create(
                            shopify_id=shopify_id,
                            defaults=customer_data
                        )

                        if created:
                            stats['created'] += 1
                            logger.info(f"✓ Cliente creado: {customer_obj.full_name or customer_obj.email or shopify_id}")
                        else:
                            stats['updated'] += 1
                            logger.debug(f"↻ Cliente actualizado: {customer_obj.full_name or customer_obj.email or shopify_id}")

                        total_processed += 1

                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"✗ Error sincronizando cliente {customer.get('id')}: {str(e)}")

                # Verificar si hay más páginas (Shopify usa Link headers para paginación)
                # Por ahora, si recibimos menos de limit, asumimos que no hay más
                has_more = len(customers) == limit

                # TODO: Implementar paginación basada en Link header si es necesario
                # Por ahora salimos después de la primera página si limit < 250
                if limit < 250:
                    has_more = False

            sync_log.items_processed = total_processed
            sync_log.items_created = stats['created']
            sync_log.items_updated = stats['updated']
            sync_log.items_failed = stats['errors']
            sync_log.complete(status='success' if stats['errors'] == 0 else 'partial')

            logger.info(f"Sincronización de clientes completada: {stats}")
            return stats

        except Exception as e:
            error_msg = f"Error en sincronización de clientes: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise

    def get_customers_summary(self):
        """Retorna un resumen de todos los clientes sincronizados"""
        from .models import ShopifyCustomer
        from django.db.models import Sum, Avg, Count

        qs = ShopifyCustomer.objects.all()
        return {
            'total': qs.count(),
            'with_email': qs.exclude(email__isnull=True).exclude(email='').count(),
            'with_phone': qs.exclude(phone__isnull=True).exclude(phone='').count(),
            'with_orders': qs.filter(orders_count__gt=0).count(),
            'verified_email': qs.filter(verified_email=True).count(),
            'tax_exempt': qs.filter(tax_exempt=True).count(),
            'total_spent': qs.aggregate(Sum('total_spent'))['total_spent__sum'] or 0,
            'avg_orders': qs.aggregate(Avg('orders_count'))['orders_count__avg'] or 0,
            'by_state': dict(qs.values('state').annotate(count=Count('id')).values_list('state', 'count')),
        }

    # ==================== PRODUCTOS (Sincronización) ====================

    def sync_products(self, limit=250):
        """
        Sincroniza productos de Shopify al modelo ShopifyProduct.
        Usa update_or_create para evitar duplicados.

        Args:
            limit: Número de productos por página (máx 250)

        Returns:
            dict: Estadísticas de sincronización {created, updated, errors}
        """
        from .models import ShopifyProduct, ShopifySyncLog
        from dateutil import parser
        from decimal import Decimal

        sync_log = ShopifySyncLog.objects.create(
            sync_type='products',
            status='success'
        )

        stats = {'created': 0, 'updated': 0, 'errors': 0}
        total_processed = 0

        try:
            response = self.get_products(limit=limit)
            products = response.get('products', [])

            logger.info(f"Sincronizando {len(products)} productos desde Shopify")

            for product in products:
                try:
                    # Obtener primera variante (para precio, SKU, etc.)
                    variants = product.get('variants', [])
                    variant = variants[0] if variants else {}

                    # Obtener primera imagen
                    images = product.get('images', [])
                    image = images[0] if images else {}

                    # Parsear fechas
                    published_at = None
                    if product.get('published_at'):
                        published_at = parser.parse(product.get('published_at'))

                    created_at_shopify = None
                    if product.get('created_at'):
                        created_at_shopify = parser.parse(product.get('created_at'))

                    updated_at_shopify = None
                    if product.get('updated_at'):
                        updated_at_shopify = parser.parse(product.get('updated_at'))

                    # Preparar precio comparativo
                    compare_at_price = None
                    if variant.get('compare_at_price'):
                        compare_at_price = Decimal(str(variant.get('compare_at_price')))

                    product_data = {
                        'title': product.get('title', '')[:500],
                        'description': product.get('body_html', '')[:5000] if product.get('body_html') else '',
                        'vendor': product.get('vendor', '')[:255],
                        'product_type': product.get('product_type', '')[:255],
                        'handle': product.get('handle', '')[:255],
                        'status': product.get('status', 'active'),
                        'price': Decimal(str(variant.get('price', 0))),
                        'compare_at_price': compare_at_price,
                        'inventory_quantity': variant.get('inventory_quantity', 0) or 0,
                        'sku': variant.get('sku', '')[:255] if variant.get('sku') else '',
                        'barcode': variant.get('barcode', '')[:255] if variant.get('barcode') else '',
                        'image_url': image.get('src', '')[:500] if image.get('src') else '',
                        'published_at': published_at,
                        'created_at_shopify': created_at_shopify,
                        'updated_at_shopify': updated_at_shopify,
                    }

                    product_obj, created = ShopifyProduct.objects.update_or_create(
                        shopify_id=product.get('id'),
                        defaults=product_data
                    )

                    if created:
                        stats['created'] += 1
                        logger.info(f"✓ Producto creado: {product_obj.title}")
                    else:
                        stats['updated'] += 1
                        logger.debug(f"↻ Producto actualizado: {product_obj.title}")

                    total_processed += 1

                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"✗ Error sincronizando producto {product.get('id')}: {str(e)}")

            sync_log.items_processed = total_processed
            sync_log.items_created = stats['created']
            sync_log.items_updated = stats['updated']
            sync_log.items_failed = stats['errors']
            sync_log.complete(status='success' if stats['errors'] == 0 else 'partial')

            logger.info(f"Sincronización de productos completada: {stats}")
            return stats

        except Exception as e:
            error_msg = f"Error en sincronización de productos: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise

    # ==================== ÓRDENES (Sincronización) ====================

    def sync_orders(self, limit=250, financial_status=None):
        """
        Sincroniza TODAS las órdenes de Shopify (no solo pagadas).

        Args:
            limit: Número de órdenes a sincronizar
            financial_status: Filtro opcional (pending, paid, etc.)

        Returns:
            dict: Estadísticas de sincronización {created, updated, errors}
        """
        from .models import ShopifyOrder, ShopifySyncLog
        from dateutil import parser
        from decimal import Decimal

        sync_log = ShopifySyncLog.objects.create(
            sync_type='orders',
            status='success'
        )

        stats = {'created': 0, 'updated': 0, 'errors': 0}
        total_processed = 0

        try:
            response = self.get_orders(
                limit=limit,
                status='any',
                financial_status=financial_status
            )
            orders = response.get('orders', [])

            logger.info(f"Sincronizando {len(orders)} órdenes desde Shopify")

            for order in orders:
                try:
                    customer = order.get('customer') or {}

                    # Parsear fechas
                    cancelled_at = None
                    if order.get('cancelled_at'):
                        cancelled_at = parser.parse(order.get('cancelled_at'))

                    created_at_shopify = None
                    if order.get('created_at'):
                        created_at_shopify = parser.parse(order.get('created_at'))

                    updated_at_shopify = None
                    if order.get('updated_at'):
                        updated_at_shopify = parser.parse(order.get('updated_at'))

                    processed_at = None
                    if order.get('processed_at'):
                        processed_at = parser.parse(order.get('processed_at'))

                    order_data = {
                        'order_number': order.get('order_number', 0),
                        'name': order.get('name', ''),
                        'customer_email': customer.get('email', '') or '',
                        'customer_phone': customer.get('phone', '') or '',
                        'customer_first_name': customer.get('first_name', '') or '',
                        'customer_last_name': customer.get('last_name', '') or '',
                        'customer_tags': customer.get('tags', '') or '',
                        'total_price': Decimal(str(order.get('total_price', 0))),
                        'subtotal_price': Decimal(str(order.get('subtotal_price', 0))),
                        'total_tax': Decimal(str(order.get('total_tax', 0))),
                        'total_discounts': Decimal(str(order.get('total_discounts', 0))),
                        'currency': order.get('currency', 'PYG'),
                        'financial_status': order.get('financial_status', 'pending'),
                        'fulfillment_status': order.get('fulfillment_status', '') or '',
                        'cancelled_at': cancelled_at,
                        'cancel_reason': order.get('cancel_reason', '') or '',
                        'note': order.get('note', '') or '',
                        'tags': order.get('tags', '') or '',
                        'created_at_shopify': created_at_shopify,
                        'updated_at_shopify': updated_at_shopify,
                        'processed_at': processed_at,
                    }

                    order_obj, created = ShopifyOrder.objects.update_or_create(
                        shopify_id=order.get('id'),
                        defaults=order_data
                    )

                    if created:
                        stats['created'] += 1
                        logger.info(f"✓ Orden creada: {order_obj.name}")
                    else:
                        stats['updated'] += 1
                        logger.debug(f"↻ Orden actualizada: {order_obj.name}")

                    total_processed += 1

                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"✗ Error sincronizando orden {order.get('id')}: {str(e)}")

            sync_log.items_processed = total_processed
            sync_log.items_created = stats['created']
            sync_log.items_updated = stats['updated']
            sync_log.items_failed = stats['errors']
            sync_log.complete(status='success' if stats['errors'] == 0 else 'partial')

            logger.info(f"Sincronización de órdenes completada: {stats}")
            return stats

        except Exception as e:
            error_msg = f"Error en sincronización de órdenes: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise


# ==================== HELPER FUNCTIONS ====================

def extract_ruc_from_tags(tags):
    """
    Extrae RUC de los tags de Shopify.
    Formato esperado: "ruc:4492525"

    Args:
        tags: String con tags separados por comas

    Returns:
        str: RUC sin DV o None si no se encuentra
    """
    if not tags:
        return None

    tags_list = tags.split(',')
    for tag in tags_list:
        tag = tag.strip().lower()
        if tag.startswith('ruc:'):
            return tag.split(':')[1].strip()

    return None
