"""
Motor de asientos automaticos.

Un handler de evento arma `montos` (en guaranies) y `refs` y llama a MotorAsientos.generar():
el motor toma el FormatoAsiento del negocio para ese evento, resuelve la cuenta de cada linea
y guarda el asiento ya aprobado. `Asiento.clave` unica hace idempotente la generacion.
"""
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from Contabilidad.models import (
    Asiento, AsientoDetalle, ConfigContable, CuentaRol, FormatoAsiento, MapeoCuenta,
)
from OptsIO.io_business import siguiente_numero
from OptsIO.io_money import precision_monetaria
from Sifen.models import Cotizacion

Q2 = Decimal('0.01')


class ContabilidadError(Exception):
    """Configuracion contable incompleta: el evento queda en error y se reprocesa al corregirla."""


class SafeDict(dict):
    def __missing__(self, key):
        return ''


def tasa_a_guaranies(moneda: str, fecha, tasa=None) -> Decimal:
    """Factor para llevar un monto a guaranies. Usa la tasa informada o la cotizacion vigente a la fecha."""
    if moneda in ('PYG', 'GS', '', None):
        return Decimal(1)
    if tasa and Decimal(str(tasa)) > 1:
        return Decimal(str(tasa))
    cot = Cotizacion.objects.filter(moneda=moneda, fecha__lte=fecha).order_by('-fecha').first()
    if not cot:
        raise ContabilidadError(f"No hay cotización de {moneda} al {fecha} para asentar en guaraníes")
    return Decimal(cot.venta or cot.tasa_cambio)


class MotorAsientos:

    def contabilidad_activa(self, business, fecha) -> bool:
        """El negocio lleva contabilidad si aplico una plantilla; respeta la fecha de arranque."""
        config = ConfigContable.objects.filter(businessobj=business).first()
        if not config:
            return False
        return not (config.fecha_inicio and str(fecha) < str(config.fecha_inicio))

    def resolver_cuenta(self, business, linea, refs):
        if linea.cuentaobj_id:
            return linea.cuentaobj
        ref = refs.get(linea.monto)
        if ref and ref[1]:
            mapeo = MapeoCuenta.objects.filter(businessobj=business, tipo=ref[0], ref_id=ref[1]).select_related('cuentaobj').first()
            if mapeo:
                return mapeo.cuentaobj
        rol = CuentaRol.objects.filter(businessobj=business, rol=linea.rol).select_related('cuentaobj').first()
        if not rol:
            raise ContabilidadError(f"El rol contable '{linea.rol}' no tiene cuenta asignada")
        return rol.cuentaobj

    @precision_monetaria
    def generar(self, event, evento: str, fecha, montos: dict, refs: dict = None, ctx: dict = None) -> dict:
        business, refs = event.business, refs or {}
        if not business or not self.contabilidad_activa(business, fecha):
            return {'omitido': 'el negocio no lleva contabilidad a esa fecha'}
        clave = f"{evento}:{event.source_app}.{event.source_model}:{event.source_id}"
        existente = Asiento.objects.filter(clave=clave).first()
        if existente:
            return {'asiento': existente.pk, 'existente': True}
        formato = FormatoAsiento.objects.filter(businessobj=business, evento=evento, activo=True).first()
        if not formato:
            return {'omitido': f'sin formato de asiento activo para {evento}'}

        detalles, debe, haber = [], Decimal(0), Decimal(0)
        for linea in formato.lineas.all():
            monto = Decimal(str(montos.get(linea.monto) or 0)).quantize(Q2)
            if monto <= 0:
                continue
            cuenta = self.resolver_cuenta(business, linea, refs)
            if not cuenta.imputable:
                raise ContabilidadError(f"La cuenta {cuenta} no es imputable")
            detalles.append(AsientoDetalle(cuentaobj=cuenta, glosa=linea.glosa,
                                           debe=monto if linea.lado == 'debe' else 0,
                                           haber=monto if linea.lado == 'haber' else 0))
            debe, haber = (debe + monto, haber) if linea.lado == 'debe' else (debe, haber + monto)
        if not detalles:
            return {'omitido': 'sin montos para asentar'}
        # El redondeo a centavos de IVA/netos puede dejar 0.01 de diferencia: se absorbe en la ultima linea del lado menor
        if debe != haber and abs(debe - haber) <= Decimal('0.05'):
            lado = 'debe' if debe < haber else 'haber'
            ultima = [d for d in detalles if getattr(d, lado) > 0][-1]
            setattr(ultima, lado, getattr(ultima, lado) + abs(debe - haber))
            debe = haber = max(debe, haber)
        if debe != haber:
            raise ContabilidadError(f"El formato '{formato.nombre}' no balancea: debe {debe} / haber {haber}")

        with transaction.atomic():
            asiento = Asiento(
                businessobj=business, numero=siguiente_numero(Asiento, business), fecha=fecha,
                concepto=formato.concepto.format_map(SafeDict(ctx or {}))[:300], origen='automatico', evento=evento,
                origen_app=event.source_app, origen_model=event.source_model, origen_id=event.source_id,
                clave=clave, total=debe, estado='aprobado', cargado_fecha=datetime.now(), cargado_usuario='sistema',
                aprobado_fecha=datetime.now(), aprobado_usuario='sistema',
                workflow_log=[{'estado': 'aprobado', 'username': 'sistema', 'usuario': 'sistema',
                               'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'nota': f'Evento {event.pk}'}])
            asiento.save()
            for d in detalles:
                d.asientoobj = asiento
            AsientoDetalle.objects.bulk_create(detalles)
        return {'asiento': asiento.pk}

    @precision_monetaria
    def revertir(self, event) -> dict:
        """Contra-asiento de todos los asientos automaticos del origen del evento. Idempotente."""
        originales = Asiento.objects.filter(
            businessobj=event.business, origen='automatico', anulado=False,
            origen_app=event.source_app, origen_model=event.source_model, origen_id=event.source_id)
        creados = []
        for original in originales:
            clave = f"reverso:{original.pk}"
            if Asiento.objects.filter(clave=clave).exists():
                continue
            with transaction.atomic():
                reverso = Asiento(
                    businessobj=original.businessobj, numero=siguiente_numero(Asiento, original.businessobj),
                    fecha=datetime.now().date(), concepto=f"Reverso asiento {original.get_numero_display()}: {original.concepto}"[:300],
                    origen='reverso', evento=event.event_type, origen_app=original.origen_app,
                    origen_model=original.origen_model, origen_id=original.origen_id, clave=clave,
                    reversaobj=original, total=original.total, estado='aprobado',
                    cargado_fecha=datetime.now(), cargado_usuario='sistema',
                    aprobado_fecha=datetime.now(), aprobado_usuario='sistema')
                reverso.save()
                AsientoDetalle.objects.bulk_create([
                    AsientoDetalle(asientoobj=reverso, cuentaobj=d.cuentaobj, debe=d.haber, haber=d.debe, glosa=d.glosa)
                    for d in original.detalles.all()])
            creados.append(reverso.pk)
        return {'reversos': creados}
