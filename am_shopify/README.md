# AM Shopify - Módulo de Integración con Shopify

Módulo completo de integración con Shopify para Django, con gestión automática de tokens, sincronización de productos y órdenes.

## 🚀 Características

- ✅ **Gestión Automática de Tokens**: Renovación automática cada 24 horas
- ✅ **Sincronización de Productos**: Lee, crea y actualiza productos
- ✅ **Gestión de Inventario**: Actualiza cantidades de stock
- ✅ **Sincronización de Órdenes**: Distingue pagadas, pendientes, canceladas
- ✅ **Logs Detallados**: Tracking completo de todas las sincronizaciones
- ✅ **Admin Interface**: Interfaz visual para gestión

## 📦 Instalación

El módulo ya está instalado en `INSTALLED_APPS`. Las migraciones han sido ejecutadas.

## 🔑 Configuración Inicial

### 1. Crear el primer token

```bash
python manage.py shopify_refresh_token
```

Esto creará el primer registro en la base de datos con el token de acceso.

### 2. Verificar en el Admin

Ve a `/admin/am_shopify/shopifyaccesstoken/` para ver el estado del token.

## 📚 Uso

### Comandos de Management

#### Sincronizar Productos

```bash
# Sincronizar todos los productos (límite 250)
python manage.py shopify_sync_products

# Sincronizar con límite personalizado
python manage.py shopify_sync_products --limit 100
```

#### Sincronizar Órdenes

```bash
# Sincronizar todas las órdenes
python manage.py shopify_sync_orders

# Solo órdenes pagadas
python manage.py shopify_sync_orders --financial-status paid

# Solo órdenes abiertas
python manage.py shopify_sync_orders --status open

# Límite personalizado
python manage.py shopify_sync_orders --limit 100
```

#### Renovar Token

```bash
python manage.py shopify_refresh_token
```

### Uso en Código Python

#### Trabajar con Productos

```python
from am_shopify.managers import ProductManager

# Inicializar manager
manager = ProductManager()

# Sincronizar productos desde Shopify
result = manager.sync_products(limit=250)
print(f"Productos sincronizados: {result['processed']}")

# Crear un nuevo producto
product = manager.create_product(
    title="Mi Producto",
    description="<p>Descripción HTML</p>",
    price=100.00,
    sku="SKU123",
    barcode="123456789",
    inventory_quantity=50,
    vendor="Mi Marca",
    product_type="Electrónica"
)

# Actualizar un producto
manager.update_product(
    shopify_id=product.shopify_id,
    title="Producto Actualizado",
    price="150.00"
)

# Actualizar inventario
manager.update_inventory(
    shopify_id=product.shopify_id,
    quantity=75
)
```

#### Trabajar con Órdenes

```python
from am_shopify.managers import OrderManager

# Inicializar manager
manager = OrderManager()

# Sincronizar órdenes
result = manager.sync_orders(limit=250, financial_status='paid')

# Obtener órdenes pagadas
paid_orders = manager.get_paid_orders()

# Obtener órdenes pendientes
pending_orders = manager.get_pending_orders()

# Obtener órdenes canceladas
cancelled_orders = manager.get_cancelled_orders()

# Iterar sobre órdenes
for order in paid_orders:
    print(f"Orden {order.name}: {order.total_price} {order.currency}")
    print(f"Cliente: {order.customer_email}")
```

#### Usar el Cliente API Directamente

