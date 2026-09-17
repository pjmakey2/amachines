"""
Egresos: proveedores, gastos (comun / a rendir / caja chica), gastos recurrentes,
pagos a proveedores (efectivo, transferencia, cheque) y transferencias internas.

Las transiciones cargado -> verificado -> aprobado -> (anulado) se operan con
OptsIO.mng_workflow.MWorkflow; aca viven la carga de datos y las consultas.
"""
import calendar
import logging
import re
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import HttpRequest, QueryDict

from Egreso.models import (
    Proveedor, CategoriaGasto, GastoRecurrente, Gasto, PagoProveedor, PagoProveedorDetalle,
    TransferenciaInterna,
)
from OptsIO import events
from OptsIO.io_business import get_active_business, siguiente_numero, user_label
from OptsIO.io_json import from_json, to_json
from OptsIO.io_money import iva_incluido, precision_monetaria
from OptsIO.io_rpt import IoRpt
from Tesoreria.mng_tesoreria import MTesoreria
from Tesoreria.models import Caja, Chequera, CuentaBancaria

logger = logging.getLogger(__name__)

RE_DECIMAL = re.compile(r'^\d+(\.\d+)?$')
RE_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CATALOGOS = {'Proveedor': Proveedor, 'CategoriaGasto': CategoriaGasto, 'GastoRecurrente': GastoRecurrente}
EN_USO = {
    'Proveedor': lambda ids: Gasto.objects.filter(proveedorobj_id__in=ids).exists(),
    'CategoriaGasto': lambda ids: (Gasto.objects.filter(categoriaobj_id__in=ids).exists()
                                   or GastoRecurrente.objects.filter(categoriaobj_id__in=ids).exists()),
    'GastoRecurrente': lambda ids: False,
}


def _dec(value) -> Decimal:
    """Decimal desde el form; vacio o invalido = 0 (la validacion de > 0 la hace cada metodo)."""
    texto = str(value if value is not None else '').strip()
    return Decimal(texto) if RE_DECIMAL.match(texto) else Decimal(0)


def _fecha(value):
    texto = str(value or '').strip()[:10]
    return datetime.strptime(texto, '%Y-%m-%d').date() if RE_FECHA.match(texto) else None


def _bool(value) -> bool:
    return str(value).lower() in ('true', '1', 'on', 'si')


def fecha_aplicacion(anho: int, mes: int, dia: int) -> date:
    """Dia de aplicacion dentro del mes; si el mes es mas corto, su ultimo dia."""
    return date(anho, mes, min(dia, calendar.monthrange(anho, mes)[1]))


