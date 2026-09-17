"""
Tesoreria: bancos, cuentas, chequeras, cheques, cajas y libro de movimientos.

API interna para otros plugins (Egreso, Deposito, Cobro):
    MTesoreria().registrar_movimiento(...)   idempotente por `clave`
    MTesoreria().emitir_cheque(...)
"""
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import ProtectedError

from OptsIO.io_business import get_active_business
from OptsIO.io_json import from_json
from Tesoreria.models import (
    Banco, CuentaBancaria, Chequera, Cheque, Caja, MovimientoTesoreria,
)

logger = logging.getLogger(__name__)

CATALOGOS = {'Banco': Banco, 'CuentaBancaria': CuentaBancaria, 'Chequera': Chequera, 'Caja': Caja}


class TesoreriaError(Exception):
    pass


def _decimal(value, campo='monto') -> Decimal:
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, TypeError):
        raise TesoreriaError(f"Valor invalido para {campo}: {value}")


class MTesoreria:

    # ------------------------------------------------------------------ API interna

    def registrar_movimiento(self, businessobj, fecha, tipo, monto, concepto,
                             cuentaobj=None, cajaobj=None, referencia='', chequeobj=None,
                             origen=None, clave=None, userobj=None) -> MovimientoTesoreria:
        """
        Registra un ingreso/egreso en una cuenta bancaria o caja.
        Con `clave`, repetir la llamada devuelve el movimiento ya registrado (idempotente).
        """
        if tipo not in ('ingreso', 'egreso'):
            raise TesoreriaError(f"Tipo de movimiento invalido: {tipo}")
        if bool(cuentaobj) == bool(cajaobj):
            raise TesoreriaError("El movimiento debe indicar una cuenta bancaria o una caja (solo una)")
        monto = _decimal(monto)
        if monto <= 0:
            raise TesoreriaError("El monto debe ser mayor a cero")
        destino = cuentaobj or cajaobj
        if destino.businessobj_id != businessobj.pk:
            raise TesoreriaError("La cuenta/caja no pertenece al negocio")
        if not destino.activo:
            raise TesoreriaError(f"{destino} esta inactiva")

        with transaction.atomic():
            if clave:
                existente = MovimientoTesoreria.objects.filter(clave=clave).first()
                if existente:
                    return existente
            if cajaobj:
                # Lock de la caja: serializa el control de saldo/tope entre movimientos concurrentes.
                cajaobj = Caja.objects.select_for_update().get(pk=cajaobj.pk)
                saldo = cajaobj.get_saldo()
                if tipo == 'egreso' and monto > saldo:
                    raise TesoreriaError(f"Saldo insuficiente en {cajaobj}: disponible {saldo:,.0f}")
                if tipo == 'ingreso' and cajaobj.tope and saldo + monto > cajaobj.tope:
                    raise TesoreriaError(
                        f"El ingreso supera el tope de {cajaobj} ({cajaobj.tope:,.0f}); "
                        f"maximo a reponer: {cajaobj.tope - saldo:,.0f}")
            return MovimientoTesoreria.objects.create(
                businessobj=businessobj, fecha=fecha, tipo=tipo, monto=monto,
                moneda=destino.moneda, concepto=concepto[:300], referencia=(referencia or '')[:120],
                cuentaobj=cuentaobj, cajaobj=cajaobj, chequeobj=chequeobj,
                origen_app=origen._meta.app_label if origen else '',
                origen_model=origen._meta.model_name if origen else '',
                origen_id=origen.pk if origen else None,
                clave=clave,
                cargado_fecha=datetime.now(),
                cargado_usuario=getattr(userobj, 'username', '') or '',
            )

    def emitir_cheque(self, chequeraobj, beneficiario, monto, fecha_emision, fecha_pago=None,
                      concepto='', a_la_orden=True, origen=None, userobj=None) -> Cheque:
        """Toma el proximo numero de la chequera y crea el cheque. No mueve saldo: eso ocurre al pagar."""
        monto = _decimal(monto)
        if monto <= 0:
            raise TesoreriaError("El monto del cheque debe ser mayor a cero")
        fecha_pago = fecha_pago or fecha_emision
        if chequeraobj.tipo == 'vista' and fecha_pago != fecha_emision:
            raise TesoreriaError("Una chequera a la vista no admite fecha de pago diferida")
        with transaction.atomic():
            try:
                numero = chequeraobj.tomar_numero()
            except ValueError as e:
                raise TesoreriaError(str(e))
            return Cheque.objects.create(
                businessobj_id=chequeraobj.businessobj_id, chequeraobj=chequeraobj, numero=numero,
                fecha_emision=fecha_emision, fecha_pago=fecha_pago, beneficiario=beneficiario[:200],
                monto=monto, concepto=(concepto or '')[:300], a_la_orden=a_la_orden,
                origen_app=origen._meta.app_label if origen else '',
                origen_model=origen._meta.model_name if origen else '',
                origen_id=origen.pk if origen else None,
                cargado_fecha=datetime.now(),
                cargado_usuario=getattr(userobj, 'username', '') or '',
            )

    # ------------------------------------------------------------------ Metodos UI (iom)

    def get_saldos(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}
        cuentas = [{
            'id': c.pk, 'descripcion': str(c), 'banco': c.bancoobj.nombre, 'numero': c.numero,
            'moneda': c.moneda, 'saldo': float(c.get_saldo()),
        } for c in CuentaBancaria.objects.filter(businessobj=bobj, activo=True).select_related('bancoobj')]
        cajas = [{
            'id': c.pk, 'descripcion': str(c), 'tipo': c.tipo, 'moneda': c.moneda,
            'tope': float(c.tope), 'saldo': float(c.get_saldo()), 'responsable': c.responsable,
        } for c in Caja.objects.filter(businessobj=bobj, activo=True)]
        return {'success': True, 'cuentas': cuentas, 'cajas': cajas}

    def create_chequera(self, *args, **kwargs) -> tuple:
        """c_a de ChequeraCreateUi: valida rango/solapamiento y fija proximo_numero."""
        userobj = kwargs.get('userobj')
        q = kwargs.get('qdict', {})
        f = from_json(q.get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        try:
            desde, hasta = int(f.get('numero_desde')), int(f.get('numero_hasta'))
        except (TypeError, ValueError):
            return {'error': 'Rango de numeracion invalido'}, args, kwargs
        if desde <= 0 or hasta < desde:
            return {'error': 'El numero hasta debe ser mayor o igual al numero desde'}, args, kwargs
        cuenta = CuentaBancaria.objects.filter(pk=f.get('cuentaobj_id') or 0, businessobj=bobj).first()
        if not cuenta:
            return {'error': 'Cuenta bancaria invalida'}, args, kwargs
        serie = (f.get('serie') or '').strip()
        activo = str(f.get('activo', 'true')).lower() in ('true', '1', 'on')
        pk = f.get('id')

        solapadas = Chequera.objects.filter(
            cuentaobj=cuenta, serie=serie, numero_desde__lte=hasta, numero_hasta__gte=desde)
        if pk:
            solapadas = solapadas.exclude(pk=pk)
        if solapadas.exists():
            return {'error': f'El rango se superpone con la chequera {solapadas.first()}'}, args, kwargs

        if pk:
            ch = Chequera.objects.filter(pk=pk, businessobj=bobj).first()
            if not ch:
                return {'error': 'Chequera inexistente'}, args, kwargs
            emitidos = ch.cheque_set.exists()
            if emitidos and (ch.cuentaobj_id != cuenta.pk or ch.numero_desde != desde or ch.serie != serie):
                return {'error': 'La chequera ya tiene cheques emitidos: solo se puede ampliar el numero hasta o desactivarla'}, args, kwargs
            if hasta < ch.proximo_numero - 1:
                return {'error': f'El numero hasta no puede ser menor al ultimo cheque emitido ({ch.proximo_numero - 1})'}, args, kwargs
            ch.cuentaobj, ch.serie, ch.tipo = cuenta, serie, f.get('tipo') or ch.tipo
            ch.numero_desde, ch.numero_hasta, ch.activo = desde, hasta, activo
            if not emitidos:
                ch.proximo_numero = desde
            ch.actualizado_fecha, ch.actualizado_usuario = datetime.now(), userobj.username
            ch.save()
            return {'success': 'Chequera actualizada', 'record_id': ch.pk}, args, kwargs

        ch = Chequera.objects.create(
            businessobj=bobj, cuentaobj=cuenta, serie=serie, tipo=f.get('tipo') or 'vista',
            numero_desde=desde, numero_hasta=hasta, proximo_numero=desde, activo=activo,
            cargado_fecha=datetime.now(), cargado_usuario=userobj.username)
        return {'success': 'Chequera creada', 'record_id': ch.pk}, args, kwargs

    def create_movimiento(self, *args, **kwargs) -> tuple:
        """c_a de MovimientoCreateUi: ajuste/movimiento manual de tesoreria."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        cuenta = CuentaBancaria.objects.filter(pk=f.get('cuentaobj_id') or 0, businessobj=bobj).first()
        caja = Caja.objects.filter(pk=f.get('cajaobj_id') or 0, businessobj=bobj).first()
        if not (f.get('concepto') or '').strip():
            return {'error': 'El concepto es obligatorio'}, args, kwargs
        try:
            mov = self.registrar_movimiento(
                bobj, f.get('fecha'), f.get('tipo'), f.get('monto'), f.get('concepto').strip(),
                cuentaobj=cuenta, cajaobj=caja, referencia=f.get('referencia', ''), userobj=userobj)
        except TesoreriaError as e:
            return {'error': str(e)}, args, kwargs
        return {'success': f'Movimiento {mov.pk} registrado', 'record_id': mov.pk}, args, kwargs

    def anular_movimientos(self, *args, **kwargs) -> dict:
        """Anula movimientos manuales. Los generados por otra operacion se anulan desde su origen."""
        userobj = kwargs.get('userobj')
        ids = from_json(kwargs.get('qdict', {}).get('ids', '[]'))
        bobj = get_active_business(userobj)
        qs = MovimientoTesoreria.objects.filter(pk__in=ids, businessobj=bobj, anulado=False)
        if qs.exclude(origen_app='').exists():
            return {'msgs': [{'error': 'Hay movimientos generados por otra operacion: anule la operacion de origen'}]}
        n = qs.update(anulado=True, anulado_fecha=datetime.now(), anulado_usuario=userobj.username)
        return {'msgs': [{'success': f'{n} movimiento(s) anulado(s)'}]}

    def anular_cheque(self, *args, **kwargs) -> dict:
        userobj = kwargs.get('userobj')
        q = kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        cheque = Cheque.objects.filter(pk=q.get('id') or 0, businessobj=bobj).first()
        if not cheque:
            return {'error': 'Cheque inexistente'}
        if cheque.estado == 'cobrado':
            return {'error': 'Un cheque cobrado no se puede anular'}
        if cheque.estado == 'anulado':
            return {'info': 'El cheque ya estaba anulado'}
        cheque.estado = 'anulado'
        cheque.anulado_fecha, cheque.anulado_usuario = datetime.now(), userobj.username
        cheque.anulado_motivo = (q.get('motivo') or '')[:300]
        cheque.save()
        return {'success': f'Cheque {cheque.numero} anulado'}

    def delete_catalogo(self, *args, **kwargs) -> dict:
        """Borra bancos/cuentas/chequeras/cajas sin uso; si tienen movimientos hay que desactivarlos."""
        q = kwargs.get('qdict', {})
        model = CATALOGOS.get(q.get('model_name'))
        bobj = get_active_business(kwargs.get('userobj'))
        if not model or not bobj:
            return {'msgs': [{'error': 'Solicitud invalida'}]}
        try:
            with transaction.atomic():
                n, _ = model.objects.filter(pk__in=from_json(q.get('ids', '[]')), businessobj=bobj).delete()
        except ProtectedError:
            return {'msgs': [{'error': 'El registro tiene datos asociados: desactivelo en lugar de borrarlo'}]}
        return {'msgs': [{'success': f'{n} registro(s) borrado(s)'}]}