```python
from am_shopify.shopify_client import ShopifyAPIClient

# Inicializar cliente
client = ShopifyAPIClient()

# Obtener información de la tienda
shop_info = client.get_shop_info()
print(shop_info['shop']['name'])

# Obtener productos
products = client.get_products(limit=50)

# Crear producto con imágenes
new_product = client.create_product({
    'title': 'Producto con Imagen',
    'body_html': '<p>Descripción</p>',
    'vendor': 'Mi Marca',
    'product_type': 'Accesorios',
    'variants': [{
        'price': '50.00',
        'sku': 'ACC-001',
        'inventory_quantity': 100
    }],
    'images': [{
        'src': 'https://example.com/image.jpg',
        'alt': 'Imagen del producto'
    }]
})

# Actualizar variante (precio, SKU, código de barras)
client.update_variant(variant_id=12345, variant_data={
    'price': '75.00',
    'barcode': '987654321',
    'sku': 'ACC-001-NEW'
})

# Gestión de inventario
locations = client.get_locations()
location_id = locations['locations'][0]['id']

# Establecer nivel de inventario
client.set_inventory_level(
    inventory_item_id=67890,
    location_id=location_id,
    available=200
)

# Ajustar inventario (incremento/decremento)
client.adjust_inventory_level(
    inventory_item_id=67890,
    location_id=location_id,
    available_adjustment=-5  # Reduce en 5 unidades
)
```

#### Gestión de Tokens

```python
from am_shopify.services import ShopifyTokenService

service = ShopifyTokenService()

# Obtener token válido (lo renueva automáticamente si es necesario)
token = service.get_valid_token()

# Crear/renovar token manualmente
token = service.get_or_create_token()
```

## 🗂️ Modelos

### ShopifyAccessToken
Almacena tokens de acceso con renovación automática.

**Campos principales:**
- `store_name`: Nombre de la tienda
- `access_token`: Token de acceso actual
- `expires_at`: Fecha de expiración
- `is_active`: Si está activo

**Métodos útiles:**
- `is_valid()`: Verifica si el token es válido
- `is_expiring_soon()`: Verifica si expirará pronto
- `get_token_or_refresh()`: Obtiene el token o lo renueva

### ShopifyProduct
Almacena productos sincronizados.

**Campos principales:**
- `shopify_id`: ID en Shopify
- `title`, `description`, `vendor`, `product_type`
- `price`, `compare_at_price`
- `inventory_quantity`, `sku`, `barcode`
- `image_url`
- `status`: active, draft, archived

### ShopifyOrder
Almacena órdenes sincronizadas.

**Campos principales:**
- `shopify_id`: ID en Shopify
- `order_number`, `name`
- `customer_email`, `customer_phone`, `customer_first_name`, `customer_last_name`
- `total_price`, `subtotal_price`, `total_tax`, `total_discounts`
- `financial_status`: pending, paid, refunded, etc.
- `fulfillment_status`: fulfilled, partial, etc.

**Propiedades útiles:**
- `is_paid`: Verifica si está pagada
- `is_pending`: Verifica si está pendiente
- `is_cancelled`: Verifica si fue cancelada

### ShopifySyncLog
Log de todas las sincronizaciones.

**Campos:**
- `sync_type`: products, orders, token_refresh
- `status`: success, error, partial
- `items_processed`, `items_created`, `items_updated`, `items_failed`
- `duration_seconds`

## 🔄 Renovación Automática de Tokens

Los tokens se renuevan automáticamente cuando:
1. Han expirado
2. Van a expirar en menos de 2 horas

Puedes configurar un cron job para renovar tokens periódicamente:

```bash
# Cada 12 horas
0 */12 * * * cd /path/to/project && python manage.py shopify_refresh_token
```

O usar Celery Beat:

```python
# celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'refresh-shopify-token': {
        'task': 'am_shopify.tasks.refresh_token',
        'schedule': crontab(hour='*/12'),  # Cada 12 horas
    },
}
```

## 📊 Admin Interface

Accede a `/admin/am_shopify/` para:

- Ver y gestionar tokens de acceso
- Ver productos sincronizados
- Ver órdenes sincronizadas
- Ver logs de sincronización
- Sincronizar productos individuales desde el admin

## 🛠️ API Client Completo

El `ShopifyAPIClient` incluye métodos para:

**Productos:**
- `get_products()`, `get_product(id)`
- `create_product()`, `update_product()`, `delete_product()`

**Variantes:**
- `get_variant()`, `update_variant()`

**Inventario:**
- `get_inventory_levels()`
- `set_inventory_level()`, `adjust_inventory_level()`

