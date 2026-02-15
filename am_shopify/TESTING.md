# Guía de Testing - AM Shopify

## 🎯 Resumen Rápido

El módulo `am_shopify` está completamente implementado con comandos de testing para todas las funcionalidades.

## ✅ Comandos Disponibles

### 1. Test Completo (Recomendado para empezar)

```bash
python manage.py shopify_test_all
```

Este comando ejecuta automáticamente:
1. ✅ Renovación de token
2. ✅ Crear 5 productos de prueba
3. ✅ Actualizar inventario
4. ✅ Actualizar descripción/EAN
5. ✅ Sincronizar órdenes
6. ✅ Mostrar órdenes pagadas
7. ✅ Convertir órdenes a facturas SIFEN

**Salida esperada:**
- Muestra progreso de cada test
- Estadísticas finales (productos, órdenes, sincronizaciones)
- Indicadores visuales ✓/✗ para cada operación

### 2. Crear Productos de Prueba

```bash
# Crear 10 productos (default)
python manage.py shopify_test_create_products

# Crear cantidad personalizada
python manage.py shopify_test_create_products --count 5
```

**Productos creados:**
- SKU: TEST-SKU-001, TEST-SKU-002, etc.
- Precio: 11,000, 12,000, 13,000, etc.
- Barcode: 7501234567001, 7501234567002, etc.
- Inventario: 10, 20, 30, etc.
- **Estado: draft** (no se publican automáticamente)

### 3. Actualizar Inventario

```bash
# Actualizar productos de prueba
python manage.py shopify_test_update_inventory --test-products --quantity 100

# Actualizar producto específico
python manage.py shopify_test_update_inventory --sku TEST-SKU-001 --quantity 50

# Actualizar primeros 10 productos
python manage.py shopify_test_update_inventory --quantity 75
```

### 4. Actualizar Descripción y EAN

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

**Nota:** El barcode se genera único agregando sufijo (750000 → 7500000001, 7500000002, etc.)

### 5. Convertir Órdenes a Facturas SIFEN

```bash
# Convertir todas las órdenes pagadas
python manage.py shopify_convert_order_to_invoice --all-paid

# Convertir orden específica
python manage.py shopify_convert_order_to_invoice --order-id 5678901234

# Forzar conversión (regenerar facturas)
python manage.py shopify_convert_order_to_invoice --all-paid --force
```

**Importante:**
- Solo convierte órdenes con `financial_status='paid'`
- Usa `ext_link` para prevenir duplicados
- Crea clientes automáticamente si no existen
- Marca la orden como `converted_to_invoice=True`

## 🔄 Flujo de Testing Típico

### Primer Test (Sin productos en Shopify)

```bash
# 1. Renovar token
python manage.py shopify_refresh_token

# 2. Crear productos de prueba
python manage.py shopify_test_create_products --count 10

# 3. Actualizar inventario de productos de prueba
python manage.py shopify_test_update_inventory --test-products --quantity 100

# 4. Actualizar descripciones
python manage.py shopify_test_update_description --test-products \
  --description "Producto actualizado desde Django" \
  --barcode "750000"

# 5. Sincronizar productos (traer a DB local)
python manage.py shopify_sync_products --limit 50

# 6. Ver productos en admin
# http://localhost:8000/admin/am_shopify/shopifyproduct/
```

### Testing de Órdenes

```bash
# 1. Sincronizar órdenes desde Shopify
python manage.py shopify_sync_orders --limit 50

# 2. Ver órdenes pagadas
python manage.py shopify_sync_orders --financial-status paid

# 3. Convertir órdenes pagadas a facturas
python manage.py shopify_convert_order_to_invoice --all-paid

# 4. Ver facturas generadas en admin
# http://localhost:8000/admin/Sifen/documentheader/
```

## 📊 Verificación de Resultados

### En la Base de Datos

```python
from am_shopify.models import ShopifyProduct, ShopifyOrder, ShopifySyncLog

# Ver productos
ShopifyProduct.objects.filter(sku__startswith='TEST-SKU-').count()

# Ver órdenes pagadas
ShopifyOrder.objects.filter(financial_status='paid').count()

# Ver órdenes convertidas a factura
ShopifyOrder.objects.filter(converted_to_invoice=True).count()

# Ver logs de sincronización
ShopifySyncLog.objects.filter(status='success').order_by('-started_at')[:5]
```

