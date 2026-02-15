# 🔑 Cómo Obtener el Admin API Access Token

## ❌ Por qué Client Credentials Grant no funciona

Shopify **intencionalmente limita** el método Client Credentials Grant:
- Solo permite acceso a información básica de la tienda
- **NO** permite crear/leer productos (403 Forbidden)
- **NO** permite leer órdenes (403 Forbidden)
- No importa cuántos scopes configures, este método tiene limitaciones hard-coded

## ✅ Solución: Admin API Access Token

Este es el método correcto para apps internas/custom. Es **MÁS SIMPLE** y funciona perfectamente.

---

## 📋 PASOS EXACTOS (5 minutos)

### Paso 1: Ir al Panel de Shopify

Abre tu navegador y ve a:
```
https://admin.shopify.com/store/altamachines
```

O simplemente ve a tu Admin de Shopify normal.

### Paso 2: Ir a Settings → Apps

1. Click en **⚙️ Settings** (esquina inferior izquierda)
2. En el menú de Settings, busca **Apps and sales channels**
3. Click en **Apps and sales channels**

### Paso 3: Develop Apps

1. En la parte superior derecha, verás un botón que dice **"Develop apps"**
2. Click en **"Develop apps"**
3. Si es tu primera vez, Shopify te pedirá que permitas el desarrollo de apps custom
4. Click en **"Allow custom app development"** si te lo pide

### Paso 4: Seleccionar tu App

Deberías ver tu app `acceso_altamachine` en la lista.

1. Click en **"acceso_altamachine"**
2. Verás varias pestañas en la parte superior

### Paso 5: Ver API Credentials

1. Click en la pestaña **"API credentials"**
2. Baja hasta encontrar la sección **"Admin API access token"**

Verás algo así:
```
Admin API access token
Your access token will only be shown once. Make sure to copy it and store it somewhere safe.

[Reveal token once]
```

### Paso 6: Revelar y Copiar el Token

1. **SI nunca has revelado el token antes:**
   - Click en **"Reveal token once"**
   - Aparecerá el token completo (empieza con `shpat_`)
   - **CÓPIALO INMEDIATAMENTE** - solo se muestra una vez

2. **SI ya revelaste el token antes pero no lo copiaste:**
   - El botón dirá "Revoke token" o mostrará el token parcialmente oculto
   - Si lo perdiste, tendrás que crear una nueva app o revocar y regenerar

### Paso 7: Guardar el Token en la Base de Datos

Copia este comando y **REEMPLAZA** `TU_TOKEN_AQUI` con el token que copiaste:

```bash
python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from am_shopify.models import ShopifyAccessToken
from django.utils import timezone
from datetime import timedelta

# REEMPLAZA ESTE VALOR CON TU TOKEN
new_token = 'TU_TOKEN_AQUI'

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

print('✓ Token guardado en la base de datos')
print(f'  Token: {token_obj.access_token[:20]}...')
print(f'  Válido: {token_obj.is_valid()}')
"
```

### Paso 8: Probar

```bash
python manage.py shopify_test_all
```

¡Debería funcionar perfectamente! 🎉

---

## 🆘 Si no ves el Admin API Access Token

### Opción A: Tu app no tiene scopes configurados

1. Ve a la pestaña **"Configuration"**
2. En **"Admin API integration"**, click **"Configure"**
3. Selecciona los scopes:
   - ✅ `read_products` y `write_products`
   - ✅ `read_orders` y `write_orders`
   - ✅ `read_inventory` y `write_inventory`
4. Click **"Save"**
5. Regresa a **"API credentials"** - ahora debería aparecer el Admin API access token

### Opción B: La app no está instalada

1. Verás un botón **"Install app"** en alguna parte
2. Click en **"Install app"**
3. Shopify te pedirá confirmación
4. Confirma la instalación
5. Ahora debería aparecer el Admin API access token

### Opción C: Crear una nueva app desde cero

Si nada funciona, crea una nueva app:

1. En **"Develop apps"**, click **"Create an app"**
2. Nombre: `toca3d_api`
3. Click **"Create app"**
4. Ve a **"Configuration"** → **"Admin API integration"** → **"Configure"**
5. Selecciona todos los scopes que necesites
6. Click **"Save"**
7. Click **"Install app"**
8. Ve a **"API credentials"**
9. Click **"Reveal token once"**
10. Copia el token

---

## 🎯 Ventajas del Admin API Access Token

✅ **Permanente** - No expira cada 24 horas
✅ **Funciona** - Acceso completo a productos, órdenes, inventario
✅ **Simple** - Solo copiar y pegar una vez
✅ **Ideal para backend** - Perfecto para tu integración Django
✅ **Sin renovación** - El sistema lo gestiona desde la BD

---

## 📸 Capturas de Referencia

Busca estas secciones en tu panel:

```
Settings (⚙️)
  └─ Apps and sales channels
       └─ Develop apps  [botón superior derecha]
            └─ acceso_altamachine [tu app]
                 ├─ Overview
                 ├─ Configuration  [configura scopes aquí]
                 └─ API credentials  [el token está aquí]
                      └─ Admin API access token
                           └─ [Reveal token once]  [CLICK AQUÍ]
```

---

## ❓ Preguntas Frecuentes

**P: ¿El token expira?**
R: No, el Admin API access token es permanente (hasta que lo revoques o desinstales la app).

**P: ¿Qué hago si ya revelé el token pero no lo copié?**
R: Tendrás que revocar el token actual y generar uno nuevo, o crear una nueva app.

**P: ¿Es seguro este método?**
R: Sí, es el método oficial de Shopify para apps custom/internas. Solo asegúrate de no compartir el token públicamente.

**P: ¿Por qué no funciona Client Credentials Grant?**
R: Shopify lo limita intencionalmente. Solo da acceso básico a la tienda, no a productos/órdenes.

---

Una vez que tengas el token, ¡todo funcionará perfectamente! 🚀
