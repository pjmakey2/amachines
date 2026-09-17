"""
RG90 (Marangatu) - Registro mensual de comprobantes, formato TXT separado por tabuladores.

Ventas (tipo de registro 1): 17 columnas; notas de credito/debito agregan comprobante y timbrado asociados.
Compras (tipo de registro 2): mismas columnas + 'no imputar'.
Anchos y relleno igual que los archivos de referencia: identificacion 15, nombre 80, montos 20 (derecha).
"""
import calendar
from datetime import date, datetime
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from Contabilidad.motor import tasa_a_guaranies
from OptsIO.io_money import precision_monetaria
from Sifen.models import DocumentHeader

TIPO_COMPROBANTE = {'FE': '109', 'NC': '110', 'ND': '111'}


def _monto(valor) -> str:
    return str(int(Decimal(str(valor or 0)).quantize(Decimal('1')))).rjust(20)


def _fila(columnas) -> str:
    return '\t'.join(columnas)


def _cabecera(ident_tipo, ident, nombre, comprobante, fecha, timbrado, numero):
    return [ident_tipo, str(ident).ljust(15)[:15], str(nombre).upper().ljust(80)[:80], comprobante,
            fecha.strftime('%d/%m/%Y'), str(timbrado or '').rjust(8)[:8], str(numero).ljust(15)[:15]]


def rango_periodo(periodo: str):
    """'2026-08' -> (date(2026,8,1), date(2026,8,31))"""
    anho, mes = int(periodo[:4]), int(periodo[5:7])
    return date(anho, mes, 1), date(anho, mes, calendar.monthrange(anho, mes)[1])


@precision_monetaria
def ventas(business, periodo: str) -> dict:
    desde, hasta = rango_periodo(periodo)
    docs = DocumentHeader.objects.filter(ek_bs_ruc=business.ruc, ek_estado='Aprobado', doc_tipo__in=list(TIPO_COMPROBANTE),
                                         doc_fecha__range=(desde, hasta)).order_by('doc_fecha', 'doc_numero')
    lineas, total = [], Decimal(0)
    for d in docs:
        factor = tasa_a_guaranies(d.doc_moneda, d.doc_fecha, d.tasa_cambio)
        g10, g5, exenta = [Decimal(str(v or 0)) * factor for v in (d.get_total_gravada_10(), d.get_total_gravada_5(), d.get_total_exenta())]
        if d.pdv_innominado:
            ident_tipo, ident, nombre = '15', 'X', 'SIN NOMBRE'
        else:
            ident_tipo, ident, nombre = ('11' if d.pdv_es_contribuyente else '12'), d.pdv_ruc, d.pdv_nombrefactura
        numero = f"{d.doc_establecimiento:03d}-{d.doc_expedicion:03d}-{d.doc_numero:07d}"
        cols = ['1'] + _cabecera(ident_tipo, ident, nombre, TIPO_COMPROBANTE[d.doc_tipo], d.doc_fecha, d.ek_timbrado, numero)
        cols += [_monto(g10), _monto(g5), _monto(exenta), _monto(g10 + g5 + exenta),
                 '2' if d.doc_cre_tipo_cod == 2 else '1', 'N' if d.doc_moneda in ('GS', 'PYG') else 'S', 'S', 'S', 'N']
        if d.doc_tipo in ('NC', 'ND'):
            asociado = f"{d.doc_relacion_establecimiento:03d}-{d.doc_relacion_expedicion:03d}-{d.doc_relacion_numero:07d}"
            cols += [asociado.ljust(15), str(d.doc_relacion_timbrado or d.ek_timbrado or '').rjust(8)[:8]]
        lineas.append(_fila(cols))
        total += (g10 + g5 + exenta) * (-1 if d.doc_tipo == 'NC' else 1)
    return _guardar(business, periodo, 'V', lineas, total)


@precision_monetaria
def compras(business, periodo: str) -> dict:
    """Comprobantes de compra = gastos aprobados con factura (plugin Egreso). Los 'a rendir' entran al rendirse."""
    if not apps.is_installed('Egreso'):
        return {'error': 'El registro de compras requiere el plugin Egreso'}
    desde, hasta = rango_periodo(periodo)
    gastos = apps.get_model('Egreso', 'Gasto').objects.filter(
        businessobj=business, anulado=False, estado='aprobado', factura_fecha__range=(desde, hasta)).exclude(
        factura_numero='').select_related('proveedorobj').order_by('factura_fecha', 'id')
    lineas, total = [], Decimal(0)
    for g in gastos:
        if g.tipo == 'a_rendir' and not g.rendido:
            continue
        factor = tasa_a_guaranies(g.moneda, g.factura_fecha, g.tasa_cambio)
        g10, g5, exenta = g.gravada_10 * factor, g.gravada_5 * factor, g.exenta * factor
        ident, nombre = (g.proveedorobj.ruc, g.proveedorobj.nombre) if g.proveedorobj_id else ('X', g.beneficiario or 'SIN NOMBRE')
        cols = ['2'] + _cabecera('11' if g.proveedorobj_id else '15', ident, nombre, '109', g.factura_fecha, g.factura_timbrado, g.factura_numero)
        cols += [_monto(g10), _monto(g5), _monto(exenta), _monto(g10 + g5 + exenta),
                 '2' if g.factura_condicion == 'credito' else '1', 'N' if g.moneda == 'PYG' else 'S', 'S', 'S', 'N', 'N']
        lineas.append(_fila(cols))
        total += g10 + g5 + exenta
    return _guardar(business, periodo, 'C', lineas, total)


def _guardar(business, periodo, tipo, lineas, total) -> dict:
    desde, _ = rango_periodo(periodo)
    nombre = f"contabilidad/rg90/{business.ruc}_REG_{desde:%m%Y}_{tipo}0001_{datetime.now():%H%M%S}.txt"
    contenido = ('\r\n'.join(lineas) + ('\r\n' if lineas else '')).encode('latin-1', errors='replace')
    guardado = default_storage.save(nombre, ContentFile(contenido))
    return {'success': True, 'archivo': f'{settings.MEDIA_URL}{guardado}', 'registros': len(lineas), 'total': float(total)}
