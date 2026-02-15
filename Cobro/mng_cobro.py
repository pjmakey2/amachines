import logging
from decimal import Decimal
from datetime import datetime, date
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.http import QueryDict
from django.db.models import Sum, Q
from Sifen.models import DocumentHeader
from Cobro.models import Pago

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
