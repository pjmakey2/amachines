import logging
from datetime import datetime
from django.utils import timezone
from .shopify_client import ShopifyAPIClient
from .models import ShopifyProduct, ShopifyOrder, ShopifySyncLog

logger = logging.getLogger(__name__)


class ProductManager:
    """
    Manager para gestionar productos de Shopify
    """
    
    def __init__(self):
        self.client = ShopifyAPIClient()
    
    def sync_products(self, limit=250):
        """
        Sincroniza productos desde Shopify a la base de datos local
        """
        sync_log = ShopifySyncLog.objects.create(
            sync_type='products',
            status='success'
        )
        
        try:
            products_created = 0
            products_updated = 0
            products_processed = 0
            
            # Obtener productos de Shopify
            response = self.client.get_products(limit=limit)
            products = response.get('products', [])
            
            for product_data in products:
                try:
                    self._sync_product(product_data)
                    products_processed += 1
                    
                    # Verificar si fue creado o actualizado
                    if ShopifyProduct.objects.filter(shopify_id=product_data['id']).exists():
                        products_updated += 1
                    else:
                        products_created += 1
                        
                except Exception as e:
                    logger.error(f"Error sincronizando producto {product_data.get('id')}: {str(e)}")
                    sync_log.items_failed += 1
            
            sync_log.items_processed = products_processed
            sync_log.items_created = products_created
            sync_log.items_updated = products_updated
            sync_log.complete(status='success')
            
            logger.info(f"Sincronización completada: {products_processed} procesados, {products_created} creados, {products_updated} actualizados")
            
            return {
                'processed': products_processed,
                'created': products_created,
                'updated': products_updated,
                'failed': sync_log.items_failed
            }
            
        except Exception as e:
            error_msg = f"Error en sincronización de productos: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise
    
    def _sync_product(self, product_data):
        """Sincroniza un producto individual"""
        # Obtener la primera variante para precio e inventario
        variant = product_data.get('variants', [{}])[0] if product_data.get('variants') else {}
        
        # Obtener la primera imagen
        image = product_data.get('images', [{}])[0] if product_data.get('images') else {}
        
        # Parsear fechas
        published_at = self._parse_datetime(product_data.get('published_at'))
        created_at = self._parse_datetime(product_data.get('created_at'))
        updated_at = self._parse_datetime(product_data.get('updated_at'))
        
        # Actualizar o crear producto
        product, created = ShopifyProduct.objects.update_or_create(
            shopify_id=product_data['id'],
            defaults={
                'title': product_data.get('title', ''),
                'description': product_data.get('body_html', ''),
                'vendor': product_data.get('vendor', ''),
                'product_type': product_data.get('product_type', ''),
                'handle': product_data.get('handle', ''),
                'status': product_data.get('status', 'active'),
                'price': variant.get('price'),
                'compare_at_price': variant.get('compare_at_price'),
                'inventory_quantity': variant.get('inventory_quantity', 0),
                'sku': variant.get('sku', ''),
                'barcode': variant.get('barcode', ''),
                'image_url': image.get('src', ''),
                'published_at': published_at,
                'created_at_shopify': created_at,
                'updated_at_shopify': updated_at,
            }
        )
        
        return product, created
    
    def create_product(self, title, description='', price=0, sku='', barcode='', inventory_quantity=0, **kwargs):
        """
        Crea un producto en Shopify y lo sincroniza localmente
        """
        product_data = {
            'title': title,
            'body_html': description,
            'variants': [{
                'price': str(price),
                'sku': sku,
                'barcode': barcode,
                'inventory_quantity': inventory_quantity,
                'inventory_management': 'shopify' if inventory_quantity > 0 else None
            }]
        }
        
        # Agregar campos opcionales
        if 'vendor' in kwargs:
            product_data['vendor'] = kwargs['vendor']
        if 'product_type' in kwargs:
            product_data['product_type'] = kwargs['product_type']
        if 'images' in kwargs:
            product_data['images'] = kwargs['images']
        
        # Crear en Shopify
        response = self.client.create_product(product_data)
        created_product = response.get('product')
        
        # Sincronizar localmente
        product, _ = self._sync_product(created_product)
        
        logger.info(f"Producto creado: {product.title} (#{product.shopify_id})")
        
        return product
    
    def update_product(self, shopify_id, **updates):
        """
        Actualiza un producto en Shopify
        
        Args:
            shopify_id: ID del producto en Shopify
            **updates: Campos a actualizar (title, body_html, vendor, etc.)
        """
        response = self.client.update_product(shopify_id, updates)
        updated_product = response.get('product')
        
        # Sincronizar localmente
        product, _ = self._sync_product(updated_product)
        
        logger.info(f"Producto actualizado: {product.title} (#{product.shopify_id})")
        
        return product
    
    def update_inventory(self, shopify_id, quantity):
        """
        Actualiza el inventario de un producto
        """
        # Primero obtenemos el producto para obtener el variant_id
        product = ShopifyProduct.objects.get(shopify_id=shopify_id)
        
        # Obtener el producto de Shopify para obtener el variant_id
        response = self.client.get_product(shopify_id)
        variant = response['product']['variants'][0]
        variant_id = variant['id']
        
        # Actualizar inventario
        self.client.update_variant(variant_id, {'inventory_quantity': quantity})
        
        # Actualizar localmente
        product.inventory_quantity = quantity
        product.save()
        
        logger.info(f"Inventario actualizado para {product.title}: {quantity}")
        
        return product
    
    def _parse_datetime(self, datetime_str):
        """Parsea una fecha de Shopify al formato de Django"""
        if not datetime_str:
            return None
        try:
            # Shopify usa formato ISO 8601
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None