**Órdenes:**
- `get_orders()`, `get_order(id)`, `cancel_order()`

**Imágenes:**
- `get_product_images()`, `create_product_image()`
- `update_product_image()`, `delete_product_image()`

**Otros:**
- `get_locations()`, `get_shop_info()`
- `get_webhooks()`, `create_webhook()`, `delete_webhook()`

## 🧪 Comandos de Testing

El módulo incluye comandos de testing completos para verificar toda la funcionalidad:

### Test Completo (Recomendado)

```bash
# Ejecuta todos los tests en secuencia
python manage.py shopify_test_all
```

Este comando ejecuta:
1. ✅ Renovación de token
2. ✅ Crear 5 productos de prueba
3. ✅ Actualizar inventario de productos
4. ✅ Actualizar descripción y EAN
5. ✅ Sincronizar órdenes
6. ✅ Mostrar órdenes pagadas
7. ✅ Convertir órdenes a facturas SIFEN

### Tests Individuales

#### Crear Productos de Prueba

```bash
# Crear 10 productos de prueba
python manage.py shopify_test_create_products

# Crear cantidad personalizada
python manage.py shopify_test_create_products --count 5
```

Los productos se crean como "draft" para no publicarlos automáticamente.

#### Actualizar Inventario

```bash
# Actualizar inventario de productos de prueba
python manage.py shopify_test_update_inventory --test-products --quantity 100

# Actualizar inventario de un producto específico por SKU
python manage.py shopify_test_update_inventory --sku TEST-SKU-001 --quantity 50
```

#### Actualizar Descripción y EAN

```bash
# Actualizar productos de prueba
python manage.py shopify_test_update_description --test-products \
  --description "Producto actualizado" \
  --barcode "750000"

# Actualizar producto específico
python manage.py shopify_test_update_description --sku TEST-SKU-001 \
  --description "Nueva descripción" \
  --barcode "7501234567001"
```

#### Convertir Órdenes a Facturas SIFEN

```bash
# Convertir todas las órdenes pagadas a facturas
python manage.py shopify_convert_order_to_invoice --all-paid

# Convertir orden específica
python manage.py shopify_convert_order_to_invoice --order-id 5678901234

# Forzar conversión (aunque ya exista factura)
python manage.py shopify_convert_order_to_invoice --all-paid --force
```

**Importante sobre duplicados:**
- El sistema usa el campo `ext_link` de `DocumentHeader` para almacenar el `shopify_id`
- Antes de crear una factura, verifica si ya existe una con el mismo `ext_link`
- El campo `converted_to_invoice` en `ShopifyOrder` indica si ya fue convertida
- Usa `--force` solo si necesitas regenerar facturas

### Opciones de Test Completo

```bash
# Saltar creación de productos
python manage.py shopify_test_all --skip-products

# Saltar actualización de inventario
python manage.py shopify_test_all --skip-inventory

# Saltar actualización de descripción
python manage.py shopify_test_all --skip-description

# Saltar sincronización de órdenes
python manage.py shopify_test_all --skip-orders

# Saltar conversión a facturas
python manage.py shopify_test_all --skip-conversion
```

## 💳 Información de Pagos en Shopify

**Pregunta:** ¿Se guarda la información de tarjetas de crédito en las órdenes?

**Respuesta:** Shopify almacena información de pagos en las órdenes, pero con limitaciones de seguridad (PCI compliance):

### Datos Disponibles

✅ **Información que SÍ se guarda:**
- Método de pago (credit_card, paypal, etc.)
- Marca de tarjeta (Visa, Mastercard, American Express, etc.)
- Últimos 4 dígitos de la tarjeta
- Gateway de pago usado (Shopify Payments, Stripe, etc.)
- Estado de la transacción (success, pending, failed)
- Monto autorizado/capturado

❌ **Información que NO se guarda:**
- Número completo de tarjeta
- CVV/CVC
- Fecha de expiración completa
- Información del titular de la tarjeta

### Acceder a Información de Pagos

