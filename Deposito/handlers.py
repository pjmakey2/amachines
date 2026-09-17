"""Handlers del bus de eventos. Idempotentes: Deposito.clave es unica por (recibo, tipo de valor)."""
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from Deposito.models import Deposito
from OptsIO.io_business import siguiente_numero
from OptsIO.io_money import precision_monetaria
from Tesoreria.models import CuentaBancaria

# Metodo de cobro -> tipo de deposito. La retencion no se deposita (es credito fiscal).
METODOS_DEPOSITABLES = {'efectivo': 'efectivo', 'cheque': 'cheque', 'transferencia': 'transferencia', 'tarjeta': 'tarjeta'}
MONEDAS = {'GS': 'PYG', 'PYG': 'PYG', 'USD': 'USD'}


@precision_monetaria
def generar_depositos_de_cobro(event) -> dict:
    """
    cobro.recibo.aprobado -> un Deposito 'cargado' por cada tipo de valor cobrado.
    Si el negocio tiene una sola cuenta activa en esa moneda queda preasignada; tesoreria
    completa la boleta y lo verifica/aprueba, y recien ahi se acredita la cuenta.
    """
    business, payload = event.business, event.payload
    moneda = MONEDAS.get(payload.get('moneda'), 'PYG')
    cuentas = list(CuentaBancaria.objects.filter(businessobj=business, activo=True, moneda=moneda)[:2])
    creados = []
    for metodo, tipo in METODOS_DEPOSITABLES.items():
        monto = Decimal(payload.get('metodos', {}).get(metodo) or 0)
        clave = f"cobro.recibo:{event.source_id}:{metodo}"
        if monto <= 0 or Deposito.objects.filter(clave=clave).exists():
            continue
        with transaction.atomic():
            dep = Deposito(
                businessobj=business, numero=siguiente_numero(Deposito, business),
                fecha=payload.get('fecha') or datetime.now().date(), tipo=tipo, monto=monto, moneda=moneda,
                cuentaobj=cuentas[0] if len(cuentas) == 1 else None, automatico=True, clave=clave,
                origen_app=event.source_app, origen_model=event.source_model, origen_id=event.source_id,
                origen_desc=f"Recibo {payload.get('numero')} - {payload.get('cliente', '')}"[:200])
            dep.registrar_carga(None)
            dep.cargado_usuario = 'sistema (cobro)'
            dep.save()
        creados.append(dep.pk)
    return {'depositos': creados}


@precision_monetaria
def generar_deposito_de_pedido(event) -> dict:
    """ecommerce.pedido.pagado -> deposito pendiente (transferencia recibida, o efectivo si fue contra entrega)."""
    business, payload = event.business, event.payload
    clave = f"ecommerce.pedido:{event.source_id}"
    monto = Decimal(payload.get('total') or 0)
    if monto <= 0 or Deposito.objects.filter(clave=clave).exists():
        return {'depositos': []}
    moneda = MONEDAS.get(payload.get('moneda'), 'PYG')
    cuentas = list(CuentaBancaria.objects.filter(businessobj=business, activo=True, moneda=moneda)[:2])
    with transaction.atomic():
        dep = Deposito(
            businessobj=business, numero=siguiente_numero(Deposito, business), fecha=payload.get('fecha') or datetime.now().date(),
            tipo='transferencia' if payload.get('metodo_pago') == 'transferencia' else 'efectivo', monto=monto, moneda=moneda,
            cuentaobj=cuentas[0] if len(cuentas) == 1 else None, boleta_numero=(payload.get('referencia') or '')[:60],
            automatico=True, clave=clave, origen_app=event.source_app, origen_model=event.source_model, origen_id=event.source_id,
            origen_desc=f"Pedido online {payload.get('numero')} - {payload.get('cliente', '')}"[:200])
        dep.registrar_carga(None)
        dep.cargado_usuario = 'sistema (tienda online)'
        dep.save()
    return {'depositos': [dep.pk]}