class OrderManager:
    """
    Manager para gestionar órdenes de Shopify
    """
    
    def __init__(self):
        self.client = ShopifyAPIClient()
    
    def sync_orders(self, limit=250, status='any', financial_status=None):
        """
        Sincroniza órdenes desde Shopify a la base de datos local
        """
        sync_log = ShopifySyncLog.objects.create(
            sync_type='orders',
            status='success'
        )
        
        try:
            orders_created = 0
            orders_updated = 0
            orders_processed = 0
            
            # Obtener órdenes de Shopify
            response = self.client.get_orders(
                limit=limit,
                status=status,
                financial_status=financial_status
            )
            orders = response.get('orders', [])
            
            for order_data in orders:
                try:
                    self._sync_order(order_data)
                    orders_processed += 1
                    
                    if ShopifyOrder.objects.filter(shopify_id=order_data['id']).exists():
                        orders_updated += 1
                    else:
                        orders_created += 1
                        
                except Exception as e:
                    logger.error(f"Error sincronizando orden {order_data.get('id')}: {str(e)}")
                    sync_log.items_failed += 1
            
            sync_log.items_processed = orders_processed
            sync_log.items_created = orders_created
            sync_log.items_updated = orders_updated
            sync_log.complete(status='success')
            
            logger.info(f"Sincronización de órdenes completada: {orders_processed} procesadas")
            
            return {
                'processed': orders_processed,
                'created': orders_created,
                'updated': orders_updated,
                'failed': sync_log.items_failed
            }
            
        except Exception as e:
            error_msg = f"Error en sincronización de órdenes: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise
    
    def _sync_order(self, order_data):
        """Sincroniza una orden individual"""
        customer = order_data.get('customer', {})
        
        # Parsear fechas
        created_at = self._parse_datetime(order_data.get('created_at'))
        updated_at = self._parse_datetime(order_data.get('updated_at'))
        processed_at = self._parse_datetime(order_data.get('processed_at'))
        cancelled_at = self._parse_datetime(order_data.get('cancelled_at'))
        
        # Actualizar o crear orden
        order, created = ShopifyOrder.objects.update_or_create(
            shopify_id=order_data['id'],
            defaults={
                'order_number': order_data.get('order_number'),
                'name': order_data.get('name', ''),
                'customer_email': customer.get('email', ''),
                'customer_phone': customer.get('phone', ''),
                'customer_first_name': customer.get('first_name', ''),
                'customer_last_name': customer.get('last_name', ''),
                'total_price': order_data.get('total_price', 0),
                'subtotal_price': order_data.get('subtotal_price', 0),
                'total_tax': order_data.get('total_tax', 0),
                'total_discounts': order_data.get('total_discounts', 0),
                'currency': order_data.get('currency', 'PYG'),
                'financial_status': order_data.get('financial_status', 'pending'),
                'fulfillment_status': order_data.get('fulfillment_status'),
                'cancelled_at': cancelled_at,
                'cancel_reason': order_data.get('cancel_reason', ''),
                'note': order_data.get('note', ''),
                'tags': order_data.get('tags', ''),
                'created_at_shopify': created_at,
                'updated_at_shopify': updated_at,
                'processed_at': processed_at,
            }
        )
        
        return order, created
    
    def get_paid_orders(self):
        """Obtiene órdenes pagadas"""
        return ShopifyOrder.objects.filter(financial_status='paid')
    
    def get_pending_orders(self):
        """Obtiene órdenes pendientes de pago"""
        return ShopifyOrder.objects.filter(financial_status='pending')
    
    def get_cart_orders(self):
        """
        Obtiene órdenes en carrito (no procesadas)
        En Shopify, esto serían draft orders o abandoned checkouts
        """
        return ShopifyOrder.objects.filter(processed_at__isnull=True)
    
    def get_cancelled_orders(self):
        """Obtiene órdenes canceladas/rechazadas"""
        return ShopifyOrder.objects.filter(cancelled_at__isnull=False)
    
    def _parse_datetime(self, datetime_str):
        """Parsea una fecha de Shopify al formato de Django"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None