```python
from am_shopify.shopify_client import ShopifyAPIClient

client = ShopifyAPIClient()

# Obtener orden con transacciones
order = client.get_order(order_id=5678901234)

# Información de pago
if 'transactions' in order:
    for transaction in order['transactions']:
        print(f"Gateway: {transaction.get('gateway')}")
        print(f"Método: {transaction.get('payment_details', {}).get('credit_card_company')}")
        print(f"Últimos 4 dígitos: {transaction.get('payment_details', {}).get('credit_card_number')}")
        print(f"Estado: {transaction.get('status')}")
        print(f"Monto: {transaction.get('amount')}")

# O desde el modelo ShopifyOrder
from am_shopify.models import ShopifyOrder

order = ShopifyOrder.objects.get(shopify_id=5678901234)
# Los datos básicos están en el modelo, pero para detalles de pago
# necesitas hacer una llamada adicional a la API
```

### Estructura de Transacción (Ejemplo)

```json
{
  "id": 123456789,
  "order_id": 5678901234,
  "kind": "sale",
  "gateway": "shopify_payments",
  "status": "success",
  "amount": "100000.00",
  "currency": "PYG",
  "payment_details": {
    "credit_card_company": "Visa",
    "credit_card_number": "•••• •••• •••• 4242",
    "credit_card_name": "John Doe"
  }
}
```

**Nota de seguridad:** Por cumplimiento PCI-DSS, nunca se debe almacenar información completa de tarjetas de crédito. Shopify maneja esto automáticamente.

## 📝 Ejemplos Avanzados

### Sincronización Completa

```python
from am_shopify.managers import ProductManager, OrderManager

# Sincronizar todo
product_mgr = ProductManager()
order_mgr = OrderManager()

products_result = product_mgr.sync_products(limit=250)
orders_result = order_mgr.sync_orders(limit=250)

print(f"✓ Productos: {products_result['created']} nuevos, {products_result['updated']} actualizados")
print(f"✓ Órdenes: {orders_result['created']} nuevas, {orders_result['updated']} actualizadas")
```

### Crear Producto con Imagen

```python
from am_shopify.managers import ProductManager

manager = ProductManager()

product = manager.create_product(
    title="Producto con Imagen",
    description="<p>Descripción detallada</p>",
    price=150.00,
    sku="PROD-IMG-001",
    barcode="1234567890123",
    inventory_quantity=25,
    vendor="Mi Marca",
    product_type="Electrónica",
    images=[{
        'src': 'https://example.com/producto.jpg',
        'alt': 'Imagen principal del producto'
    }]
)

print(f"Producto creado: {product.title} (#{product.shopify_id})")
```

### Filtrar Órdenes Pagadas del Último Mes

```python
from am_shopify.models import ShopifyOrder
from datetime import datetime, timedelta

one_month_ago = datetime.now() - timedelta(days=30)

recent_paid_orders = ShopifyOrder.objects.filter(
    financial_status='paid',
    created_at_shopify__gte=one_month_ago
).order_by('-created_at_shopify')

total_revenue = sum(order.total_price for order in recent_paid_orders)

print(f"Órdenes pagadas último mes: {recent_paid_orders.count()}")
print(f"Ingresos totales: {total_revenue} PYG")
```

## 🐛 Troubleshooting

### Token expirado
```python
# Renovar manualmente
python manage.py shopify_refresh_token
```

### Error de conexión
```python
# Verificar credenciales en settings.py
# SHOPIFY_STORE
# SHOPIFY_CLIENTEID
# SHOPIFY_SECRET
```

### Ver logs de errores
```python
from am_shopify.models import ShopifySyncLog

# Ver últimos errores
errors = ShopifySyncLog.objects.filter(status='error').order_by('-started_at')[:10]

for error in errors:
    print(f"{error.sync_type}: {error.error_message}")
```

## 📞 Soporte

Para más información sobre la API de Shopify:
- [Documentación oficial](https://shopify.dev/docs/api/admin-rest)
- [API Reference](https://shopify.dev/docs/api/admin-rest/2024-10)
