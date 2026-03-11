import logging
from collections import namedtuple
from decimal import Decimal
from datetime import datetime
from zoneinfo import ZoneInfo
from django.http import QueryDict, HttpRequest
from django.forms import model_to_dict
from django.db.models import Sum
from django.core.files import File
from OptsIO.io_serial import IoS
from OptsIO.io_rpt import IoRpt
from OptsIO.io_json import to_json, from_json
from Egreso.models import OrdenCompra, OrdenCompraDetail, OrdenCompraCuota, OrdenCompraPago
from Sifen.models import Business, Producto, Cotizacion, Clientes
from Sifen import fl_sifen_conf, mng_gmdata
from Finance import f_calcs
import os


logger = logging.getLogger(__name__)


class MOC:
    def __init__(self):
        self.RUC = fl_sifen_conf.RUC
        self.bsobj = Business.objects.get(ruc=self.RUC)
        self.asuzone = ZoneInfo('America/Asuncion')

    def get_contadores_oc(self, *args, **kwargs) -> dict:
        base = OrdenCompra.objects.all()
        return {
            'total': base.count(),
            'creado': base.filter(oc_estado='CREADO').count(),
            'aprobado': base.filter(oc_estado='APROBADO').count(),
            'anulado': base.filter(oc_estado='ANULADO').count(),
        }

    def create_ordencompra(self, *args, **kwargs) -> tuple:
        ios = IoS()
        gdata = mng_gmdata.Gdata()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        pk = uc_fields.get('id')
        details = uc_fields.pop('details', [])
        cuotas = uc_fields.pop('cuotas', [])

        if not details:
            return {'error': 'Faltan los detalles de la orden de compra'}, args, kwargs

        if not pk:
            uc_fields['cargado_usuario'] = userobj.first_name if userobj else 'system'
            uc_fields['cargado_fecha'] = datetime.now(tz=self.asuzone)
            uc_fields['oc_fecha'] = datetime.now(tz=self.asuzone).date()
        else:
            uc_fields['actualizado_usuario'] = userobj.first_name if userobj else 'system'
            uc_fields['actualizado_fecha'] = datetime.now(tz=self.asuzone)

        # RUC DV
        if not uc_fields.get('prov_ruc_dv'):
            uc_fields['prov_ruc_dv'] = gdata.calculate_dv(uc_fields.get('prov_ruc', ''))

        uc_fields['oc_estado'] = uc_fields.get('oc_estado', 'CREADO')
        uc_fields['bs'] = self.bsobj.name
        uc_fields['bs_ruc'] = self.bsobj.ruc

        # Condicion
        oc_condicion_cod = int(uc_fields.get('oc_condicion_cod', 1))
        uc_fields['oc_condicion_cod'] = oc_condicion_cod
        uc_fields['oc_condicion'] = 'Contado' if oc_condicion_cod == 1 else 'Crédito'

        if oc_condicion_cod == 1:
            uc_fields.pop('oc_vencimiento', None)

        # Moneda / tasa
        if uc_fields.get('oc_moneda') == 'USD':
            cot = Cotizacion.objects.order_by('-id').first()
            uc_fields['tasa_cambio'] = cot.venta if cot else Decimal('7500')
        else:
            uc_fields['tasa_cambio'] = Decimal('1')

        # Initialize totals
        uc_fields['oc_total'] = 0
        uc_fields['oc_iva'] = 0
        uc_fields['oc_exenta'] = 0
        uc_fields['oc_g10'] = 0
        uc_fields['oc_i10'] = 0
        uc_fields['oc_g5'] = 0
        uc_fields['oc_i5'] = 0
        uc_fields['oc_descuento'] = 0
        if 'oc_descuento_global' not in uc_fields or uc_fields.get('oc_descuento_global') in [None, '']:
            uc_fields['oc_descuento_global'] = 0
        else:
            uc_fields['oc_descuento_global'] = float(uc_fields['oc_descuento_global'])
        uc_fields['oc_observacion'] = uc_fields.get('oc_observacion', '').strip() if uc_fields.get('oc_observacion') else ''

        # Auto-number for new OC
        if not pk:
            last = OrdenCompra.objects.order_by('-oc_numero').first()
            uc_fields['oc_numero'] = (last.oc_numero + 1) if last else 1

        # Clean fields not in model
        rnorm, rrm, rbol = ios.format_data_for_db(OrdenCompra, uc_fields)
        for c in rrm: uc_fields.pop(c, None)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        ff = ios.form_model_fields(uc_fields, OrdenCompra._meta.fields)
        for rr in ff:
            uc_fields.pop(rr, None)

        # Create or update
        if pk:
            ocobj = OrdenCompra.objects.using(dbcon).get(pk=pk)
            OrdenCompra.objects.using(dbcon).filter(pk=pk).update(**uc_fields)
            ocobj = OrdenCompra.objects.using(dbcon).get(pk=pk)
            ocobj.ordencompradetail_set.all().delete()
            ocobj.cuotas.all().delete()
        else:
            ocobj = OrdenCompra.objects.using(dbcon).create(**uc_fields)

        # Process details
        for d in details:
            precio_unitario = float(str(d.get('precio_unitario', 0)))
            cantidad = float(str(d.get('cantidad', 1)))
            prod_cod = d.get('prod_cod')

            try:
                prodobj = Producto.objects.get(prod_cod=prod_cod)
            except Producto.DoesNotExist:
                prod_autocreado = True
                PAF = namedtuple('PAF', ['prod_cod', 'precio', 'moneda', 'g5', 'g10', 'exenta', 'volumen', 'peso', 'medidaobj', 'porcentaje_iva'])
                MOBJ = namedtuple('MOBJ', ['medida_cod', 'medida'])
                IOBJ = namedtuple('IOBJ', ['porcentaje'])

                exenta_pct = float(d.get('exenta', 0))
                g5_pct = float(d.get('g5', 0))
                g10_pct = float(d.get('g10', 100))

                if g10_pct > 0:
                    porcentaje_iva_val = 10
                elif g5_pct > 0:
                    porcentaje_iva_val = 5
                else:
                    porcentaje_iva_val = 0

                medidaobj = MOBJ(medida_cod=77, medida='UNI')
                porcentajeobj = IOBJ(porcentaje=porcentaje_iva_val)
                prodobj = PAF(
                    prod_cod=prod_cod, precio=precio_unitario, moneda='GS',
                    g5=g5_pct, g10=g10_pct, exenta=exenta_pct,
                    volumen=0, peso=0, medidaobj=medidaobj, porcentaje_iva=porcentajeobj
                )
            else:
                prod_autocreado = False

            # Discounts
            descuento_item = float(d.get('descuento', 0) or 0)
            descuento_global_item = float(d.get('descuento_global_item', 0) or 0)
            descuento_total = descuento_item + descuento_global_item
            bruto = precio_unitario * cantidad
            neto = bruto - descuento_total
            if neto < 0:
                neto = 0

            if cantidad > 0 and neto > 0:
                precio_efectivo = neto / cantidad
                pcalc = f_calcs.calculate_price(prodobj, precio_efectivo, cantidad)
            else:
                pcalc = f_calcs.calculate_price(prodobj, precio_unitario, cantidad)
                if neto == 0:
                    pcalc = {
                        'exenta': 0, 'iva_5': 0, 'gravada_5': 0, 'base_gravada_5': 0,
                        'iva_10': 0, 'gravada_10': 0, 'base_gravada_10': 0
                    }

            prod_unidad_medida_desc = d.get('prod_unidad_medida_desc', '77')
            try:
                prod_unidad_medida = int(prod_unidad_medida_desc)
            except Exception:
                prod_unidad_medida = 77

            OrdenCompraDetail.objects.using(dbcon).create(
                ordencompraobj=ocobj,
                prod_autocreado=prod_autocreado,
                prod_cod=d.get('prod_cod', 9999),
                prod_descripcion=d.get('prod_descripcion', ''),
                prod_unidad_medida=prod_unidad_medida,
                prod_unidad_medida_desc=d.get('prod_unidad_medida_desc_text', 'UNI'),
                porcentaje_iva=prodobj.porcentaje_iva.porcentaje if hasattr(prodobj.porcentaje_iva, 'porcentaje') else prodobj.porcentaje_iva,
                precio_unitario=precio_unitario,
                cantidad=cantidad,
                exenta_pct=Decimal(str(d.get('exenta', 0))),
                g5_pct=Decimal(str(d.get('g5', 0))),
                g10_pct=Decimal(str(d.get('g10', 100))),
                exenta=pcalc['exenta'],
                iva_5=pcalc['iva_5'],
                gravada_5=pcalc['gravada_5'],
                base_gravada_5=pcalc['base_gravada_5'],
                iva_10=pcalc['iva_10'],
                gravada_10=pcalc['gravada_10'],
                base_gravada_10=pcalc['base_gravada_10'],
                descuento=d.get('descuento', 0),
                per_descuento=d.get('per_descuento', 0),
                cargado_usuario=userobj.first_name if userobj else 'system',
                cargado_fecha=datetime.now()
            )

        # Process cuotas if it's a credit condition
        if ocobj.oc_condicion_cod == 2 and cuotas:
            for idx, cuota in enumerate(cuotas):
                OrdenCompraCuota.objects.using(dbcon).create(
                    ordencompraobj=ocobj,
                    cuota_numero=idx + 1,
                    monto=float(str(cuota.get('monto', 0))),
                    vencimiento=cuota.get('vencimiento')
                )

        # Update totals
        totals = ocobj.ordencompradetail_set.aggregate(
            exenta=Sum('exenta'),
            iva_5=Sum('iva_5'),
            gravada_5=Sum('gravada_5'),
            iva_10=Sum('iva_10'),
            gravada_10=Sum('gravada_10'),
            descuento=Sum('descuento')
        )

        oc_total = (totals.get('gravada_5') or 0) + (totals.get('gravada_10') or 0) + (totals.get('exenta') or 0)

        # Intereses
        interes_pct = float(ocobj.oc_interes_pct or 0)
        interes_monto = float(oc_total) * (interes_pct / 100.0)
        ocobj.oc_interes_monto = interes_monto

        ocobj.oc_total = float(oc_total) + interes_monto
        ocobj.oc_iva = (totals.get('iva_5') or 0) + (totals.get('iva_10') or 0)
        ocobj.oc_exenta = totals.get('exenta') or 0
        ocobj.oc_g10 = totals.get('gravada_10') or 0
        ocobj.oc_i10 = totals.get('iva_10') or 0
        ocobj.oc_g5 = totals.get('gravada_5') or 0
        ocobj.oc_i5 = totals.get('iva_5') or 0
        ocobj.oc_descuento = totals.get('descuento', 0) or 0

        # Payment management
        ocobj.oc_pagado = ocobj.oc_pagado or 0
        ocobj.oc_saldo = float(ocobj.oc_total) - float(ocobj.oc_pagado)

        if ocobj.oc_saldo <= 0:
            ocobj.oc_estado_pago = 'PAGADO'
        elif ocobj.oc_pagado > 0:
            ocobj.oc_estado_pago = 'PARCIAL'
        else:
            ocobj.oc_estado_pago = 'PENDIENTE'

        ocobj.save()

        msg = 'Orden de Compra actualizada exitosamente' if pk else 'Orden de Compra creada exitosamente'
        return {'success': msg, 'record_id': ocobj.id}, args, kwargs

    def delete_ordencompra(self, *args, **kwargs) -> dict:
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        ids = from_json(q.get('ids'))
        msgs = []
        if not ids:
            return {'msgs': [{'error': 'Falta los IDs de los registros a eliminar'}]}
        for pk in ids:
            mobj = OrdenCompra.objects.using(dbcon).get(pk=pk)
            if mobj.pagos.exists():
                msgs.append({'error': f'OC {str(mobj.oc_numero).zfill(7)} tiene pagos registrados y no puede eliminarse'})
                continue
            mobj.delete()
            msgs.append({'success': 'Orden de Compra eliminada exitosamente'})
        return {'msgs': msgs}

    def register_payment(self, *args, **kwargs) -> tuple:
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        pk = uc_fields.get('id')
        monto_pago = float(uc_fields.get('monto_pago', 0))
        cuota_id = uc_fields.get('cuota_id')

        if not pk:
            return {'error': 'ID de la Orden de Compra no proporcionado'}, args, kwargs

        if monto_pago <= 0:
            return {'error': 'El monto a pagar debe ser mayor a 0'}, args, kwargs

        try:
            ocobj = OrdenCompra.objects.using(dbcon).get(pk=pk)

            oc_saldo = float(ocobj.oc_saldo)
            if oc_saldo <= 0:
                return {'error': 'Esta orden de compra ya está pagada en su totalidad'}, args, kwargs

            if monto_pago > oc_saldo + 0.01:
                return {'error': f'El monto a pagar ({monto_pago:.0f}) supera el saldo restante ({oc_saldo:.0f})'}, args, kwargs

            cuotaobj = None
            if cuota_id:
                try:
                    cuotaobj = OrdenCompraCuota.objects.using(dbcon).get(pk=cuota_id, ordencompraobj=ocobj)
                    if cuotaobj.estado == 'PAGADO':
                        return {'error': 'Esta cuota ya está pagada'}, args, kwargs
                    cuota_saldo = float(cuotaobj.monto) - float(cuotaobj.monto_pagado)
                    if monto_pago > cuota_saldo + 0.01:
                        return {'error': f'El monto ({monto_pago}) supera el saldo de la cuota ({cuota_saldo:.0f})'}, args, kwargs
                    cuotaobj.monto_pagado = float(cuotaobj.monto_pagado) + monto_pago
                    cuota_saldo_nuevo = float(cuotaobj.monto) - float(cuotaobj.monto_pagado)
                    if cuota_saldo_nuevo <= 0.01:
                        cuotaobj.estado = 'PAGADO'
                        cuotaobj.monto_pagado = cuotaobj.monto
                    else:
                        cuotaobj.estado = 'PARCIAL'
                    cuotaobj.save()
                except OrdenCompraCuota.DoesNotExist:
                    return {'error': 'Cuota no encontrada'}, args, kwargs

            ocobj.oc_pagado = float(ocobj.oc_pagado) + monto_pago
            ocobj.oc_saldo = float(ocobj.oc_total) - float(ocobj.oc_pagado)

            if ocobj.oc_saldo <= 0.01:
                ocobj.oc_estado_pago = 'PAGADO'
                ocobj.oc_saldo = 0
            else:
                ocobj.oc_estado_pago = 'PARCIAL'

            ocobj.save()

            OrdenCompraPago.objects.using(dbcon).create(
                ordencompraobj=ocobj,
                cuotaobj=cuotaobj,
                monto=monto_pago,
                fecha_pago=datetime.now(tz=ZoneInfo('America/Asuncion')).date(),
                metodo_pago=uc_fields.get('metodo_pago', 'Efectivo'),
                referencia=uc_fields.get('numero_referencia', ''),
                cargado_usuario=userobj.first_name if userobj else 'system'
            )

            return {'success': f'Pago registrado. Saldo actual: {ocobj.oc_saldo:.0f}', 'estado_pago': ocobj.oc_estado_pago}, args, kwargs

        except OrdenCompra.DoesNotExist:
            return {'error': 'Orden de Compra no encontrada'}, args, kwargs

    def get_ordenes_compra(self, *args, **kwargs) -> dict:
        """Obtiene todas las órdenes de compra según el filtro de estado."""
        from django.db.models import Q
        q = kwargs.get('qdict', {})
        filtro_estado = q.get('filtro_estado', 'pendientes')

        ordenes = OrdenCompra.objects.all()

        if filtro_estado == 'pendientes':
            ordenes = ordenes.filter(oc_saldo__gt=0.1)
        elif filtro_estado == 'pagadas':
            ordenes = ordenes.filter(oc_saldo__lte=0.1)

        ordenes = ordenes.order_by('-oc_fecha', '-oc_numero')

        search = q.get('search', '')
        if search:
            ordenes = ordenes.filter(
                Q(oc_numero__icontains=search) |
                Q(prov_nombre__icontains=search) |
                Q(prov_ruc__icontains=search)
            )

        total_count = ordenes.count()
        result = []
        for o in ordenes:
            cuotas = []
            if o.oc_condicion_cod == 2:
                for c in o.cuotas.all().order_by('cuota_numero'):
                    cuotas.append({
                        'id': c.id,
                        'cuota_numero': c.cuota_numero,
                        'monto': float(c.monto),
                        'monto_pagado': float(c.monto_pagado),
                        'saldo': float(c.monto) - float(c.monto_pagado),
                        'estado': c.estado,
                        'vencimiento': c.vencimiento.strftime('%Y-%m-%d'),
                    })
            result.append({
                'id': o.id,
                'oc_numero': o.oc_numero,
                'oc_fecha': o.oc_fecha.strftime('%Y-%m-%d') if o.oc_fecha else '',
                'oc_condicion_cod': o.oc_condicion_cod,
                'prov_nombre': o.prov_nombre,
                'prov_ruc': o.prov_ruc,
                'total_oc': float(o.oc_total or 0),
                'total_pagado': float(o.oc_pagado or 0),
                'oc_saldo': float(o.oc_saldo or 0),
                'oc_estado_pago': o.oc_estado_pago,
                'dias_vencido': self._calcular_dias_vencido_oc(o),
                'cuotas': cuotas,
            })

        return {'trows': total_count, 'qs': result}

    def _calcular_dias_vencido_oc(self, oc):
        """Calcula los días vencidos de una OC."""
        if not oc.oc_vencimiento:
            return 0
        hoy = datetime.now(tz=self.asuzone).date()
        if hoy > oc.oc_vencimiento:
            return (hoy - oc.oc_vencimiento).days
        return 0

    def get_resumen_pagos_oc(self, *args, **kwargs) -> dict:
        """Obtiene un resumen de pagos pendientes a proveedores."""
        ordenes_pendientes = OrdenCompra.objects.filter(oc_saldo__gt=0.1)

        total_pendiente = ordenes_pendientes.aggregate(total=Sum('oc_saldo'))['total'] or 0
        cantidad_ordenes = ordenes_pendientes.count()

        hoy = datetime.now(tz=self.asuzone).date()
        ordenes_vencidas = ordenes_pendientes.filter(oc_vencimiento__lt=hoy)
        total_vencido = ordenes_vencidas.aggregate(total=Sum('oc_saldo'))['total'] or 0

        return {
            'success': True,
            'resumen': {
                'total_pendiente': float(total_pendiente),
                'cantidad_facturas': cantidad_ordenes,
                'total_vencido': float(total_vencido),
                'cantidad_vencidas': ordenes_vencidas.count()
            }
        }

    def get_historial_pagos_oc(self, *args, **kwargs) -> dict:
        """Obtiene el historial de pagos de una OC."""
        q = kwargs.get('qdict', {})
        oc_id = q.get('oc_id')

        if not oc_id:
            return {'error': 'ID de OC requerido'}

        try:
            ocobj = OrdenCompra.objects.get(pk=oc_id)
        except OrdenCompra.DoesNotExist:
            return {'error': 'Orden de Compra no encontrada'}

        pagos = OrdenCompraPago.objects.filter(ordencompraobj=ocobj).order_by('-fecha_pago')

        result = []
        for p in pagos:
            result.append({
                'id': p.id,
                'monto': float(p.monto),
                'fecha_pago': p.fecha_pago.strftime('%Y-%m-%d'),
                'metodo_pago': p.metodo_pago,
                'referencia': p.referencia or '',
                'cargado_fecha': p.cargado_fecha.strftime('%Y-%m-%d %H:%M'),
                'cargado_usuario': p.cargado_usuario or '',
            })

        return {
            'success': True,
            'oc': {
                'oc_numero': ocobj.oc_numero,
                'prov_nombre': ocobj.prov_nombre,
                'total_oc': float(ocobj.oc_total or 0),
                'oc_saldo': float(ocobj.oc_saldo or 0),
            },
            'pagos': result,
            'total_pagado': float(ocobj.oc_pagado)
        }

    def get_ordencompra_details(self, *args, **kwargs) -> dict:
        q: dict = kwargs.get('qdict', {})
        header_id = q.get('header_id')
        dbcon = q.get('dbcon', 'default')

        if not header_id:
            return {'error': 'Falta el header_id'}

        try:
            ocobj = OrdenCompra.objects.using(dbcon).get(pk=header_id)
            details = []
            for detail in ocobj.ordencompradetail_set.filter(anulado=False):
                is_from_model = detail.prod_cod not in [9999, 1850] and not detail.prod_autocreado
                details.append({
                    'prod_cod': detail.prod_cod,
                    'prod_unidad_medida_desc': detail.prod_unidad_medida,
                    'prod_unidad_medida_desc_text': detail.prod_unidad_medida_desc,
                    'prod_descripcion': detail.prod_descripcion,
                    'precio_unitario': float(detail.precio_unitario),
                    'cantidad': float(detail.cantidad),
                    'porcentaje_iva': detail.porcentaje_iva,
                    'is_from_model': is_from_model,
                    'exenta_pct': float(detail.exenta_pct),
                    'g5_pct': float(detail.g5_pct),
                    'g10_pct': float(detail.g10_pct),
                    'exenta': float(detail.exenta),
                    'iva_5': float(detail.iva_5),
                    'gravada_5': float(detail.gravada_5),
                    'base_gravada_5': float(detail.base_gravada_5),
                    'iva_10': float(detail.iva_10),
                    'gravada_10': float(detail.gravada_10),
                    'base_gravada_10': float(detail.base_gravada_10),
                    'subtotal': float(detail.exenta) + float(detail.gravada_5) + float(detail.gravada_10),
                    'descuento': float(detail.descuento or 0),
                    'per_descuento': float(detail.per_descuento or 0)
                })
            total_bruto = sum(d['precio_unitario'] * d['cantidad'] for d in details)
            oc_descuento_global = float(ocobj.oc_descuento_global or 0)
            oc_descuento_global_pct = (oc_descuento_global / total_bruto * 100) if total_bruto > 0 else 0

            cuotas = []
            for c in ocobj.cuotas.all().order_by('cuota_numero'):
                cuotas.append({
                    'id': c.id,
                    'cuota_numero': c.cuota_numero,
                    'monto': float(c.monto),
                    'monto_pagado': float(c.monto_pagado),
                    'saldo': float(c.monto) - float(c.monto_pagado),
                    'estado': c.estado,
                    'vencimiento': c.vencimiento.strftime('%Y-%m-%d')
                })

            return {
                'success': True,
                'details': details,
                'cuotas': cuotas,
                'oc_descuento_global': oc_descuento_global,
                'oc_descuento_global_pct': oc_descuento_global_pct
            }
        except OrdenCompra.DoesNotExist:
            return {'error': 'Orden de Compra no encontrada'}

    def generando_ordencompra(self, *args, **kwargs) -> dict:
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')
        id = q.get('id')

        ocobj = OrdenCompra.objects.using(dbcon).get(pk=id)

        dattrs = {'media_path': True}
        bobj = Business.objects.get(ruc=ocobj.bs_ruc)
        bobj_dict = model_to_dict(bobj, exclude=['contribuyenteobj', 'actividadecoobj'])
        bobj_dict['contribuyente'] = bobj.contribuyenteobj.tipo
        bobj_dict['ciudad'] = bobj.ciudadobj.nombre_ciudad
        bobj_dict['denominacion'] = bobj.actividadecoobj.nombre_actividad
        dattrs.update(bobj_dict)

        return self.crear_ordencompra_pdf(
            username=userobj.username,
            userobj=userobj,
            qdict={
                'dbcon': dbcon,
                'id': id,
                'dattrs': to_json(dattrs)
            })

    def crear_ordencompra_pdf(self, *args, **kwargs) -> dict:
        q: dict = kwargs.get('qdict')
        dbcon = q.get('dbcon')
        id = q.get('id')
        dattrs = q.get('dattrs')
        ocobj = OrdenCompra.objects.using(dbcon).get(id=id)
        mq = QueryDict(mutable=True)
        fv = {
            'tmpl': 'Egreso/OrdenCompraRptUi.html',
            'model_app_name': 'Egreso',
            'model_name': 'OrdenCompra',
            'pk': id,
            'dattrs': dattrs,
            'dbcon': 'default',
            'surround': 'BaseAmReportUi.html',
            'g_pdf': 0,
            'g_pdf_kit': 1,
            'page-size': 'A5',
            'orientation': 'Portrait',
            'page-height': '250.000212',
            'page-width': '210.000088',
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
            'no-outline': None
        }
        mq.update(fv)
        mrq = HttpRequest()
        mrq.user = kwargs.get('userobj')
        mrq.method = 'GET'
        mrq.GET = mq
        io_rpt = IoRpt()
        rp = io_rpt.rpt_view(mrq)
        pdf_file = rp.get('pdf_file')
        with open(pdf_file, 'rb') as f:
            ocobj.oc_pdf_file = File(f, name=os.path.basename(pdf_file))
            ocobj.save()
        return {
            'success': 'PDF generado exitosamente',
            'oc_pdf_file': ocobj.oc_pdf_file.url
        }
