#!/usr/bin/env python
"""
Script para obtener Access Token de Shopify usando Client Credentials Grant
Para apps creadas en el Dev Dashboard
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

def get_shopify_access_token():
    """
    Obtiene un access token usando Client Credentials Grant
    """
    print("=" * 80)
    print("OBTENIENDO ACCESS TOKEN DE SHOPIFY")
    print("=" * 80)
    print()

    # Configuración
    store_name = settings.SHOPIFY_STORE.replace('.myshopify.com', '').replace('https://', '').replace('http://', '')
    client_id = settings.SHOPIFY_CLIENTEID
    client_secret = settings.SHOPIFY_SECRET

    print("Configuración:")
    print(f"  Tienda: {store_name}.myshopify.com")
    print(f"  Client ID: {client_id}")
    print(f"  Client Secret: {client_secret[:10]}...{client_secret[-4:]}")
    print()

    # Endpoint para Client Credentials Grant
    token_url = f"https://{store_name}.myshopify.com/admin/oauth/access_token"

    print(f"Endpoint: {token_url}")
    print()

    # Parámetros para la solicitud
    # IMPORTANTE: El client_secret debe ser el valor completo sin modificaciones
    data = {
        'client_id': client_id,
        'client_secret': client_secret.strip(),  # Remover espacios
        'grant_type': 'client_credentials'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    print("Datos de la solicitud:")
    print(f"  grant_type: client_credentials")
    print(f"  client_id: {client_id}")
    print(f"  client_secret: {client_secret[:10]}...{client_secret[-4:]}")
    print()

    print("Enviando solicitud...")
    try:
        response = requests.post(token_url, data=data, headers=headers, timeout=30)

        print(f"Status Code: {response.status_code}")
        print()

        if response.status_code == 200:
            token_data = response.json()

            print("✓ ACCESS TOKEN OBTENIDO EXITOSAMENTE!")
            print()
            print("=" * 80)
            print("INFORMACIÓN DEL TOKEN:")
            print("=" * 80)
            print(f"Access Token: {token_data.get('access_token')}")
            print(f"Scopes: {token_data.get('scope', 'N/A')}")
            print(f"Expira en: {token_data.get('expires_in', 'N/A')} segundos ({token_data.get('expires_in', 0) / 3600:.1f} horas)")
            print()
            print("=" * 80)
            print("SIGUIENTE PASO:")
            print("=" * 80)
            print()
            print("Copia el Access Token de arriba y actualiza tu settings.py:")
            print()
            print(f"SHOPIFY_ACCESS_TOKEN = '{token_data.get('access_token')}'")
            print()
            print("NOTA: Este token expira en 24 horas. Necesitarás renovarlo diariamente")
            print("      o implementar un sistema de renovación automática.")
            print()

            return token_data.get('access_token')

        elif response.status_code == 401:
            print("✗ ERROR: No autorizado")
            print()
            print("Posibles causas:")
            print("  1. El Client ID o Client Secret son incorrectos")
            print("  2. La app no está instalada en la tienda")
            print("  3. La app fue desinstalada o eliminada")
            print()
            print("Solución:")
            print("  - Verifica que la app esté instalada en tu tienda")
            print("  - Ve a Settings → Apps and sales channels → Develop apps")
            print("  - Verifica que las credenciales sean correctas")

        elif response.status_code == 403:
            print("✗ ERROR: Acceso prohibido")
            print()
            print("La app no tiene permisos suficientes o no está configurada correctamente.")
            print()
            print("Solución:")
            print("  - Configura los scopes necesarios en el dev dashboard")
            print("  - Reinstala la app en tu tienda")

        elif response.status_code == 404:
            print("✗ ERROR: Tienda no encontrada")
            print()
            print(f"La tienda '{store_name}.myshopify.com' no existe o no es accesible.")
            print()
            print("Verifica el nombre de la tienda en SHOPIFY_STORE")

        else:
            print(f"✗ ERROR: {response.status_code}")
            print()
            print("Respuesta del servidor:")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"✗ ERROR de conexión: {str(e)}")
        return None

    print()
    print("=" * 80)
    print("INFORMACIÓN ADICIONAL:")
    print("=" * 80)
    print()
    print("El Client Credentials Grant está diseñado para apps internas de tu organización.")
    print("Los tokens obtenidos son válidos por 24 horas.")
    print()
    print("Documentación:")
    print("  - https://shopify.dev/docs/apps/build/authentication-authorization/access-tokens/client-credentials-grant")
    print()

    return None


if __name__ == "__main__":
    try:
        token = get_shopify_access_token()
        sys.exit(0 if token else 1)
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