def sumar_meses(fecha: date, meses: int, dia: int) -> date:
    total = fecha.year * 12 + (fecha.month - 1) + meses
    return fecha_aplicacion(total // 12, total % 12 + 1, dia)


class MEgreso:

    # ------------------------------------------------------------------ Catalogos

    def delete_catalogo(self, *args, **kwargs) -> dict:
        q = kwargs.get('qdict', {})
        model = CATALOGOS.get(q.get('model_name'))
        bobj = get_active_business(kwargs.get('userobj'))
        if not model or not bobj:
            return {'msgs': [{'error': 'Solicitud invalida'}]}
        ids = list(model.objects.filter(pk__in=from_json(q.get('ids', '[]')), businessobj=bobj).values_list('pk', flat=True))
        if EN_USO[q.get('model_name')](ids):
            return {'msgs': [{'error': 'El registro tiene gastos asociados: desactivelo en lugar de borrarlo'}]}
        n, _ = model.objects.filter(pk__in=ids).delete()
        return {'msgs': [{'success': f'{n} registro(s) borrado(s)'}]}

    # ------------------------------------------------------------------ Gastos recurrentes

    @precision_monetaria
    def create_recurrente(self, *args, **kwargs) -> tuple:
        """c_a de GastoRecurrenteCreateUi (ficha del proveedor)."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        proveedor = Proveedor.objects.filter(pk=f.get('proveedorobj_id') or 0, businessobj=bobj).first()
        categoria = CategoriaGasto.objects.filter(pk=f.get('categoriaobj_id') or 0, businessobj=bobj).first()
        monto, inicio, fin = _dec(f.get('monto')), _fecha(f.get('fecha_inicio')), _fecha(f.get('fecha_fin'))
        dia = int(_dec(f.get('dia_aplicacion')))
        if not proveedor or not categoria:
            return {'error': 'Proveedor y categoría son obligatorios'}, args, kwargs
        if not (f.get('concepto') or '').strip() or monto <= 0 or not inicio:
            return {'error': 'Concepto, monto y fecha de inicio son obligatorios'}, args, kwargs
        if not 1 <= dia <= 31:
            return {'error': 'El día de aplicación debe estar entre 1 y 31'}, args, kwargs
        if f.get('frecuencia') not in GastoRecurrente.MESES:
            return {'error': 'Frecuencia inválida'}, args, kwargs

        proxima = fecha_aplicacion(inicio.year, inicio.month, dia)
        if proxima < inicio:
            proxima = sumar_meses(proxima, 1, dia)
        datos = dict(proveedorobj=proveedor, categoriaobj=categoria, concepto=f.get('concepto').strip()[:300],
                     monto=monto, moneda=f.get('moneda') or 'PYG', frecuencia=f.get('frecuencia'),
                     dia_aplicacion=dia, fecha_inicio=inicio, fecha_fin=fin, activo=_bool(f.get('activo', 'true')))
        if f.get('id'):
            rec = GastoRecurrente.objects.filter(pk=f.get('id'), businessobj=bobj).first()
            if not rec:
                return {'error': 'Gasto recurrente inexistente'}, args, kwargs
            # La proxima fecha solo se recalcula si cambio la programacion
            if (rec.dia_aplicacion, rec.fecha_inicio, rec.frecuencia) != (dia, inicio, f.get('frecuencia')):
                datos['proxima_fecha'] = max(proxima, fecha_aplicacion(date.today().year, date.today().month, dia))
            GastoRecurrente.objects.filter(pk=rec.pk).update(
                actualizado_fecha=datetime.now(), actualizado_usuario=user_label(userobj), **datos)
            return {'success': 'Gasto recurrente actualizado', 'record_id': rec.pk}, args, kwargs
        rec = GastoRecurrente.objects.create(
            businessobj=bobj, proxima_fecha=proxima, cargado_fecha=datetime.now(),
            cargado_usuario=user_label(userobj), **datos)
        return {'success': f'Gasto recurrente creado. Primera generación: {proxima:%d/%m/%Y}', 'record_id': rec.pk}, args, kwargs

    @precision_monetaria
    def generar_recurrentes(self, hasta: date = None) -> dict:
        """
        Genera los gastos de los recurrentes vencidos (proxima_fecha <= hasta). Idempotente:
        (recurrenteobj, periodo) es unico, asi que re-ejecutar no duplica.
        """
        hasta = hasta or date.today()
        generados = 0
        recurrentes = GastoRecurrente.objects.filter(
            activo=True, proxima_fecha__lte=hasta, proveedorobj__activo=True).select_related('proveedorobj')
        for rec_id in list(recurrentes.values_list('pk', flat=True)):
            with transaction.atomic():
                rec = GastoRecurrente.objects.select_for_update().get(pk=rec_id)
                while rec.activo and rec.proxima_fecha <= hasta:
                    if rec.fecha_fin and rec.proxima_fecha > rec.fecha_fin:
                        rec.activo = False
                        break
                    periodo = rec.proxima_fecha.strftime('%Y-%m-%d')
                    if not Gasto.objects.filter(recurrenteobj=rec, periodo=periodo).exists():
                        gasto = Gasto(
                            businessobj=rec.businessobj, numero=siguiente_numero(Gasto, rec.businessobj),
                            tipo='comun', fecha=rec.proxima_fecha, proveedorobj=rec.proveedorobj,
                            categoriaobj=rec.categoriaobj, concepto=rec.concepto, moneda=rec.moneda,
                            gravada_10=rec.monto, iva_10=iva_incluido(rec.monto, 11),
                            total=rec.monto, saldo=rec.monto, recurrenteobj=rec, periodo=periodo)
                        gasto.registrar_carga(None)
                        gasto.cargado_usuario = 'sistema (recurrente)'
                        gasto.save()
                        generados += 1
                    rec.proxima_fecha = sumar_meses(rec.proxima_fecha, GastoRecurrente.MESES[rec.frecuencia], rec.dia_aplicacion)
                rec.save(update_fields=['proxima_fecha', 'activo'])
        return {'success': f'{generados} gasto(s) recurrente(s) generado(s)', 'generados': generados}

    def generar_recurrentes_ui(self, *args, **kwargs) -> dict:
        """Disparo manual desde la pantalla (el automatico corre por Celery beat)."""
        return self.generar_recurrentes()

    # ------------------------------------------------------------------ Gastos

    @precision_monetaria
    def create_gasto(self, *args, **kwargs) -> tuple:
        """c_a de GastoCreateUi. Un gasto solo se edita mientras esta 'cargado'."""
        userobj, files = kwargs.get('userobj'), kwargs.get('files') or {}
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        tipo = f.get('tipo')
        if tipo not in dict(Gasto.TIPOS):
            return {'error': 'Tipo de gasto inválido'}, args, kwargs
        categoria = CategoriaGasto.objects.filter(pk=f.get('categoriaobj_id') or 0, businessobj=bobj).first()
        proveedor = Proveedor.objects.filter(pk=f.get('proveedorobj_id') or 0, businessobj=bobj).first()
        caja = Caja.objects.filter(pk=f.get('cajaobj_id') or 0, businessobj=bobj).first()
        fecha = _fecha(f.get('fecha'))
        if not categoria or not fecha or not (f.get('concepto') or '').strip():
            return {'error': 'Fecha, categoría y concepto son obligatorios'}, args, kwargs
        if tipo == 'comun' and not proveedor:
            return {'error': 'Un gasto común requiere proveedor'}, args, kwargs
        if tipo == 'caja_chica' and (not caja or caja.tipo != 'chica'):
            return {'error': 'Seleccione la caja chica que paga el gasto'}, args, kwargs
        if not proveedor and not (f.get('beneficiario') or '').strip():
            return {'error': 'Indique el proveedor o el beneficiario'}, args, kwargs

        exenta, g5, g10 = _dec(f.get('exenta')), _dec(f.get('gravada_5')), _dec(f.get('gravada_10'))
        total, presupuesto = exenta + g5 + g10, _dec(f.get('presupuesto_monto'))
        if tipo == 'a_rendir' and presupuesto <= 0:
            return {'error': 'Un gasto a rendir requiere el monto del presupuesto'}, args, kwargs
        if tipo != 'a_rendir' and total <= 0:
            return {'error': 'Cargue los montos del comprobante (exenta / gravadas)'}, args, kwargs
        moneda = caja.moneda if tipo == 'caja_chica' else (f.get('moneda') or 'PYG')
        datos = dict(
            tipo=tipo, fecha=fecha, proveedorobj=proveedor, categoriaobj=categoria,
            beneficiario=(f.get('beneficiario') or '').strip()[:200], concepto=f.get('concepto').strip()[:300],
            moneda=moneda, tasa_cambio=_dec(f.get('tasa_cambio')) or Decimal(1),
            factura_numero=(f.get('factura_numero') or '').strip(), factura_timbrado=(f.get('factura_timbrado') or '').strip(),
            factura_fecha=_fecha(f.get('factura_fecha')), factura_condicion=f.get('factura_condicion') or 'contado',
            vencimiento=_fecha(f.get('vencimiento')), exenta=exenta, gravada_5=g5, gravada_10=g10,
            iva_5=iva_incluido(g5, 21), iva_10=iva_incluido(g10, 11),
            total=total, presupuesto_monto=presupuesto if tipo == 'a_rendir' else 0,
            presupuesto_ref=(f.get('presupuesto_ref') or '').strip()[:120],
            responsable=(f.get('responsable') or '').strip()[:120],
            cajaobj=caja if tipo == 'caja_chica' else None)

        with transaction.atomic():
            if f.get('id'):
                gasto = Gasto.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not gasto:
                    return {'error': 'Gasto inexistente'}, args, kwargs
                if gasto.estado != 'cargado' or gasto.anulado:
                    return {'error': f'El gasto está {gasto.estado}: ya no se puede modificar'}, args, kwargs
                for campo, valor in datos.items():
                    setattr(gasto, campo, valor)
                gasto.actualizado_fecha, gasto.actualizado_usuario = datetime.now(), user_label(userobj)
                msg = f'Gasto {gasto.get_numero_display()} actualizado'
            else:
                gasto = Gasto(businessobj=bobj, numero=siguiente_numero(Gasto, bobj), **datos)
                gasto.registrar_carga(userobj)
                msg = f'Gasto {gasto.get_numero_display()} cargado'
            gasto.recalcular_pago()
            if files.get('archivo'):
                gasto.archivo = File(files.get('archivo'), name=f"gasto_{gasto.numero}_{files.get('archivo').name}")
            gasto.save()
        return {'success': msg, 'record_id': gasto.pk}, args, kwargs

    @precision_monetaria
    def rendir_gasto(self, *args, **kwargs) -> tuple:
        """
        c_a de GastoRendirUi: carga el comprobante real de un gasto a rendir ya aprobado.
        Si se entrego mas dinero que el gastado, la diferencia vuelve a una cuenta/caja.
        """
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        exenta, g5, g10 = _dec(f.get('exenta')), _dec(f.get('gravada_5')), _dec(f.get('gravada_10'))
        total = exenta + g5 + g10
        if total <= 0 or not (f.get('factura_numero') or '').strip():
            return {'error': 'Cargue el número de factura y los montos del comprobante'}, args, kwargs
        cuenta = CuentaBancaria.objects.filter(pk=f.get('devolucion_cuentaobj_id') or 0, businessobj=bobj).first()
        caja = Caja.objects.filter(pk=f.get('devolucion_cajaobj_id') or 0, businessobj=bobj).first()

        with transaction.atomic():
            gasto = Gasto.objects.select_for_update().filter(pk=f.get('id') or 0, businessobj=bobj).first()
            if not gasto or gasto.tipo != 'a_rendir':
                return {'error': 'Gasto a rendir inexistente'}, args, kwargs
            if gasto.estado != 'aprobado' or gasto.anulado:
                return {'error': 'Solo se rinde un gasto aprobado'}, args, kwargs
            if gasto.rendido:
                return {'info': 'El gasto ya fue rendido'}, args, kwargs
            devolucion = gasto.pagado - total
            if devolucion > 0:
                error = MTesoreria().validar_movimiento('ingreso', devolucion, cuentaobj=cuenta, cajaobj=caja, businessobj=bobj)
                if error:
                    return {'error': f'Sobran {devolucion:,.0f} a devolver. {error}'}, args, kwargs
                MTesoreria().registrar_movimiento(
                    bobj, date.today(), 'ingreso', devolucion, f"Devolución rendición gasto {gasto.get_numero_display()}",
                    cuentaobj=cuenta, cajaobj=caja, origen=gasto, clave=f"egreso.gasto:{gasto.pk}:devolucion", userobj=userobj)
                gasto.pagado = total
            gasto.factura_numero = f.get('factura_numero').strip()
            gasto.factura_timbrado = (f.get('factura_timbrado') or '').strip()
            gasto.factura_fecha = _fecha(f.get('factura_fecha')) or date.today()
            proveedor = Proveedor.objects.filter(pk=f.get('proveedorobj_id') or 0, businessobj=bobj).first()
            if proveedor:
                gasto.proveedorobj = proveedor
            gasto.exenta, gasto.gravada_5, gasto.gravada_10, gasto.total = exenta, g5, g10, total
            gasto.iva_5 = iva_incluido(g5, 21)
            gasto.iva_10 = iva_incluido(g10, 11)
            gasto.rendido, gasto.rendido_fecha, gasto.rendido_usuario = True, datetime.now(), user_label(userobj)
            gasto.recalcular_pago()
            gasto.save()
            events.emit('egreso.gasto.rendido', gasto, business=bobj, userobj=userobj,
                        payload={**gasto.get_workflow_payload(), 'presupuesto': str(gasto.presupuesto_monto),
                                 'devolucion': str(max(devolucion, Decimal(0)))})
        msg = f'Gasto {gasto.get_numero_display()} rendido.'
        if devolucion > 0:
            msg += f' Devolución registrada: {devolucion:,.0f}.'
        if gasto.saldo > 0:
            msg += f' Queda un saldo a pagar de {gasto.saldo:,.0f}.'
        return {'success': msg, 'record_id': gasto.pk}, args, kwargs

    @precision_monetaria
    def get_gastos_pendientes(self, *args, **kwargs) -> dict:
        """Gastos aprobados con saldo, para armar un pago. Filtra por proveedor si se indica."""
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        qs = Gasto.objects.filter(businessobj=bobj, anulado=False, estado='aprobado', saldo__gt=0).select_related('proveedorobj')
        if q.get('proveedor_id'):
            qs = qs.filter(proveedorobj_id=q.get('proveedor_id'))
        else:
            qs = qs.filter(proveedorobj__isnull=True)
        return {'success': True, 'gastos': [{
            'id': g.pk, 'numero': g.get_numero_display(), 'fecha': g.fecha.strftime('%Y-%m-%d'), 'tipo': g.get_tipo_display(),
            'concepto': g.concepto, 'beneficiario': g.get_beneficiario(), 'factura': g.factura_numero,
            'vencimiento': g.vencimiento.strftime('%Y-%m-%d') if g.vencimiento else '',
            'moneda': g.moneda, 'total': float(g.monto_a_pagar), 'saldo': float(g.saldo),
        } for g in qs.order_by('vencimiento', 'fecha')]}

    # ------------------------------------------------------------------ Pagos a proveedores

    @precision_monetaria
    def create_pago(self, *args, **kwargs) -> tuple:
        """c_a de PagoProveedorCreateUi. `detalles` = [{gasto_id, monto}]. Se edita solo en 'cargado'."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        detalles = [d for d in (f.get('detalles') or []) if _dec(d.get('monto')) > 0]
        fecha, medio = _fecha(f.get('fecha')), f.get('medio')
        if not fecha or medio not in dict(PagoProveedor.MEDIOS) or not detalles:
            return {'error': 'Fecha, medio de pago y al menos un gasto con monto son obligatorios'}, args, kwargs
        gastos = {g.pk: g for g in Gasto.objects.filter(
            pk__in=[d.get('gasto_id') for d in detalles], businessobj=bobj, anulado=False, estado='aprobado')}
        if len(gastos) != len(detalles):
            return {'error': 'Hay gastos inexistentes o no aprobados en el pago'}, args, kwargs
        if len({g.proveedorobj_id for g in gastos.values()}) > 1 or len({g.moneda for g in gastos.values()}) > 1:
            return {'error': 'Todos los gastos de un pago deben ser del mismo proveedor y moneda'}, args, kwargs
        for d in detalles:
            g = gastos[int(d.get('gasto_id'))]
            if _dec(d.get('monto')) > g.saldo:
                return {'error': f'El gasto {g.get_numero_display()} tiene saldo {g.saldo:,.0f}'}, args, kwargs

        primero = next(iter(gastos.values()))
        caja = Caja.objects.filter(pk=f.get('cajaobj_id') or 0, businessobj=bobj).first() if medio == 'efectivo' else None
        cuenta = CuentaBancaria.objects.filter(pk=f.get('cuentaobj_id') or 0, businessobj=bobj).first() if medio == 'transferencia' else None
        chequera = Chequera.objects.filter(pk=f.get('chequeraobj_id') or 0, businessobj=bobj).first() if medio == 'cheque' else None
        fondo = caja or cuenta or (chequera.cuentaobj if chequera else None)
        if not fondo:
            return {'error': 'Indique de dónde salen los fondos (caja, cuenta o chequera)'}, args, kwargs
        if fondo.moneda != primero.moneda:
            return {'error': f'Los gastos son en {primero.moneda} y el origen de fondos en {fondo.moneda}'}, args, kwargs
        datos = dict(
            fecha=fecha, proveedorobj=primero.proveedorobj, beneficiario=primero.get_beneficiario()[:200], medio=medio,
            cajaobj=caja, cuentaobj=cuenta, chequeraobj=chequera, cheque_fecha_pago=_fecha(f.get('cheque_fecha_pago')),
            referencia=(f.get('referencia') or '').strip()[:120], moneda=primero.moneda,
            total=sum(_dec(d.get('monto')) for d in detalles), observacion=(f.get('observacion') or '').strip()[:300])

        with transaction.atomic():
            if f.get('id'):
                pago = PagoProveedor.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not pago:
                    return {'error': 'Pago inexistente'}, args, kwargs
                if pago.estado != 'cargado' or pago.anulado:
                    return {'error': f'El pago está {pago.estado}: ya no se puede modificar'}, args, kwargs
                for campo, valor in datos.items():
                    setattr(pago, campo, valor)
                pago.actualizado_fecha, pago.actualizado_usuario = datetime.now(), user_label(userobj)
                pago.save()
                pago.detalles.all().delete()
                msg = f'Pago {pago.get_numero_display()} actualizado'
            else:
                pago = PagoProveedor(businessobj=bobj, numero=siguiente_numero(PagoProveedor, bobj), **datos)
                pago.registrar_carga(userobj)
                pago.save()
                msg = f'Pago {pago.get_numero_display()} cargado. Se hace efectivo al aprobarse.'
            PagoProveedorDetalle.objects.bulk_create([
                PagoProveedorDetalle(pagoobj=pago, gastoobj=gastos[int(d.get('gasto_id'))], monto=_dec(d.get('monto')))
                for d in detalles])
        return {'success': msg, 'record_id': pago.pk}, args, kwargs

    def get_pago(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        pago = PagoProveedor.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not pago:
            return {'error': 'Pago inexistente'}
        return {'success': True, 'detalles': [{
            'gasto_id': d.gastoobj_id, 'numero': d.gastoobj.get_numero_display(), 'concepto': d.gastoobj.concepto,
            'factura': d.gastoobj.factura_numero, 'saldo': float(d.gastoobj.saldo), 'monto': float(d.monto),
        } for d in pago.detalles.select_related('gastoobj')]}

    def imprimir_cheque(self, *args, **kwargs) -> dict:
        """PDF del cheque de un pago aprobado, para imprimir sobre el formulario del banco."""
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        pago = PagoProveedor.objects.filter(pk=q.get('id') or 0, businessobj=bobj).select_related('chequeobj').first()
        if not pago or not pago.chequeobj_id:
            return {'error': 'El pago no tiene un cheque emitido (se emite al aprobarse)'}
        if pago.chequeobj.estado == 'anulado':
            return {'error': 'El cheque está anulado'}
        mq = QueryDict(mutable=True)
        mq.update({
            'tmpl': 'Egreso/ChequeRptUi.html', 'model_app_name': 'Egreso', 'model_name': 'PagoProveedor',
            'pk': pago.pk, 'dattrs': to_json({'media_path': True}), 'dbcon': 'default',
            'surround': 'BaseStaticReportBS5.html', 'g_pdf': 0, 'g_pdf_kit': 1, 'orientation': 'Landscape',
            'page-height': '80', 'page-width': '180', 'margin-top': '0', 'margin-right': '0',
            'margin-bottom': '0', 'margin-left': '0', 'no-outline': None,
        })
        mrq = HttpRequest()
        mrq.user, mrq.method, mrq.GET = userobj, 'GET', mq
        rp = IoRpt().rpt_view(mrq)
        with open(rp.get('pdf_file'), 'rb') as fobj:
            name = default_storage.save(f'egreso/cheques/cheque_{pago.chequeobj.numero}_{pago.pk}.pdf', File(fobj))
        return {'success': f'Cheque {pago.chequeobj.numero} listo para imprimir', 'pdf_file': f'{settings.MEDIA_URL}{name}'}

    # ------------------------------------------------------------------ Transferencias internas

    @precision_monetaria
    def create_transferencia(self, *args, **kwargs) -> tuple:
        """c_a de TransferenciaInternaCreateUi. Se edita solo en 'cargado'; mueve fondos al aprobarse."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        cuenta = lambda k: CuentaBancaria.objects.filter(pk=f.get(k) or 0, businessobj=bobj).first()
        caja = lambda k: Caja.objects.filter(pk=f.get(k) or 0, businessobj=bobj).first()
        fecha, monto = _fecha(f.get('fecha')), _dec(f.get('monto'))
        if not fecha or monto <= 0:
            return {'error': 'Fecha y monto son obligatorios'}, args, kwargs
        datos = dict(fecha=fecha, monto=monto, monto_destino=_dec(f.get('monto_destino')),
                     origen_cuentaobj=cuenta('origen_cuentaobj_id'), origen_cajaobj=caja('origen_cajaobj_id'),
                     destino_cuentaobj=cuenta('destino_cuentaobj_id'), destino_cajaobj=caja('destino_cajaobj_id'),
                     concepto=(f.get('concepto') or '').strip()[:300], referencia=(f.get('referencia') or '').strip()[:120])
        with transaction.atomic():
            if f.get('id'):
                tr = TransferenciaInterna.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not tr:
                    return {'error': 'Transferencia inexistente'}, args, kwargs
                if tr.estado != 'cargado' or tr.anulado:
                    return {'error': f'La transferencia está {tr.estado}: ya no se puede modificar'}, args, kwargs
                for campo, valor in datos.items():
                    setattr(tr, campo, valor)
                tr.actualizado_fecha, tr.actualizado_usuario = datetime.now(), user_label(userobj)
            else:
                tr = TransferenciaInterna(businessobj=bobj, numero=siguiente_numero(TransferenciaInterna, bobj), **datos)
                tr.registrar_carga(userobj)
            error = tr.workflow_validar('aprobado')
            if error:
                return {'error': error}, args, kwargs
            tr.save()
        return {'success': f'Transferencia {tr.get_numero_display()} cargada. Mueve los fondos al aprobarse.', 'record_id': tr.pk}, args, kwargs