### En el Admin de Django

1. **Tokens**: `/admin/am_shopify/shopifyaccesstoken/`
   - Ver estado del token
   - Ver fecha de expiración

2. **Productos**: `/admin/am_shopify/shopifyproduct/`
   - Ver productos sincronizados
   - Acción: "Sync selected products"

3. **Órdenes**: `/admin/am_shopify/shopifyorder/`
   - Filtrar por estado financiero
   - Ver órdenes convertidas a factura

4. **Logs**: `/admin/am_shopify/shopifysynclog/`
   - Ver historial de sincronizaciones
   - Ver errores

5. **Facturas SIFEN**: `/admin/Sifen/documentheader/`
   - Filtrar por `ext_link__isnull=False` para ver facturas de Shopify
   - Ver cliente asignado automáticamente

## 🐛 Resolución de Problemas

### Error 403: Forbidden

**Causa:** El token tiene scopes limitados (Client Credentials Grant).

**Solución:** Los productos se crean como "draft", no "active". Esto puede fallar con algunos tokens. Usa `--force` o cambia a OAuth flow si necesitas crear productos activos.

### Error: Token expirado

```bash
python manage.py shopify_refresh_token
```

### Error: Orden ya convertida

Normal si ejecutas el comando dos veces. Usa `--force` para regenerar:

```bash
python manage.py shopify_convert_order_to_invoice --all-paid --force
```

### Error: Cliente no encontrado

El sistema crea clientes automáticamente. Si hay error, verifica:
- Email del cliente en la orden
- Modelo `Clientes` tiene campos requeridos correctos

### Ver logs detallados

Los errores se registran en:
- `log/toca3d.log`
- Admin: `/admin/am_shopify/shopifysynclog/`

## 📝 Notas Importantes

### Productos de Prueba

- Se crean como **draft** para no publicarlos automáticamente
- Puedes cambiarlos a "active" desde el admin de Shopify
- SKU único: TEST-SKU-001, TEST-SKU-002, etc.
- Tienen tag "test, prueba, automatico"

### Conversión a Facturas

- El campo `ext_link` de `DocumentHeader` almacena el `shopify_id`
- **Prevención de duplicados:**
  1. Busca `DocumentHeader` con mismo `ext_link`
  2. Verifica flag `converted_to_invoice` en `ShopifyOrder`
  3. Solo crea si no existe o con `--force`

### Clientes Automáticos

Cuando se convierte una orden a factura:
- Busca cliente por email
- Si no existe, lo crea automáticamente:
  - Nombre: `customer_first_name + customer_last_name`
  - Email y teléfono de la orden
  - Tipo: B2C, No Contribuyente
  - RUC innominado (0/0)

### Información de Pagos

**Se guarda en Shopify:**
- ✅ Método de pago (credit_card, paypal, etc.)
- ✅ Marca de tarjeta (Visa, Mastercard, etc.)
- ✅ Últimos 4 dígitos
- ✅ Gateway usado
- ✅ Estado de transacción

**NO se guarda (PCI compliance):**
- ❌ Número completo de tarjeta
- ❌ CVV
- ❌ Fecha de expiración completa

Para acceder a información de pago, usa:

```python
from am_shopify.shopify_client import ShopifyAPIClient

client = ShopifyAPIClient()
order = client.get_order(order_id=5678901234)

# Ver transacciones
for transaction in order.get('transactions', []):
    payment = transaction.get('payment_details', {})
    print(f"Tarjeta: {payment.get('credit_card_company')}")
    print(f"Número: {payment.get('credit_card_number')}")
```

## 🚀 Próximos Pasos

1. **Ejecutar test completo:**
   ```bash
   python manage.py shopify_test_all
   ```

2. **Revisar resultados en admin:**
   - http://localhost:8000/admin/am_shopify/

3. **Verificar facturas generadas:**
   - http://localhost:8000/admin/Sifen/documentheader/

4. **Implementar en producción:**
   - Configurar cron job para sincronización automática
   - O usar Celery Beat para tareas periódicas

## 📚 Documentación Completa

Ver [README.md](README.md) para documentación completa del módulo.
