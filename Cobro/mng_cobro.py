import logging
import arrow
from decimal import Decimal
from datetime import datetime, date
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.http import QueryDict
from django.db.models import Sum, Q
from num2words import num2words
from Sifen.models import DocumentHeader, DocumentRecibo, DocumentReciboDetail, Cotizacion, Business, Enumbers
from Sifen import ekuatia_serials
from Cobro.models import Pago
from OptsIO.models import UserProfile, UserBusiness

logger = logging.getLogger(__name__)


class MCobro:
    """
    Manager para gestión de cobros y pagos de facturas a crédito.
    """

    def __init__(self):
        self.asuzone = ZoneInfo('America/Asuncion')

    def get_facturas_credito(self, *args, **kwargs) -> dict:
        """
        Obtiene las facturas a crédito según el filtro de estado.
        filtro_estado: 'pendientes' (saldo > 0), 'pagadas' (saldo = 0), 'todas'
        """
        q = kwargs.get('qdict', {})
        filtro_estado = q.get('filtro_estado', 'pendientes')

        # Base: facturas tipo crédito
        facturas = DocumentHeader.objects.filter(
            doc_tipo='FE',
            doc_cre_tipo_cod=2,  # Crédito
        )

        # Aplicar filtro de estado
        if filtro_estado == 'pendientes':
            facturas = facturas.filter(doc_saldo__gt=0)
        elif filtro_estado == 'pagadas':
            facturas = facturas.filter(doc_saldo=0)
        # 'todas' no aplica filtro adicional

        facturas = facturas.order_by('-doc_fecha', '-doc_numero')

        # Búsqueda opcional
        search = q.get('search', '')
        if search:
            facturas = facturas.filter(
                Q(doc_numero__icontains=search) |
                Q(pdv_nombrefactura__icontains=search) |
                Q(pdv_ruc__icontains=search)
            )

        total_count = facturas.count()
        result = []
        for f in facturas:
            total_pagado = f.pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0')
            result.append({
                'id': f.id,
                'doc_numero': f.doc_numero,
                'doc_fecha': f.doc_fecha.strftime('%Y-%m-%d') if f.doc_fecha else '',
                'pdv_razon_social': f.pdv_nombrefactura,
                'pdv_ruc': f.pdv_ruc,
                'total_factura': float(f.doc_total or 0),
                'total_pagado': float(total_pagado),
                'doc_saldo': float(f.doc_saldo or 0),
                'doc_cre_plazo': f.doc_cre_plazo,
                'dias_vencido': self._calcular_dias_vencido(f),
            })

        # Formato compatible con DataTables (io_grid.py)
        return {'trows': total_count, 'qs': result}

    def _calcular_dias_vencido(self, factura):
        """Calcula los días vencidos de una factura."""
        if not factura.doc_fecha:
            return 0

        # Parsear el plazo (ej: "30 dias")
        plazo_dias = 30  # Default
        if factura.doc_cre_plazo:
            try:
                plazo_dias = int(factura.doc_cre_plazo.split()[0])
            except:
                pass

        from datetime import timedelta
        fecha_vencimiento = factura.doc_fecha + timedelta(days=plazo_dias)
        hoy = date.today()

        if hoy > fecha_vencimiento:
            return (hoy - fecha_vencimiento).days
        return 0

    def registrar_pago(self, *args, **kwargs) -> dict:
        """
        Registra un pago para una factura.
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')

        factura_id = q.get('factura_id')
        monto = q.get('monto')
        fecha_pago = q.get('fecha_pago')
        metodo_pago = q.get('metodo_pago', 'efectivo')
        numero_referencia = q.get('numero_referencia', '')
        observaciones = q.get('observaciones', '')

        if not factura_id or not monto:
            return {'error': 'Factura y monto son requeridos'}

        try:
            factura = DocumentHeader.objects.get(pk=factura_id)
        except DocumentHeader.DoesNotExist:
            return {'error': 'Factura no encontrada'}

        # Validar que el monto no exceda el saldo
        monto_decimal = Decimal(str(monto))
        if monto_decimal > factura.doc_saldo:
            return {
                'error': f'El monto ({monto_decimal}) excede el saldo pendiente ({factura.doc_saldo})'
            }

        if monto_decimal <= 0:
            return {'error': 'El monto debe ser mayor a 0'}

        # Parsear fecha
        if isinstance(fecha_pago, str):
            fecha_pago = datetime.strptime(fecha_pago, '%Y-%m-%d').date()
        elif not fecha_pago:
            fecha_pago = date.today()

        # Crear el pago
        pago = Pago.objects.create(
            documentheaderobj=factura,
            monto=monto_decimal,
            fecha_pago=fecha_pago,
            metodo_pago=metodo_pago,
            numero_referencia=numero_referencia,
            observaciones=observaciones,
            cargado_usuario=userobj
        )

        logger.info(f'Pago registrado: {pago.id} - Factura {factura.doc_numero} - Monto {monto_decimal}')

        return {
            'success': True,
            'message': f'Pago de {monto_decimal:,.0f} Gs. registrado correctamente',
            'pago_id': pago.id,
            'nuevo_saldo': float(factura.doc_saldo)
        }

    def get_historial_pagos(self, *args, **kwargs) -> dict:
        """
        Obtiene el historial de pagos de una factura.
        """
        q = kwargs.get('qdict', {})
        factura_id = q.get('factura_id')

        if not factura_id:
            return {'error': 'ID de factura requerido'}

        try:
            factura = DocumentHeader.objects.get(pk=factura_id)
        except DocumentHeader.DoesNotExist:
            return {'error': 'Factura no encontrada'}

        pagos = Pago.objects.filter(documentheaderobj=factura).order_by('-fecha_pago')

        result = []
        for p in pagos:
            result.append({
                'id': p.id,
                'monto': float(p.monto),
                'fecha_pago': p.fecha_pago.strftime('%Y-%m-%d'),
                'metodo_pago': p.metodo_pago,
                'metodo_pago_display': p.get_metodo_pago_display(),
                'numero_referencia': p.numero_referencia or '',
                'observaciones': p.observaciones or '',
                'cargado_fecha': p.cargado_fecha.strftime('%Y-%m-%d %H:%M'),
                'cargado_usuario': p.cargado_usuario.username if p.cargado_usuario else '',
            })

        total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0')

        return {
            'success': True,
            'factura': {
                'doc_numero': factura.doc_numero,
                'pdv_razon_social': factura.pdv_nombrefactura,
                'total_factura': float(factura.doc_total or 0),
                'doc_saldo': float(factura.doc_saldo or 0),
            },
            'pagos': result,
            'total_pagado': float(total_pagado)
        }

    def eliminar_pago(self, *args, **kwargs) -> dict:
        """
        Elimina un pago y restaura el saldo de la factura.
        """
        q = kwargs.get('qdict', {})
        pago_id = q.get('pago_id')

        if not pago_id:
            return {'error': 'ID de pago requerido'}

        try:
            pago = Pago.objects.get(pk=pago_id)
        except Pago.DoesNotExist:
            return {'error': 'Pago no encontrado'}

        factura_numero = pago.documentheaderobj.doc_numero
        monto = pago.monto

        # El método delete() del modelo restaura el saldo automáticamente
        pago.delete()

        logger.info(f'Pago eliminado: Factura {factura_numero} - Monto {monto}')

        return {
            'success': True,
            'message': f'Pago de {monto:,.0f} Gs. eliminado correctamente'
        }

    def get_resumen_cobros(self, *args, **kwargs) -> dict:
        """
        Obtiene un resumen de cobros pendientes.
        """
        facturas_pendientes = DocumentHeader.objects.filter(
            doc_tipo='FE',
            doc_cre_tipo_cod=2,
            doc_saldo__gt=0
        )

        total_pendiente = facturas_pendientes.aggregate(
            total=Sum('doc_saldo')
        )['total'] or Decimal('0')

        cantidad_facturas = facturas_pendientes.count()

        # Facturas vencidas (más de 30 días por defecto)
        from datetime import timedelta
        fecha_limite = date.today() - timedelta(days=30)
        facturas_vencidas = facturas_pendientes.filter(doc_fecha__lt=fecha_limite)
        total_vencido = facturas_vencidas.aggregate(
            total=Sum('doc_saldo')
        )['total'] or Decimal('0')

        return {
            'success': True,
            'resumen': {
                'total_pendiente': float(total_pendiente),
                'cantidad_facturas': cantidad_facturas,
                'total_vencido': float(total_vencido),
                'cantidad_vencidas': facturas_vencidas.count()
            }
        }

    def get_resumen_recibo_cobro(self, *args, **kwargs) -> dict:
        """
        Prepara datos de facturas seleccionadas para el resumen pre-recibo.
        Valida: mismo cliente, que no tengan recibo existente, que tengan pagos.
        """
        q = kwargs.get('qdict', {})
        facturas_ids = q.getlist('facturas[]') if hasattr(q, 'getlist') else q.get('facturas', [])

        if not facturas_ids:
            return {'error': 'Debe seleccionar al menos una factura'}

        fobjs = DocumentHeader.objects.filter(pk__in=facturas_ids)
        if not fobjs.exists():
            return {'error': 'No se encontraron las facturas seleccionadas'}

        # Validar mismo cliente (pdv_ruc)
        rucs = set(fobjs.values_list('pdv_ruc', flat=True))
        if len(rucs) > 1:
            return {'error': 'Todas las facturas deben ser del mismo cliente'}

        # Validar que no sean facturas ya concluidas (saldo 0 con recibo existente)
        concluidas = []
        for f in fobjs:
            if f.doc_saldo == 0 and DocumentReciboDetail.objects.filter(prof_number=f.prof_number, saldo=0).exists():
                concluidas.append(f.doc_numero)
        if concluidas:
            return {'error': f'Las facturas {concluidas} ya estan concluidas con recibo generado'}

        # Validar que todas tengan pagos registrados
        sin_pagos = [f.doc_numero for f in fobjs if not f.pagos.exists()]
        if sin_pagos:
            return {'error': f'Las facturas {sin_pagos} no tienen pagos registrados'}

        # Preparar datos y validar cobrado incremental
        result = []
        total_cobrado_all = Decimal('0')
        total_saldo_all = Decimal('0')
        total_factura_all = Decimal('0')
        sin_cobro_nuevo = []

        for f in fobjs:
            total_factura = f.get_total_venta_gs()
            saldo = f.doc_saldo or Decimal('0')

            total_pagado_acum = total_factura - saldo
            prev_cobrado = DocumentReciboDetail.objects.filter(
                prof_number=f.prof_number
            ).aggregate(total=Sum('cobrado'))['total'] or Decimal('0')
            cobrado = total_pagado_acum - prev_cobrado

            if cobrado <= 0:
                sin_cobro_nuevo.append(str(f.doc_numero))

            total_cobrado_all += cobrado
            total_saldo_all += saldo
            total_factura_all += total_factura

            result.append({
                'id': f.id,
                'doc_numero': f.doc_numero,
                'doc_fecha': f.doc_fecha.strftime('%Y-%m-%d') if f.doc_fecha else '',
                'total_factura': float(total_factura),
                'cobrado': float(cobrado),
                'saldo': float(saldo),
                'estado': 'PAGADO' if saldo == 0 else 'PARCIAL',
            })

        if sin_cobro_nuevo:
            return {'error': f'Las facturas {", ".join(sin_cobro_nuevo)} no tienen pagos nuevos desde el ultimo recibo'}

        fobj = fobjs[0]
        return {
            'success': True,
            'cliente': {
                'pdv_ruc': fobj.pdv_ruc,
                'pdv_nombrefactura': fobj.pdv_nombrefactura,
            },
            'facturas': result,
            'totales': {
                'total_factura': float(total_factura_all),
                'total_cobrado': float(total_cobrado_all),
                'total_saldo': float(total_saldo_all),
            }
        }

    def crear_recibo_cobro(self, *args, **kwargs) -> dict:
        """
        Crea un DocumentRecibo desde Cobros con soporte para pagos parciales.
        Calcula cobrado = total - doc_saldo (incremental desde el ultimo recibo).
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        facturas_ids = q.getlist('facturas[]') if hasattr(q, 'getlist') else q.get('facturas', [])

        if not facturas_ids:
            return {'error': 'Debe seleccionar al menos una factura'}

        today = datetime.today()
        fobjs = DocumentHeader.objects.filter(pk__in=facturas_ids)

        if not fobjs.exists():
            return {'error': 'No se encontraron las facturas seleccionadas'}

        # Validar mismo cliente
        rucs = set(fobjs.values_list('pdv_ruc', flat=True))
        if len(rucs) > 1:
            return {'error': 'Todas las facturas deben ser del mismo cliente'}

        # Validar que no sean facturas ya concluidas
        for f in fobjs:
            if f.doc_saldo == 0 and DocumentReciboDetail.objects.filter(prof_number=f.prof_number, saldo=0).exists():
                return {'error': f'La factura {f.doc_numero} ya esta concluida con recibo generado'}

        # Validar que todas tengan pagos registrados
        sin_pagos = [f.doc_numero for f in fobjs if not f.pagos.exists()]
        if sin_pagos:
            return {'error': f'Las facturas {sin_pagos} no tienen pagos registrados'}

        # Validar que haya pagos nuevos desde el ultimo recibo
        for f in fobjs:
            total_factura = f.get_total_venta_gs()
            saldo = f.doc_saldo or Decimal('0')
            total_pagado_acum = total_factura - saldo
            prev_cobrado = DocumentReciboDetail.objects.filter(
                prof_number=f.prof_number
            ).aggregate(total=Sum('cobrado'))['total'] or Decimal('0')
            if total_pagado_acum - prev_cobrado <= 0:
                return {'error': f'La factura {f.doc_numero} no tiene pagos nuevos desde el ultimo recibo'}

        fobj = fobjs[0]

        # Obtener tasa de cambio
        tasa_cambio = Decimal('1')
        try:
            cg = Cotizacion.objects.order_by('id').last()
            if cg:
                tasa_cambio = cg.dolar_venta
        except Exception:
            pass

        # Obtener Business activo del usuario logueado
        bobj = None
        try:
            profile = UserProfile.objects.filter(username=userobj.username).first()
            if profile:
                active_ub = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()
                if active_ub:
                    bobj = active_ub.businessobj
        except Exception:
            pass
        if not bobj:
            return {'error': 'No se encontró el negocio activo del usuario. Configure un negocio en su perfil.'}

        # Obtener siguiente numero de recibo disponible (tipo RC)
        eser = ekuatia_serials.Eserial()
        timbrado_result = eser.get_available_timbrado(qdict={'ruc': bobj.ruc})
        if timbrado_result.get('error'):
            return {'error': f'No se encontro timbrado: {timbrado_result["error"]}'}
        timbradoobj = timbrado_result['tobj']

        enumobj = Enumbers.objects.filter(
            expobj__timbradoobj__timbrado=timbradoobj['timbrado'],
            expobj__establecimiento=fobj.doc_establecimiento,
            tipo='RC',
            estado='L'
        ).order_by('numero').first()
        if not enumobj:
            return {'error': 'No hay numeros de recibo (RC) disponibles. Genere numeros en Gestion de Numeros.'}

        doc_numero_rc = enumobj.numero
        doc_expedicion_rc = enumobj.expobj.timbradoobj.eestablecimiento_set.get(
            establecimiento=fobj.doc_establecimiento
        ).expedicion
        ek_serie = timbradoobj['serie']
        ek_timbrado = timbradoobj['timbrado']
        ek_timbrado_vigencia = timbradoobj['inicio']
        ek_timbrado_vencimiento = timbradoobj['vencimiento']

        # Crear el recibo
        recobj = DocumentRecibo.objects.create(
            bs=fobj.bs,
            source='COBRO',
            ext_link=0,
            doc_moneda=fobj.doc_moneda,
            doc_fecha=today,
            doc_tipo='RC',
            doc_tipo_cod=9,
            doc_tipo_desc='RECIBOD',
            doc_op='COBRO',
            doc_numero=doc_numero_rc,
            doc_expedicion=fobj.doc_expedicion,
            doc_establecimiento=fobj.doc_establecimiento,
            doc_establecimiento_ciudad=fobj.doc_establecimiento_ciudad,
            doc_estado='INICIADO',
            doc_vencimiento=arrow.get().shift(days=30).strftime('%Y-%m-%d'),
            doc_total_factura=0,
            doc_total_nc=0,
            doc_cobrar=0,
            doc_retencion=0,
            doc_efectivo=0,
            doc_cheque=0,
            doc_cobrado=0,
            pdv_innominado=fobj.pdv_innominado,
            pdv_pais_cod=fobj.pdv_pais_cod,
            pdv_pais=fobj.pdv_pais,
            pdv_tipocontribuyente=fobj.pdv_tipocontribuyente,
            pdv_es_contribuyente=fobj.pdv_es_contribuyente,
            pdv_type_business=fobj.pdv_type_business,
            pdv_codigo=fobj.pdv_codigo,
            pdv_ruc=fobj.pdv_ruc,
            pdv_ruc_dv=fobj.pdv_ruc_dv,
            pdv_nombrefantasia=fobj.pdv_nombrefantasia,
            pdv_nombrefactura=fobj.pdv_nombrefactura,
            pdv_direccion_entrega=fobj.pdv_direccion_entrega,
            pdv_dir_calle_sec=fobj.pdv_dir_calle_sec,
            pdv_direccion_comple=fobj.pdv_direccion_comple,
            pdv_numero_casa=fobj.pdv_numero_casa,
            pdv_numero_casa_entrega=fobj.pdv_numero_casa_entrega,
            pdv_dpto_cod=fobj.pdv_dpto_cod,
            pdv_dpto_nombre=fobj.pdv_dpto_nombre,
            pdv_distrito_cod=fobj.pdv_distrito_cod,
            pdv_distrito_nombre=fobj.pdv_distrito_nombre,
            pdv_ciudad_cod=fobj.pdv_ciudad_cod,
            pdv_ciudad_nombre=fobj.pdv_ciudad_nombre,
            pdv_telefono=fobj.pdv_telefono,
            pdv_celular=fobj.pdv_celular,
            pdv_email=fobj.pdv_email,
            tasa_cambio=tasa_cambio,
            observacion='Recibo generado desde Cobros',
            cargado_fecha=today,
            cargado_usuario=userobj.username if userobj else 'system',
        )

        total_cobrado = Decimal('0')
        username = userobj.username if userobj else 'system'

        for f in fobjs:
            total_factura = f.get_total_venta_gs()
            saldo = f.doc_saldo or Decimal('0')

            total_pagado_acum = total_factura - saldo
            prev_cobrado = DocumentReciboDetail.objects.filter(
                prof_number=f.prof_number
            ).aggregate(total=Sum('cobrado'))['total'] or Decimal('0')
            cobrado = total_pagado_acum - prev_cobrado
            total_cobrado += cobrado

            retencion = f.retencionobj.retencion if f.retencionobj else 0
            retencion_numero = f.retencionobj.retencion_numero if f.retencionobj else 0

            recobj.documentrecibodetail_set.create(
                tipo=f.doc_tipo,
                prof_number=f.prof_number,
                establecimiento=f.doc_establecimiento,
                expedicion=f.doc_expedicion,
                numero=f.doc_numero,
                cobrado=cobrado,
                total=total_factura,
                saldo=saldo,
                retencion_numero=retencion_numero,
                retencion=retencion,
                observacion='ND',
                cargado_fecha=today,
                cargado_usuario=username,
            )

            # Solo marcar CONCLUIDO si saldo es 0
            if f.doc_saldo == 0:
                f.doc_estado = 'CONCLUIDO'
                f.save(update_fields=['doc_estado'])

        # Actualizar totales del recibo
        total_fe = recobj.documentrecibodetail_set.filter(tipo='FE').aggregate(
            total=Sum('total')
        ).get('total') or 0
        recobj.doc_total_factura = total_fe
        recobj.doc_cobrado = total_cobrado
        recobj.doc_efectivo = total_cobrado
        recobj.save()

        # Marcar numero de recibo como usado
        enumobj.estado = 'R'
        enumobj.save(update_fields=['estado'])

        logger.info(f'Recibo cobro creado: {recobj.id} - Numero {doc_numero_rc} - Cliente {fobj.pdv_ruc} - Total cobrado {total_cobrado}')

        return {
            'success': True,
            'message': f'Recibo N° {doc_numero_rc} generado correctamente por Gs {total_cobrado:,.0f}',
            'recibo_id': recobj.id,
        }

    def get_historial_recibos_factura(self, *args, **kwargs) -> dict:
        """
        Obtiene todos los recibos donde aparece una factura dada.
        """
        q = kwargs.get('qdict', {})
        factura_id = q.get('factura_id')

        if not factura_id:
            return {'error': 'ID de factura requerido'}

        try:
            factura = DocumentHeader.objects.get(pk=factura_id)
        except DocumentHeader.DoesNotExist:
            return {'error': 'Factura no encontrada'}

        detalles = DocumentReciboDetail.objects.filter(
            prof_number=factura.prof_number
        ).select_related('recobj').order_by('-recobj__doc_fecha')

        recibos = []
        for d in detalles:
            rec = d.recobj
            has_pdf = bool(rec.pdf_file) if rec.pdf_file else False
            recibos.append({
                'recibo_id': rec.id,
                'doc_numero': rec.doc_numero,
                'doc_fecha': rec.doc_fecha.strftime('%Y-%m-%d') if rec.doc_fecha else '',
                'doc_estado': rec.doc_estado,
                'source': rec.source,
                'doc_cobrado': float(rec.doc_cobrado or 0),
                'doc_total_factura': float(rec.doc_total_factura or 0),
                'cobrado_detalle': float(d.cobrado or 0),
                'total_detalle': float(d.total or 0),
                'saldo_detalle': float(d.saldo or 0),
                'has_pdf': has_pdf,
                'pdf_url': rec.pdf_file.url if has_pdf else None,
            })

        return {
            'success': True,
            'factura': {
                'doc_numero': factura.doc_numero,
                'pdv_nombrefactura': factura.pdv_nombrefactura,
                'pdv_ruc': factura.pdv_ruc,
            },
            'recibos': recibos,
            'total_recibos': len(recibos),
        }
