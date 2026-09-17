"""
Handlers del bus de eventos: traducen cada cierre de operacion a montos en guaranies y delegan
en MotorAsientos. No importan otros plugins: todo llega en event.payload (las ventas se leen
del core Sifen). Son idempotentes (Asiento.clave).
"""
from decimal import Decimal

from Contabilidad.motor import MotorAsientos, tasa_a_guaranies
from OptsIO.io_money import precision_monetaria
from Sifen.models import DocumentHeader


def _d(value) -> Decimal:
    return Decimal(str(value or 0))


def _gs(payload, fecha, *claves) -> list:
    """Montos del payload llevados a guaranies."""
    factor = tasa_a_guaranies(payload.get('moneda'), fecha, payload.get('tasa_cambio'))
    return [_d(payload.get(c)) * factor for c in claves]


@precision_monetaria
def asiento_venta(event) -> dict:
    """sifen.documento.aprobado: factura/ND -> venta; NC -> devolucion. Autofacturas no son ventas."""
    doc = DocumentHeader.objects.get(pk=event.source_id)
    if doc.doc_tipo not in ('FE', 'ND', 'NC'):
        return {'omitido': f'tipo de documento {doc.doc_tipo}'}
    factor = tasa_a_guaranies(doc.doc_moneda, doc.doc_fecha, doc.tasa_cambio)
    g10, g5, exenta = [_d(v) * factor for v in (doc.get_total_gravada_10(), doc.get_total_gravada_5(), doc.get_total_exenta())]
    iva_10, iva_5 = _d(doc.get_ivas_10_master()) * factor, _d(doc.get_ivas_5_master()) * factor
    total = g10 + g5 + exenta
    numero = f"{doc.doc_establecimiento:03d}-{doc.doc_expedicion:03d}-{doc.doc_numero:07d}"
    ctx = {'numero': numero, 'cliente': doc.pdv_nombrefactura}
    if doc.doc_tipo == 'NC':
        montos = {'neto': total - iva_10 - iva_5, 'iva_10': iva_10, 'iva_5': iva_5, 'total': total}
        return MotorAsientos().generar(event, 'sifen.nc.emitida', doc.doc_fecha, montos, ctx=ctx)
    credito = doc.doc_cre_tipo_cod == 2
    montos = {'total_credito': total if credito else 0, 'total_contado': 0 if credito else total,
              'neto_10': g10 - iva_10, 'neto_5': g5 - iva_5, 'exenta': exenta, 'iva_10': iva_10, 'iva_5': iva_5}
    return MotorAsientos().generar(event, 'sifen.factura.emitida', doc.doc_fecha, montos, ctx=ctx)


@precision_monetaria
def asiento_cobro(event) -> dict:
    p = event.payload
    metodos = {m: _d(v) for m, v in (p.get('metodos') or {}).items()}
    factor = tasa_a_guaranies(p.get('moneda'), p.get('fecha'))
    retencion = metodos.get('retencion', 0) * factor
    total = _d(p.get('total')) * factor
    montos = {'depositable': total - retencion, 'retencion': retencion, 'total': total}
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), montos, ctx=p)


@precision_monetaria
def asiento_deposito(event) -> dict:
    p = event.payload
    monto, = _gs(p, p.get('fecha'), 'monto')
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), {'monto': monto, 'monto_valores': monto},
                                   refs={'monto': ('cuenta_bancaria', p.get('cuenta_id'))}, ctx=p)


def _montos_comprobante(p) -> dict:
    total, iva_10, iva_5 = _gs(p, p.get('fecha'), 'total', 'iva_10', 'iva_5')
    return {'neto': total - iva_10 - iva_5, 'iva_10': iva_10, 'iva_5': iva_5, 'total': total}


@precision_monetaria
def asiento_gasto(event) -> dict:
    """Un gasto a rendir no se asienta al aprobarse (todavia no hay comprobante): se asienta al rendirse."""
    p = event.payload
    if p.get('tipo') == 'a_rendir':
        return {'omitido': 'gasto a rendir: se asienta en la rendición'}
    montos = _montos_comprobante(p)
    caja_chica = p.get('tipo') == 'caja_chica'
    montos.update({'total_proveedor': 0 if caja_chica else montos['total'], 'total_caja_chica': montos['total'] if caja_chica else 0})
    refs = {'neto': ('categoria_gasto', p.get('categoria_id')), 'total_caja_chica': ('caja', p.get('caja_id'))}
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), montos, refs=refs, ctx=p)


@precision_monetaria
def asiento_gasto_rendido(event) -> dict:
    p = event.payload
    montos = _montos_comprobante(p)
    devolucion, = _gs(p, p.get('fecha'), 'devolucion')
    montos.update({'devolucion_banco': devolucion if p.get('devolucion_cuenta_id') else 0,
                   'devolucion_caja': devolucion if p.get('devolucion_caja_id') else 0,
                   'total_mas_devolucion': montos['total'] + devolucion})
    refs = {'neto': ('categoria_gasto', p.get('categoria_id')),
            'devolucion_banco': ('cuenta_bancaria', p.get('devolucion_cuenta_id')),
            'devolucion_caja': ('caja', p.get('devolucion_caja_id'))}
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), montos, refs=refs, ctx=p)


@precision_monetaria
def asiento_pago(event) -> dict:
    """Lo pagado de gastos a rendir es una entrega de fondos (anticipo), no una cancelacion de proveedores."""
    p = event.payload
    factor = tasa_a_guaranies(p.get('moneda'), p.get('fecha'))
    anticipos = sum((_d(g.get('monto')) for g in p.get('gastos', []) if g.get('tipo') == 'a_rendir'), Decimal(0)) * factor
    total = _d(p.get('total')) * factor
    en_caja = p.get('medio') == 'efectivo'
    montos = {'a_proveedores': total - anticipos, 'a_anticipos': anticipos,
              'total_banco': 0 if en_caja else total, 'total_caja': total if en_caja else 0}
    refs = {'total_banco': ('cuenta_bancaria', p.get('cuenta_id')), 'total_caja': ('caja', p.get('caja_id'))}
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), montos, refs=refs, ctx=p)


@precision_monetaria
def asiento_transferencia(event) -> dict:
    p = event.payload
    sale, = _gs(p, p.get('fecha'), 'monto')
    montos = {'in_banco': sale if p.get('destino_cuenta_id') else 0, 'in_caja': sale if p.get('destino_caja_id') else 0,
              'out_banco': sale if p.get('origen_cuenta_id') else 0, 'out_caja': sale if p.get('origen_caja_id') else 0}
    refs = {'in_banco': ('cuenta_bancaria', p.get('destino_cuenta_id')), 'in_caja': ('caja', p.get('destino_caja_id')),
            'out_banco': ('cuenta_bancaria', p.get('origen_cuenta_id')), 'out_caja': ('caja', p.get('origen_caja_id'))}
    return MotorAsientos().generar(event, event.event_type, p.get('fecha'), montos, refs=refs, ctx=p)


def reverso(event) -> dict:
    """*.anulado / sifen.documento.cancelado: contra-asiento de lo que genero la operacion."""
    return MotorAsientos().revertir(event)
