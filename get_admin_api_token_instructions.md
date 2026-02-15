# Cómo Obtener el Admin API Access Token de Shopify

## ⚠️ Problema Actual

El método **Client Credentials Grant** que estamos usando tiene limitaciones:
- ❌ No da acceso a productos (403 Forbidden)
- ❌ No da acceso a órdenes (403 Forbidden)
- ❌ Shopify restringe intencionalmente este flow para seguridad

## ✅ Solución: Usar Admin API Access Token

Este es el método recomendado y MÁS SIMPLE para apps internas/privadas.

### Paso 1: Acceder al Dev Dashboard

1. Ve a tu Admin de Shopify: `https://admin.shopify.com/store/altamachines`
2. Click en **Settings** (⚙️) en la barra lateral izquierda
3. Click en **Apps and sales channels**
4. Click en **Develop apps** (parte superior derecha)

### Paso 2: Seleccionar tu App

1. Busca y click en tu app: `acceso_altamachine`
2. Si no existe, créala:
   - Click **Create an app**
   - Nombre: `acceso_altamachine`
   - Click **Create app**

### Paso 3: Configurar Scopes (Permisos)

1. Click en la pestaña **Configuration**
2. En la sección **Admin API integration**, click **Configure**
3. Selecciona los scopes necesarios:

   **Productos:**
   - ✅ `read_products`
   - ✅ `write_products`

   **Órdenes:**
   - ✅ `read_orders`
   - ✅ `write_orders`

   **Inventario:**
   - ✅ `read_inventory`
   - ✅ `write_inventory`

   **Clientes (opcional):**
   - ✅ `read_customers`
   - ✅ `write_customers`

4. Click **Save**

### Paso 4: Instalar la App (si no está instalada)

1. Si ves un botón **Install app**, haz click en él
2. Confirma la instalación
3. Shopify mostrará un mensaje de éxito

### Paso 5: Obtener el Admin API Access Token

1. Ve a la pestaña **API credentials**
2. Baja hasta la sección **Admin API access token**
3. Click en **Reveal token once** (solo se muestra UNA VEZ, cópialo bien)
4. Copia el token completo (empieza con `shpat_`)

   Ejemplo: `shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Paso 6: Guardar el Token en la Base de Datos

Ejecuta este comando Python (reemplaza `TU_TOKEN_AQUI` con el token que copiaste):

```bash
python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from am_shopify.models import ShopifyAccessToken
from django.utils import timezone
from datetime import timedelta

# REEMPLAZA ESTE TOKEN CON EL QUE COPIASTE
new_token = 'TU_TOKEN_AQUI'

# Token permanente (expira en 1 año como precaución, pero realmente no expira)
expires_at = timezone.now() + timedelta(days=365)

token_obj, created = ShopifyAccessToken.objects.update_or_create(
    store_name='altamachines',
    defaults={
        'client_id': 'TU_CLIENT_ID_AQUI',
        'client_secret': 'TU_CLIENT_SECRET_AQUI',
        'access_token': new_token,
        'scopes': 'read_products,write_products,read_orders,write_orders,read_inventory,write_inventory',
        'expires_at': expires_at,
        'is_active': True
    }
)

print(f'✓ Token guardado en la base de datos')
print(f'  Store: {token_obj.store_name}')
print(f'  Token: {token_obj.access_token[:20]}...')
print(f'  Válido: {token_obj.is_valid()}')
"
```

### Paso 7: Probar la Conexión

```bash
python manage.py shopify_test_all
```

## 🎯 Ventajas del Admin API Access Token

✅ **Permanente** - No expira (a diferencia de Client Credentials Grant que expira en 24h)
✅ **Acceso completo** - Todos los scopes que configures funcionan
✅ **Simple** - Solo copiar y pegar, sin OAuth flow complejo
✅ **Ideal para apps internas** - Perfecto para integración backend
✅ **Sin renovación** - No necesitas renovar el token diariamente

## 🔒 Seguridad

- ⚠️ **NUNCA** compartas este token públicamente
- ⚠️ **NUNCA** lo commits en Git
- ✅ Úsalo solo en tu backend (Django)
- ✅ Está almacenado de forma segura en tu base de datos

## 📝 Notas Importantes

1. **Este token NO expira** - Es permanente hasta que:
   - Desinstales la app
   - Revokes el token manualmente
   - Recrees la app

2. **Si pierdes el token:**
   - Ve a API credentials
   - Encontrarás el token (parcialmente oculto)
   - Si no lo recuerdas, tendrás que revocar y generar uno nuevo

3. **Revocación:**
   - En API credentials → Admin API access token
   - Click en **Revoke**
   - Genera uno nuevo

## ✨ Después de Configurar

Una vez que guardes el Admin API Access Token en la base de datos:

```bash
# Probar creación de productos
python manage.py shopify_test_create_products --count 5

# Sincronizar órdenes
python manage.py shopify_sync_orders --limit 20

# Test completo
python manage.py shopify_test_all
```

¡Todo debería funcionar perfectamente! 🎉
