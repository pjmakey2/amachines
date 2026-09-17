"""Depositos bancarios: carga manual y completado de los generados por el cierre de cobros."""
import re
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Sum

from Deposito.models import Deposito, DepositoCheque
from OptsIO.io_business import get_active_business, siguiente_numero, user_label
from OptsIO.io_json import from_json
from OptsIO.io_money import precision_monetaria
from Tesoreria.models import CuentaBancaria

RE_DECIMAL = re.compile(r'^\d+(\.\d+)?$')
RE_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def _dec(value) -> Decimal:
    texto = str(value if value is not None else '').strip()
    return Decimal(texto) if RE_DECIMAL.match(texto) else Decimal(0)


def _fecha(value):
    texto = str(value or '').strip()[:10]
    return datetime.strptime(texto, '%Y-%m-%d').date() if RE_FECHA.match(texto) else None


class MDeposito:

    @precision_monetaria
    def create_deposito(self, *args, **kwargs) -> tuple:
        """
        c_a de DepositoCreateUi. Se edita solo en 'cargado'. En un deposito automatico el monto,
        tipo y moneda vienen del cobro y no se tocan: se completa cuenta, boleta y cheques.
        """
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        fecha = _fecha(f.get('fecha'))
        cuenta = CuentaBancaria.objects.filter(pk=f.get('cuentaobj_id') or 0, businessobj=bobj).first()
        cheques = [c for c in (f.get('cheques') or []) if _dec(c.get('monto')) > 0 and (c.get('numero') or '').strip()]
        if not fecha:
            return {'error': 'La fecha es obligatoria'}, args, kwargs

        with transaction.atomic():
            if f.get('id'):
                dep = Deposito.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not dep:
                    return {'error': 'Depósito inexistente'}, args, kwargs
                if dep.estado != 'cargado' or dep.anulado:
                    return {'error': f'El depósito está {dep.estado}: ya no se puede modificar'}, args, kwargs
                dep.actualizado_fecha, dep.actualizado_usuario = datetime.now(), user_label(userobj)
            else:
                dep = Deposito(businessobj=bobj, numero=siguiente_numero(Deposito, bobj))
                dep.registrar_carga(userobj)
            if not dep.automatico:
                dep.tipo, dep.monto = f.get('tipo') or 'efectivo', _dec(f.get('monto'))
                dep.moneda = cuenta.moneda if cuenta else (f.get('moneda') or 'PYG')
                if dep.tipo not in dict(Deposito.TIPOS) or dep.monto <= 0:
                    return {'error': 'Tipo y monto son obligatorios'}, args, kwargs
            if cuenta and cuenta.moneda != dep.moneda:
                return {'error': f'El depósito es en {dep.moneda} y la cuenta en {cuenta.moneda}'}, args, kwargs
            if dep.tipo == 'cheque' and cheques and sum(_dec(c.get('monto')) for c in cheques) != dep.monto:
                return {'error': 'La suma de los cheques no coincide con el monto del depósito'}, args, kwargs
            dep.fecha, dep.cuentaobj = fecha, cuenta
            dep.boleta_numero = (f.get('boleta_numero') or '').strip()[:60]
            dep.observacion = (f.get('observacion') or '').strip()[:300]
            dep.save()
            dep.cheques.all().delete()
            DepositoCheque.objects.bulk_create([DepositoCheque(
                depositoobj=dep, banco=(c.get('banco') or '').strip()[:120], numero=c.get('numero').strip()[:60],
                librador=(c.get('librador') or '').strip()[:200], fecha=_fecha(c.get('fecha')), monto=_dec(c.get('monto')),
            ) for c in cheques if dep.tipo == 'cheque'])
        return {'success': f'Depósito {dep.get_numero_display()} guardado. Acredita la cuenta al aprobarse.', 'record_id': dep.pk}, args, kwargs

    def get_cheques(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        dep = Deposito.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not dep:
            return {'error': 'Depósito inexistente'}
        return {'success': True, 'cheques': [{
            'banco': c.banco, 'numero': c.numero, 'librador': c.librador,
            'fecha': c.fecha.strftime('%Y-%m-%d') if c.fecha else '', 'monto': float(c.monto)} for c in dep.cheques.all()]}

    @precision_monetaria
    def get_resumen(self, *args, **kwargs) -> dict:
        """Valores cobrados todavia no acreditados (depositos sin aprobar), por tipo."""
        bobj = get_active_business(kwargs.get('userobj'))
        pendientes = Deposito.objects.filter(businessobj=bobj, anulado=False).exclude(estado='aprobado')
        return {'success': True, 'pendientes': [
            {'tipo': r['tipo'], 'moneda': r['moneda'], 'cantidad': r['n'], 'monto': float(r['t'])}
            for r in pendientes.values('tipo', 'moneda').annotate(t=Sum('monto'), n=Count('id')).order_by('tipo')]}
