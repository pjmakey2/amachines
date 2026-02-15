#!/usr/bin/env python
"""
Script para cancelar documentos electrónicos por CDC.

Uso en Docker:
    docker exec -it toca3d_web python /app/am_shopify/bin/cancelar_cdc.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

# Imports después de configurar Django
from Sifen.rq_soap_handler import SoapSifen

# Lista de CDC a cancelar: (CDC, Motivo)
CDC = [
    #('01801631211001001000003022025121818286332688', 'Error en la emision del documento'),
    ('01801631211001001000004622025122317904424903', 'Error en la emision del documento'),
]

def main():
    rqsoap = SoapSifen()

    for cdc, motivo in CDC:
        print(f"Cancelando CDC: {cdc}")
        print(f"Motivo: {motivo}")
        print("-" * 50)

        try:
            rsp = rqsoap.cancelar_xde(cdc, motivo)
            print(rsp.text)
        except Exception as e:
            print(f"Error: {e}")

        print("=" * 50)

if __name__ == '__main__':
    main()
