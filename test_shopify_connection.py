#!/usr/bin/env python
"""
Script de prueba de conexión a Shopify
Tienda: http://www.gst3d.com.py/
"""

import os
import sys
import django
import requests
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from django.conf import settings

def test_shopify_connection():
    """
    Prueba la conexión con Shopify usando las credenciales configuradas
    """
    print("=" * 80)
    print("PRUEBA DE CONEXIÓN A SHOPIFY")
    print("=" * 80)
    print()

    # Mostrar configuración
    print("Configuración encontrada:")
    print(f"  SHOPIFY_STORE: {settings.SHOPIFY_STORE}")
    print(f"  SHOPIFY_CLIENTEID: {settings.SHOPIFY_CLIENTEID}")
    print(f"  SHOPIFY_SECRET: {settings.SHOPIFY_SECRET[:10]}...{settings.SHOPIFY_SECRET[-4:]}")
    print()

    # Extraer el nombre de la tienda de SHOPIFY_STORE
    shop_url = settings.SHOPIFY_STORE

    print("Extrayendo información de la tienda...")

    # Extraer nombre de SHOPIFY_STORE
    store_value = settings.SHOPIFY_STORE

    # Si SHOPIFY_STORE contiene .myshopify.com, extraer solo el nombre
    if '.myshopify.com' in store_value:
        shop_name = store_value.replace('https://', '').replace('http://', '').split('.myshopify.com')[0]
    else:
        shop_name = store_value

    print(f"  Nombre de tienda: {shop_name}")
    print()

    # Probar API con diferentes versiones
    api_versions = ['2024-10', '2024-07', '2024-04', '2024-01']

    print("Probando acceso a la API de Shopify Admin...")
    print()

    for version in api_versions:
        print(f"   Versión de API: {version}")

        # URL formato para custom app con API Key y Secret
        # NOTA: El SHOPIFY_SECRET que tienes parece ser un Access Token, no un password
        api_url = f"https://{shop_name}.myshopify.com/admin/api/{version}/shop.json"

        # Intentar con Access Token en header (método OAuth)
        # Usar SHOPIFY_ACCESS_TOKEN si está disponible, sino usar SHOPIFY_SECRET
        access_token = getattr(settings, 'SHOPIFY_ACCESS_TOKEN', settings.SHOPIFY_SECRET)
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            print(f"      Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                shop_info = data.get('shop', {})
                print(f"      ✓ CONEXIÓN EXITOSA!")
                print(f"      Nombre de la tienda: {shop_info.get('name', 'N/A')}")
                print(f"      Dominio: {shop_info.get('domain', 'N/A')}")
                print(f"      Email: {shop_info.get('email', 'N/A')}")
                print(f"      Plan: {shop_info.get('plan_name', 'N/A')}")
                print(f"      Moneda: {shop_info.get('currency', 'N/A')}")
                print()
                print("      Información adicional disponible:")
                print(f"      - ID de tienda: {shop_info.get('id', 'N/A')}")
                print(f"      - País: {shop_info.get('country_name', 'N/A')}")
                print(f"      - Timezone: {shop_info.get('timezone', 'N/A')}")

                # Intentar obtener información de productos
                print()
                print("      Probando acceso a productos...")
                products_url = f"https://{shop_name}.myshopify.com/admin/api/{version}/products.json?limit=5"
                products_response = requests.get(products_url, headers=headers, timeout=10)

                if products_response.status_code == 200:
                    products_data = products_response.json()
                    products = products_data.get('products', [])
                    print(f"      ✓ Se encontraron {len(products)} productos (mostrando primeros 5)")
                    for i, product in enumerate(products, 1):
                        print(f"         {i}. {product.get('title', 'Sin título')} - ID: {product.get('id')}")
                else:
                    print(f"      ✗ Error al obtener productos: {products_response.status_code}")

                return True

            elif response.status_code == 401:
                print(f"      ✗ No autorizado - Verifica las credenciales")
            elif response.status_code == 403:
                print(f"      ✗ Acceso prohibido - La app no tiene permisos suficientes")
            elif response.status_code == 404:
                print(f"      ✗ Tienda no encontrada")
            else:
                print(f"      ✗ Error: {response.status_code}")
                if response.text:
                    print(f"      Respuesta: {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            print(f"      ✗ Error de conexión: {str(e)}")

    print()

    print()
    print("=" * 80)
    print("DIAGNÓSTICO:")
    print("=" * 80)
    print()
    print("Si ninguna de las pruebas funcionó, verifica lo siguiente:")
    print()
    print("1. El SHOPIFY_SECRET debe ser un Access Token válido de la app")
    print("   - Para apps custom/privadas, debe ser el Admin API access token")
    print("   - Para apps públicas OAuth, debe ser el access token obtenido del proceso OAuth")
    print()
    print("2. El nombre de la tienda debe ser correcto")
    print(f"   - Nombre detectado: {shop_name}")
    print("   - URL de admin de Shopify: https://admin.shopify.com/store/XXX")
    print("   - El XXX es el nombre de la tienda")
    print()
    print("3. La app debe tener los permisos necesarios:")
    print("   - read_products (para leer productos)")
    print("   - write_products (si necesitas crear/modificar productos)")
    print("   - read_orders (para leer pedidos)")
    print("   - etc.")
    print()
    print("4. Verifica en el panel de Shopify:")
    print("   - Settings → Apps and sales channels → Develop apps")
    print("   - Encuentra tu app y verifica el Access Token")
    print()

    return False


if __name__ == "__main__":
    try:
        success = test_shopify_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
