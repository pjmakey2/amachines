#!/usr/bin/env python
"""
Script para generar URL de instalación de la app de Shopify
"""

import os
import sys
import django
from pathlib import Path
from urllib.parse import quote

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from django.conf import settings

def generate_install_url():
    """
    Genera la URL de instalación para la app de Shopify
    """
    print("=" * 80)
    print("GENERAR URL DE INSTALACIÓN DE SHOPIFY APP")
    print("=" * 80)
    print()

    # Configuración
    store_name = settings.SHOPIFY_STORE.replace('.myshopify.com', '').replace('https://', '').replace('http://', '')
    client_id = settings.SHOPIFY_CLIENTEID

    # Scopes - usar solo los scopes esenciales para empezar
    # Puedes agregar más después
    scopes = "read_products,write_products,read_orders,write_orders,read_inventory,write_inventory"

    # Si tienes todos los scopes configurados, usar esos
    if hasattr(settings, 'SHOPIFY_ALL_PEMRS'):
        scopes = settings.SHOPIFY_ALL_PEMRS.strip()

    # Redirect URI - para apps que usan client credentials, esto puede ser una URL ficticia
    # pero debe estar en la whitelist de la app en el dev dashboard
    redirect_uri = "https://example.com/auth/callback"

    # Construir URL
    install_url = (
        f"https://{store_name}.myshopify.com/admin/oauth/authorize?"
        f"client_id={client_id}&"
        f"scope={quote(scopes)}&"
        f"redirect_uri={quote(redirect_uri)}"
    )

    print("Configuración:")
    print(f"  Tienda: {store_name}.myshopify.com")
    print(f"  Client ID: {client_id}")
    print(f"  Scopes configurados: {len(scopes.split(','))} permisos")
    print()
    print("=" * 80)
    print("URL DE INSTALACIÓN:")
    print("=" * 80)
    print()
    print(install_url)
    print()
    print("=" * 80)
    print("INSTRUCCIONES:")
    print("=" * 80)
    print()
    print("1. Copia la URL de arriba")
    print("2. Pégala en tu navegador")
    print("3. Inicia sesión en tu tienda de Shopify si te lo pide")
    print("4. Haz clic en 'Instalar app' o 'Install app'")
    print("5. Una vez instalada, ejecuta el script get_shopify_token.py")
    print()
    print("NOTA IMPORTANTE:")
    print("  El redirect_uri debe estar configurado en tu app en el Dev Dashboard.")
    print("  Ve a https://partners.shopify.com y agrega esta URL a la whitelist:")
    print(f"  {redirect_uri}")
    print()
    print("  O puedes usar Client Credentials Grant directamente después de instalar.")
    print()

    return install_url


if __name__ == "__main__":
    try:
        url = generate_install_url()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
