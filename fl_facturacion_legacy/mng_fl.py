"""
Lógica de negocio para FL Facturación Legacy

Este módulo maneja las operaciones de facturación del sistema Frontliner,
integrándose con SIFEN para facturación electrónica.
"""

import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any

from django.conf import settings
from django.contrib.auth.models import User

from OptsIO import io_json
from Sifen.mng_sifen import MSifen
from Sifen.models import DocumentHeader, Clientes
from Sifen import mng_gmdata

from .fl_mysql_client import FLMySQLClient

logger = logging.getLogger(__name__)


class MFLFacturacion:
    """
    Clase para manejar las operaciones de facturación del sistema Frontliner.

    Trabaja directamente sobre la base de datos MySQL de Frontliner y genera
    facturas electrónicas en SIFEN.
    """

    def __init__(self, userobj=None, rq=None, files=None, qdict=None, **kwargs):
        self.userobj = userobj
        self.request = rq
        self.files = files
        self.qdict = qdict or {}
        self.kwargs = kwargs
        self.mysql_client = FLMySQLClient()
        self.gdata = mng_gmdata.Gdata()

    # =========================================================================
    # CLIENTES
    # =========================================================================

    def buscar_clientes(self, *args, **kwargs) -> Dict:
        """
        Busca clientes en la base de datos Frontliner.

        Query params:
            - termino: Texto a buscar
            - sucursal: Filtrar por sucursal (opcional)
        """
        q = kwargs.get('qdict', {})
        termino = q.get('termino', '')

        if len(termino) < 2:
            return {'error': 'Ingrese al menos 2 caracteres para buscar'}

        try:
            sucursal = int(q.get('sucursal')) if q.get('sucursal') else None
            clientes = self.mysql_client.buscar_clientes(termino, sucursal)

            # Formatear para el frontend
            result = []
            for c in clientes:
                nombre_completo = f"{c.get('clientenombre', '')} {c.get('clienteapellido', '')}".strip()
                result.append({
                    'id': c['clientecodigo'],
                    'codigo': c['clientecodigo'],
                    'nombre': nombre_completo,
                    'ruc': c.get('ruc', ''),
                    'cedula': c.get('clienteci', ''),
                    'telefono': c.get('clientetelefono', ''),
                    'celular': c.get('clientecelular', ''),
                    'email': c.get('clientemail', ''),
                    'direccion': c.get('clientedireccion', ''),
                    'sucursal': c.get('sucursal'),
                })

            return {'clientes': result}

        except Exception as e:
            logger.error(f"Error buscando clientes: {e}")
            return {'error': f'Error buscando clientes: {str(e)}'}

    def buscar_clientes_select2(self, *args, **kwargs) -> Dict:
        """
        Busca clientes para Select2 (como datospaquetesentrega.php).

        Devuelve formato Select2: {items: [{id, text}], total_count}

        Query params:
            - q: Texto a buscar (mínimo 3 caracteres)
            - page: Página para paginación (opcional)
        """
        q = kwargs.get('qdict', {})
        termino = q.get('q', '')
        page = int(q.get('page', 1) or 1)

        if len(termino) < 3:
            return {'items': [], 'total_count': 0}

        try:
            # Buscar con límite para paginación
            limit = 30
            offset = (page - 1) * limit

            clientes = self.mysql_client.buscar_clientes(termino, limit=limit + 1)

            # Formatear para Select2
            items = []
            for c in clientes[:limit]:
                # Usar etiqueta como en PHP: "codigo - nombre apellido"
                etiqueta = c.get('etiqueta', '')
                if not etiqueta:
                    etiqueta = f"{c.get('clientecodigo', '')} - {c.get('clientenombre', '')} {c.get('clienteapellido', '')}".strip()

                items.append({
                    'id': c['clientecodigo'],
                    'text': etiqueta
                })

            # Si hay más registros que el límite, hay más páginas
            has_more = len(clientes) > limit

            return {
                'items': items,
                'total_count': (page * limit) + (1 if has_more else 0)
            }

        except Exception as e:
            logger.error(f"Error buscando clientes Select2: {e}")
            return {'items': [], 'total_count': 0, 'error': str(e)}

    def buscar_acuses_select2(self, *args, **kwargs) -> Dict:
        """
        Busca acuses (tickets/facturas) para Select2.
        Busca por número de acuse O por nombre de cliente.

        Devuelve formato Select2: {items: [{id, text}], total_count}

        Query params:
            - q: Texto a buscar (número de acuse o nombre de cliente)
            - page: Página para paginación (opcional)
        """
        q = kwargs.get('qdict', {})
        termino = q.get('q', '').strip()
        page = int(q.get('page', 1) or 1)

        if len(termino) < 2:
            return {'items': [], 'total_count': 0}

        try:
            limit = 30
            facturas = self.mysql_client.buscar_acuses_para_facturar(termino, limit=limit + 1)

            # Formatear para Select2
            items = []
            for f in facturas[:limit]:
                nombre_cliente = f"{f.get('clientenombre', '')} {f.get('clienteapellido', '')}".strip()
                monto_gs = float(f.get('montogs', 0) or 0)

                # Determinar estado
                estado_txt = ""
                if f.get('facturaemitida') == 1:
                    estado_txt = "[FACTURADO]"
                elif f.get('estado') == 2:
                    estado_txt = "[Pago OK]"
                else:
                    estado_txt = "[Pendiente]"

                # Etiqueta: "Acuse #123 - CLIENTE - Gs. 500,000 [Estado]"
                etiqueta = f"#{f['acuse_id']} - {nombre_cliente} - Gs. {int(monto_gs):,} {estado_txt}"

                items.append({
                    'id': f['acuse_id'],
                    'text': etiqueta
                })

            has_more = len(facturas) > limit

            return {
                'items': items,
                'total_count': (page * limit) + (1 if has_more else 0)
            }

        except Exception as e:
            logger.error(f"Error buscando acuses Select2: {e}")
            import traceback
            traceback.print_exc()
            return {'items': [], 'total_count': 0, 'error': str(e)}

    def get_datos_cliente_entrega(self, *args, **kwargs) -> Dict:
        """
        Obtiene datos del cliente para entrega de paquetes.
        Replica exactamente la lógica de datospaquetesentrega.php::obtenerDatosEntrega()

        Query params:
            - clientecodigo: ID del cliente

        Retorna:
            {
                resultado_exitoso: bool,
                mensaje: str (si hay error),
                dato: {
                    personaAutorizada: {...},
                    listaPaquetes: [...]
                }
            }
        """
        q = kwargs.get('qdict', {})
        clientecodigo = q.get('clientecodigo')

        if not clientecodigo:
            return {
                'resultado_exitoso': False,
                'mensaje': 'Código de cliente requerido'
            }

        try:
            # 1. Obtener datos del cliente
            cliente = self.mysql_client.get_cliente(int(clientecodigo))
            if not cliente:
                return {
                    'resultado_exitoso': False,
                    'mensaje': 'Cliente no encontrado'
                }

            # 2. Obtener sucursal del cliente
            sucursal_codigo = cliente.get('sucursal', 1)
            sucursal_info = self.mysql_client.get_sucursal(sucursal_codigo)

            # 3. Obtener paquetes pendientes
            paquetes = self.mysql_client.get_paquetes_pendientes_cliente(int(clientecodigo))

            # 4. Formatear persona autorizada (como en PHP)
            persona_autorizada = {
                'nombreAutorizada': cliente.get('clientenombre', ''),
                'apellidoAutorizada': cliente.get('clienteapellido', ''),
                'cedulaAutorizada': cliente.get('clienteci', ''),
                'estante': cliente.get('estante', ''),
                'tarifa': str(cliente.get('tarifa', '22.50')),
                'sucursal': sucursal_codigo,
                'sucursalNombre': sucursal_info.get('sucursalnombre', '') if sucursal_info else '',
                'sucursalColorFondo': sucursal_info.get('sucursalcolorfondo', '#6c757d') if sucursal_info else '#6c757d',
                'sucursalColorTexto': sucursal_info.get('sucursalcolortexto', '#ffffff') if sucursal_info else '#ffffff',
            }

            # 5. Formatear lista de paquetes
            lista_paquetes = []
            for p in paquetes:
                lista_paquetes.append({
                    'paquetecodigo': p.get('paquetecodigo'),
                    'tracking': p.get('tracking', ''),
                    'descripcion': p.get('descripcion', ''),
                    'peso_real': float(p.get('peso_real', 0) or 0),
                    'embarquecodigo': p.get('embarquecodigo'),
                    'estadoembarque': p.get('estadoembarquedescripcion', ''),
                    'fecha_embarque': p.get('fecha_embarque').strftime('%d/%m/%Y') if p.get('fecha_embarque') else '',
                    'fecha_llegada': p.get('fecha_llegada').strftime('%d/%m/%Y') if p.get('fecha_llegada') else '',
                })

            return {
                'resultado_exitoso': True,
                'dato': {
                    'personaAutorizada': persona_autorizada,
                    'listaPaquetes': lista_paquetes
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos cliente entrega: {e}")
            import traceback
            traceback.print_exc()
            return {
                'resultado_exitoso': False,
                'mensaje': f'Error obteniendo datos: {str(e)}'
            }

    def get_cliente(self, *args, **kwargs) -> Dict:
        """Obtiene datos de un cliente específico."""
        q = kwargs.get('qdict', {})
        clientecodigo = q.get('clientecodigo')

        if not clientecodigo:
            return {'error': 'Código de cliente requerido'}

        try:
            cliente = self.mysql_client.get_cliente(int(clientecodigo))
            if not cliente:
                return {'error': 'Cliente no encontrado'}

            nombre_completo = f"{cliente.get('clientenombre', '')} {cliente.get('clienteapellido', '')}".strip()

            # Obtener deuda
            deuda = self.mysql_client.get_deuda_cliente(int(clientecodigo))

            return {
                'cliente': {
                    'id': cliente['clientecodigo'],
                    'codigo': cliente['clientecodigo'],
                    'nombre': nombre_completo,
                    'nombre_factura': nombre_completo,
                    'ruc': cliente.get('ruc', ''),
                    'cedula': cliente.get('cedula', ''),
                    'telefono': cliente.get('telefono', ''),
                    'celular': cliente.get('celular', ''),
                    'email': cliente.get('email', ''),
                    'direccion': cliente.get('direccion', ''),
                    'sucursal': cliente.get('sucursal'),
                    'saldo_pendiente': float(cliente.get('saldopendiente', 0) or 0),
                    'deuda_total': float(deuda),
                }
            }

        except Exception as e:
            logger.error(f"Error obteniendo cliente: {e}")
            return {'error': f'Error obteniendo cliente: {str(e)}'}

    # =========================================================================
    # PAQUETES
    # =========================================================================

    def get_paquetes_cliente(self, *args, **kwargs) -> Dict:
        """
        Obtiene los paquetes pendientes de entrega para un cliente.
        """
        q = kwargs.get('qdict', {})
        clientecodigo = q.get('clientecodigo')

        if not clientecodigo:
            return {'error': 'Código de cliente requerido'}

        try:
            paquetes = self.mysql_client.get_paquetes_pendientes_cliente(int(clientecodigo))

            # Calcular totales
            total_peso = sum(float(p.get('peso_real', 0) or 0) for p in paquetes)
            total_usd = sum(
                float(p.get('peso_real', 0) or 0) * float(p.get('tarifa', 0) or 0)
                for p in paquetes
            )

            # Obtener cotización
            cotizacion = self.mysql_client.get_cotizacion_usd()

            return {
                'paquetes': paquetes,
                'total_paquetes': len(paquetes),
                'total_peso': total_peso,
                'total_usd': total_usd,
                'total_gs': float(Decimal(str(total_usd)) * cotizacion),
                'cotizacion_usd': float(cotizacion),
            }

        except Exception as e:
            logger.error(f"Error obteniendo paquetes: {e}")
            return {'error': f'Error obteniendo paquetes: {str(e)}'}

    # =========================================================================
    # TARIFAS ESCALONADAS (según PHP)
    # =========================================================================

    # Límites de peso y tarifas correspondientes
    # {"peso_limite_superior":[5,8,20,1000000],"tarifa":[22.50,21.90,21.00,22.50]}
    TARIFA_LIMITES = [5, 8, 20, 1000000]
    TARIFA_VALORES = [22.50, 21.90, 21.00, 22.50]

    def calcular_tarifa_por_peso(self, peso_total: float) -> float:
        """
        Calcula la tarifa según el peso total (como en PHP).
        """
        for i, limite in enumerate(self.TARIFA_LIMITES):
            if peso_total <= limite:
                return self.TARIFA_VALORES[i]
        return self.TARIFA_VALORES[-1]

    # =========================================================================
    # GENERAR TICKET (ACUSE)
    # =========================================================================

    def generar_ticket(self, *args, **kwargs) -> Dict:
        """
        Genera un ticket/acuse de entrega.
        Replica exactamente la lógica de Ticket.php

        Query params:
            - clientecodigo: ID del cliente
            - paquetes_codigos: Lista de códigos de paquetes (JSON)
            - tarifa: Tarifa USD/kg
            - tasa_usd: Cotización USD
            - peso_total: Peso total en kg
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')

        clientecodigo = q.get('clientecodigo')
        paquetes_codigos = io_json.from_json(q.get('paquetes_codigos', '[]'))
        tarifa = float(q.get('tarifa', 0) or 0)
        tasa_usd = float(q.get('tasa_usd', 7500) or 7500)
        peso_total = float(q.get('peso_total', 0) or 0)

        if not clientecodigo:
            return {'error': 'Código de cliente requerido'}

        if not paquetes_codigos:
            return {'error': 'Seleccione al menos un paquete'}

        if tarifa <= 0:
            return {'error': 'Tarifa inválida'}

        if peso_total <= 0:
            return {'error': 'Peso total inválido'}

        try:
            # Usar código de funcionario 1 por defecto o del usuario
            funcionario_codigo = 1
            if userobj and hasattr(userobj, 'id'):
                funcionario_codigo = userobj.id

            acuse_id = self.mysql_client.generar_ticket(
                clientecodigo=int(clientecodigo),
                paquetes_codigos=paquetes_codigos,
                tarifa=tarifa,
                tasa_usd=tasa_usd,
                peso_total=peso_total,
                funcionario_codigo=funcionario_codigo
            )

            # Calcular montos para respuesta
            monto_usd = peso_total * tarifa
            monto_gs_raw = monto_usd * tasa_usd
            monto_gs = round(monto_gs_raw / 1000) * 1000

            return {
                'success': True,
                'message': f'Ticket generado correctamente',
                'acuse_id': acuse_id,
                'monto_usd': round(monto_usd, 2),
                'monto_gs': monto_gs,
                'fecha': datetime.now().strftime('%d/%m/%Y'),
                'hora': datetime.now().strftime('%H:%M:%S'),
            }

        except Exception as e:
            logger.error(f"Error generando ticket: {e}")
            return {'error': f'Error generando ticket: {str(e)}'}

    # =========================================================================
    # FACTURAS / ACUSES
    # =========================================================================

    def get_facturas_pendientes(self, *args, **kwargs) -> Dict:
        """
        Obtiene las facturas pendientes de emitir.
        """
        q = kwargs.get('qdict', {})

        try:
            sucursal = int(q.get('sucursal')) if q.get('sucursal') else None
            limit = int(q.get('limit', 100))

            facturas = self.mysql_client.get_facturas_pendientes(sucursal, limit)

            # Formatear para el frontend
            result = []
            for f in facturas:
                nombre_cliente = f"{f.get('clientenombre', '')} {f.get('clienteapellido', '')}".strip()
                result.append({
                    'acuse_id': f['acuse_id'],
                    'fecha': f['fecha'].strftime('%d/%m/%Y') if f.get('fecha') else '',
                    'cliente_codigo': f.get('clientecodigo'),
                    'cliente_nombre': nombre_cliente,
                    'cliente_ruc': f.get('ruc', ''),
                    'monto_usd': float(f.get('montousd', 0) or 0),
                    'monto_gs': float(f.get('montogs', 0) or 0),
                    'estado': 'Pendiente' if f.get('facturaemitida') == 2 else 'Facturado',
                    'observacion': f.get('obs', ''),
                })

            return {'facturas': result, 'total': len(result)}

        except Exception as e:
            logger.error(f"Error obteniendo facturas pendientes: {e}")
            return {'error': f'Error obteniendo facturas: {str(e)}'}

    def get_todas_facturas(self, *args, **kwargs) -> Dict:
        """
        Obtiene todas las facturas con paginación y filtros.
        """
        q = kwargs.get('qdict', {})

        try:
            sucursal = int(q.get('sucursal')) if q.get('sucursal') else None
            limit = int(q.get('limit', 100))
            offset = int(q.get('offset', 0))

            # Construir filtros
            filtros = {}
            if q.get('acuse_id'):
                filtros['acuse_id'] = q.get('acuse_id')
            if q.get('clientecodigo'):
                filtros['clientecodigo'] = q.get('clientecodigo')
            if q.get('clientenombre'):
                filtros['clientenombre'] = q.get('clientenombre')
            if q.get('facturaemitida'):
                filtros['facturaemitida'] = q.get('facturaemitida')
            if q.get('fecha_desde'):
                filtros['fecha_desde'] = q.get('fecha_desde')
            if q.get('fecha_hasta'):
                filtros['fecha_hasta'] = q.get('fecha_hasta')

            facturas = self.mysql_client.get_todas_facturas(sucursal, limit, offset, filtros)
            total = self.mysql_client.count_facturas(sucursal, filtros)

            # Formatear para el frontend
            result = []
            for f in facturas:
                nombre_cliente = f"{f.get('clientenombre', '')} {f.get('clienteapellido', '')}".strip()

                # Calcular total pagado
                tasa = float(f.get('dolar_venta', 1) or 1)
                total_pagado = (
                    float(f.get('montoefegs', 0) or 0) +
                    float(f.get('montoefeusd', 0) or 0) * tasa +
                    float(f.get('montotcgs', 0) or 0) +
                    float(f.get('montotcusd', 0) or 0) * tasa +
                    float(f.get('montotdgs', 0) or 0) +
                    float(f.get('montotdusd', 0) or 0) * tasa +
                    float(f.get('montochkgs', 0) or 0) +
                    float(f.get('montochkusd', 0) or 0) * tasa
                )

                result.append({
                    'acuse_id': f['acuse_id'],
                    'fecha': f['fecha'].strftime('%d/%m/%Y') if f.get('fecha') else '',
                    'cliente_codigo': f.get('clientecodigo'),
                    'cliente_nombre': nombre_cliente,
                    'cliente_ruc': f.get('ruc', ''),
                    'monto_usd': float(f.get('montousd', 0) or 0),
                    'monto_gs': float(f.get('montogs', 0) or 0),
                    'total_pagado': total_pagado,
                    'pendiente': float(f.get('montopendiente', 0) or 0),
                    'estado': f.get('estado'),  # 1=pendiente pago, 2=pago confirmado
                    'facturado': f.get('facturaemitida') == 1,
                    'id_factura': f.get('id_factura', ''),
                    'observacion': f.get('obs', ''),
                })

            return {
                'facturas': result,
                'total': total,
                'limit': limit,
                'offset': offset
            }

        except Exception as e:
            logger.error(f"Error obteniendo facturas: {e}")
            return {'error': f'Error obteniendo facturas: {str(e)}'}

    def get_factura_detalle(self, *args, **kwargs) -> Dict:
        """
        Obtiene el detalle completo de una factura/acuse.
        """
        q = kwargs.get('qdict', {})
        acuse_id = q.get('acuse_id')

        if not acuse_id:
            return {'error': 'ID de acuse requerido'}

        try:
            factura = self.mysql_client.get_factura(int(acuse_id))
            if not factura:
                return {'error': 'Factura no encontrada'}

            paquetes = self.mysql_client.get_paquetes_por_acuse(int(acuse_id))

            nombre_cliente = f"{factura.get('clientenombre', '')} {factura.get('clienteapellido', '')}".strip()
            tasa = float(factura.get('dolar_venta', 1) or 1)

            # Calcular totales de pago
            efectivo_gs = float(factura.get('montoefegs', 0) or 0)
            efectivo_usd = float(factura.get('montoefeusd', 0) or 0)
            tc_gs = float(factura.get('montotcgs', 0) or 0)
            tc_usd = float(factura.get('montotcusd', 0) or 0)
            td_gs = float(factura.get('montotdgs', 0) or 0)
            td_usd = float(factura.get('montotdusd', 0) or 0)
            cheque_gs = float(factura.get('montochkgs', 0) or 0)
            cheque_usd = float(factura.get('montochkusd', 0) or 0)

            total_pagado = (
                efectivo_gs + (efectivo_usd * tasa) +
                tc_gs + (tc_usd * tasa) +
                td_gs + (td_usd * tasa) +
                cheque_gs + (cheque_usd * tasa)
            )

            # Obtener deuda del cliente
            deuda = self.mysql_client.get_deuda_cliente(int(factura['clientecodigo']))

            # Buscar en Clientes (Sifen) por anclaje_cliente
            cliente_codigo = str(factura.get('clientecodigo', ''))
            ruc_factura = factura.get('rucusado', '')
            nombre_factura = factura.get('razonsocial', '')
            correo_factura = factura.get('email', '')

            try:
                cliente_sifen = Clientes.objects.filter(anclaje_cliente=cliente_codigo).first()
                if cliente_sifen:
                    # Si encuentra el registro en Clientes (Sifen), usar esos datos
                    ruc_factura = cliente_sifen.pdv_ruc or ruc_factura
                    nombre_factura = cliente_sifen.pdv_nombrefactura or nombre_factura
                    correo_factura = cliente_sifen.pdv_email or correo_factura
            except Exception as e:
                logger.warning(f"Error buscando cliente en Sifen por anclaje_cliente={cliente_codigo}: {e}")
                # Si hay error, continuar con los datos de MySQL

            return {
                'factura': {
                    'acuse_id': factura['acuse_id'],
                    'fecha': factura['fecha'].strftime('%d/%m/%Y') if factura.get('fecha') else '',
                    'cliente_codigo': factura.get('clientecodigo'),
                    'cliente_nombre': nombre_cliente,
                    'cliente_ruc': factura.get('ruc', ''),
                    'cliente_cedula': factura.get('cedula', ''),
                    'cliente_direccion': factura.get('direccion', ''),
                    'cliente_telefono': factura.get('telefono', ''),
                    'cliente_email': factura.get('email', ''),
                    'cliente_deuda': float(deuda),
                    'monto_usd': float(factura.get('montousd', 0) or 0),
                    'monto_gs': float(factura.get('montogs', 0) or 0),
                    'cotizacion': tasa,
                    'peso_real': float(factura.get('peso_real', 0) or 0),
                    'tarifa': float(factura.get('tarifa', 0) or 0),
                    'estado': factura.get('estado'),
                    'facturado': factura.get('facturaemitida') == 1,
                    'id_factura': factura.get('id_factura', ''),
                    'ruc_factura': ruc_factura,
                    'nombre_factura': nombre_factura,
                    'correo_factura': correo_factura,
                    'observacion': factura.get('obs', ''),
                    # Pagos
                    'efectivo_gs': efectivo_gs,
                    'efectivo_usd': efectivo_usd,
                    'tc_gs': tc_gs,
                    'tc_usd': tc_usd,
                    'td_gs': td_gs,
                    'td_usd': td_usd,
                    'cheque_gs': cheque_gs,
                    'cheque_usd': cheque_usd,
                    'descuento': float(factura.get('descuento', 0) or 0),
                    'total_pagado': total_pagado,
                    'pendiente': float(factura.get('montopendiente', 0) or 0),
                    # IVA
                    'monto_exenta': float(factura.get('montogsexenta', 0) or 0),
                    'monto_gravada': float(factura.get('montogsgravada', 0) or 0),
                    'monto_iva': float(factura.get('montoivags', 0) or 0),
                },
                'paquetes': paquetes,
                'total_paquetes': len(paquetes),
            }

        except Exception as e:
            logger.error(f"Error obteniendo detalle de factura: {e}")
            return {'error': f'Error obteniendo factura: {str(e)}'}

    # =========================================================================
    # CONFIRMAR PAGO
    # =========================================================================

    def confirmar_pago(self, *args, **kwargs) -> Dict:
        """
        Confirma el pago de un acuse.

        Query params:
            - acuse_id: ID del acuse
            - efectivo_gs, efectivo_usd
            - tc_gs, tc_usd
            - td_gs, td_usd
            - cheque_gs, cheque_usd
            - descuento
            - ruc_factura
            - nombre_factura
            - observaciones
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')

        acuse_id = q.get('acuse_id')

        if not acuse_id:
            return {'error': 'ID de acuse requerido'}

        try:
            pagos = {
                'efectivo_gs': float(q.get('efectivo_gs', 0) or 0),
                'efectivo_usd': float(q.get('efectivo_usd', 0) or 0),
                'tc_gs': float(q.get('tc_gs', 0) or 0),
                'tc_usd': float(q.get('tc_usd', 0) or 0),
                'td_gs': float(q.get('td_gs', 0) or 0),
                'td_usd': float(q.get('td_usd', 0) or 0),
                'cheque_gs': float(q.get('cheque_gs', 0) or 0),
                'cheque_usd': float(q.get('cheque_usd', 0) or 0),
                'descuento': float(q.get('descuento', 0) or 0),
            }

            ruc_factura = q.get('ruc_factura', '')
            nombre_factura = q.get('nombre_factura', '')
            observaciones = q.get('observaciones', '')

            funcionario_codigo = 1
            if userobj and hasattr(userobj, 'id'):
                funcionario_codigo = userobj.id

            self.mysql_client.confirmar_pago(
                acuse_id=int(acuse_id),
                pagos=pagos,
                ruc_factura=ruc_factura,
                nombre_factura=nombre_factura,
                observaciones=observaciones,
                funcionario_codigo=funcionario_codigo
            )

            return {
                'success': True,
                'message': 'Pago confirmado correctamente'
            }

        except Exception as e:
            logger.error(f"Error confirmando pago: {e}")
            return {'error': f'Error confirmando pago: {str(e)}'}

    # =========================================================================
    # GENERAR FACTURA SIFEN
    # =========================================================================

    def generar_factura_sifen(self, *args, **kwargs) -> Dict:
        """
        Genera una factura electrónica SIFEN a partir de un acuse.

        Este método:
        1. Obtiene los datos del acuse de MySQL
        2. Crea el DocumentHeader en SIFEN usando MSifen
        3. Actualiza MySQL con el CDC generado

        Query params:
            - acuse_id: ID del acuse a facturar
        """
        q = kwargs.get('qdict', {})
        userobj = kwargs.get('userobj')
        dbcon = q.get('dbcon', 'default')

        acuse_id = q.get('acuse_id')

        if not acuse_id:
            return {'error': 'ID de acuse requerido'}

        try:
            # 1. Obtener datos del acuse
            factura = self.mysql_client.get_factura(int(acuse_id))
            if not factura:
                return {'error': 'Acuse no encontrado'}

            # Verificar que esté confirmado (estado=2) y no facturado
            if factura.get('estado') != 2:
                return {'error': 'El acuse debe tener el pago confirmado antes de facturar'}

            if factura.get('facturaemitida') == 1:
                return {'error': 'Este acuse ya fue facturado'}

            # Obtener paquetes
            paquetes = self.mysql_client.get_paquetes_por_acuse(int(acuse_id))

            # 2. Preparar datos para SIFEN
            # Prioridad: valores del frontend > datos de MySQL
            ruc_frontend = q.get('ruc_factura', '').strip()
            nombre_frontend = q.get('nombre_factura', '').strip()
            correo_frontend = q.get('correo_factura', '').strip()

            # Usar valores del frontend si están disponibles
            if ruc_frontend:
                ruc_cliente = ruc_frontend
            else:
                ruc_cliente = factura.get('rucusado') or factura.get('ruc') or ''

            # Limpiar RUC: eliminar puntos y guiones (ej: "29.38.965-1" → "29389651")
            if ruc_cliente:
                ruc_cliente = ruc_cliente.replace('.', '').replace('-', '')

            # VALIDAR que el RUC sea solo números (sin el dígito verificador)
            ruc_sin_dv = ruc_cliente.split('-')[0] if '-' in ruc_cliente else ruc_cliente
            if ruc_sin_dv and ruc_sin_dv not in ['0', '']:
                if not ruc_sin_dv.isdigit():
                    return {'error': f'El RUC debe contener solo números. RUC ingresado: {ruc_frontend}'}

            if nombre_frontend:
                nombre_cliente = nombre_frontend
            else:
                nombre_cliente = factura.get('razonsocial') or f"{factura.get('clientenombre', '')} {factura.get('clienteapellido', '')}".strip()

            # Calcular DV del RUC
            ruc_dv = ''
            if ruc_cliente and ruc_cliente not in ['0', '']:
                ruc_dv = self.gdata.calculate_dv(ruc_cliente)

            # Determinar tipo de contribuyente
            # Si no tiene RUC válido, es innominado/no contribuyente
            if not ruc_cliente or ruc_cliente in ['0', '']:
                pdv_tipocontribuyente = '3'  # No contribuyente
                pdv_es_contribuyente = False
                pdv_innominado = True
            else:
                pdv_tipocontribuyente = '1'  # Persona física por defecto
                pdv_es_contribuyente = True
                pdv_innominado = False

            # Preparar detalles de la factura
            tasa = float(factura.get('dolar_venta', 1) or 1)
            details = []

            # Determinar descripción según el tipo de factura (como en PHP JS líneas 3440-3444)
            # Si hay paquetes → "Servicio de transporte de paquetes"
            # Si no hay paquetes (otro concepto) → usar obs o descripción personalizada

            if paquetes:
                # Factura de paquetes - siempre usa "Servicio de transporte de paquetes"
                # (como en PHP JS líneas 3440-3444: concepto = 'Servicio de transporte de paquetes')
                monto_total_gs = sum(float(paq.get('montogsdet', 0) or 0) for paq in paquetes)
                if monto_total_gs > 0:
                    details.append({
                        'prod_cod': 920,
                        'prod_descripcion': 'Servicio de transporte de paquetes',
                        'cantidad': 1,
                        'precio_unitario': monto_total_gs,
                        'g10': 100,  # 100% gravado al 10%
                        'g5': 0,
                        'exenta': 0,
                    })
            else:
                # Factura por otro concepto - usar obs como descripción
                monto_gs = float(factura.get('montogs', 0) or 0)
                descripcion = factura.get('obs') or 'Servicios varios'
                if monto_gs > 0:
                    details.append({
                        'prod_cod': 920,
                        'prod_descripcion': descripcion,
                        'cantidad': 1,
                        'precio_unitario': monto_gs,
                        'g10': 100,
                        'g5': 0,
                        'exenta': 0,
                    })

            if not details:
                return {'error': 'No hay items para facturar'}

            # 3. Construir uc_fields para MSifen
            # Obtener establecimiento del frontend (default: 1)
            establecimiento = q.get('establecimiento', '1')

            # Obtener condición de venta (contado/crédito) desde el frontend
            doc_cre_tipo_cod = q.get('doc_cre_tipo_cod', '1')  # Default: Contado
            doc_vencimiento = q.get('doc_vencimiento', '')

            uc_fields = {
                'doc_tipo': 'FE',  # Factura Electrónica
                'doc_moneda': 'PYG',
                'doc_establecimiento': establecimiento,
                'pdv_ruc': ruc_cliente,
                'pdv_ruc_dv': ruc_dv,
                'pdv_nombrefactura': nombre_cliente,
                'pdv_nombrefantasia': nombre_cliente,
                'pdv_tipocontribuyente': pdv_tipocontribuyente,
                'pdv_es_contribuyente': pdv_es_contribuyente,
                'pdv_innominado': pdv_innominado,
                'pdv_direccion_entrega': factura.get('direccion', ''),
                'pdv_telefono': factura.get('telefono', ''),
                'pdv_celular': factura.get('celular') or '000000',
                'pdv_email': factura.get('email') or 'nomail@nomail.com',
                'pdv_pais_cod': 'PRY',
                'pdv_pais': 'Paraguay',
                'pdv_dpto_cod': 1,
                'pdv_dpto_nombre': 'CAPITAL',
                'pdv_ciudad_cod': 1,
                'pdv_ciudad_nombre': 'ASUNCION',
                'doc_tipo_ope': 2,  # Prestación de servicios
                'doc_tipo_ope_desc': 'Prestación de servicios',
                'doc_cre_tipo_cod': doc_cre_tipo_cod,
                'doc_tipo_pago_cod': 1,  # Efectivo (se puede mejorar según forma de pago)
                'observacion': f"Acuse: {acuse_id}. {factura.get('obs', '')}",
                'ext_link': acuse_id,  # Guardar referencia al acuse
                'source': 'FL_LEGACY',
                'details': details,
            }

            # Si es crédito (doc_cre_tipo_cod == 2), agregar fecha de vencimiento
            if doc_cre_tipo_cod == '2' or doc_cre_tipo_cod == 2:
                if doc_vencimiento:
                    uc_fields['doc_vencimiento'] = doc_vencimiento

            # Determinar forma de pago principal
            efectivo = float(factura.get('montoefegs', 0) or 0) + float(factura.get('montoefeusd', 0) or 0) * tasa
            tarjeta_credito = float(factura.get('montotcgs', 0) or 0) + float(factura.get('montotcusd', 0) or 0) * tasa
            tarjeta_debito = float(factura.get('montotdgs', 0) or 0) + float(factura.get('montotdusd', 0) or 0) * tasa
            cheque = float(factura.get('montochkgs', 0) or 0) + float(factura.get('montochkusd', 0) or 0) * tasa

            # Seleccionar el tipo de pago principal
            if tarjeta_credito >= max(efectivo, tarjeta_debito, cheque):
                uc_fields['doc_tipo_pago_cod'] = 3  # Tarjeta de crédito
                uc_fields['doc_tipo_pago'] = 'Tarjeta de crédito'
            elif tarjeta_debito >= max(efectivo, cheque):
                uc_fields['doc_tipo_pago_cod'] = 4  # Tarjeta de débito
                uc_fields['doc_tipo_pago'] = 'Tarjeta de débito'
            elif cheque >= efectivo:
                uc_fields['doc_tipo_pago_cod'] = 2  # Cheque
                uc_fields['doc_tipo_pago'] = 'Cheque'
            else:
                uc_fields['doc_tipo_pago_cod'] = 1  # Efectivo
                uc_fields['doc_tipo_pago'] = 'Efectivo'

            # 4. Crear factura en SIFEN
            msifen = MSifen()

            result, _, _ = msifen.create_documentheader(
                userobj=userobj,
                qdict={
                    'dbcon': dbcon,
                    'uc_fields': io_json.to_json(uc_fields)
                }
            )

            if result.get('error'):
                return result

            # 5. Obtener el CDC generado
            doc_id = result.get('record_id')
            if not doc_id:
                return {'error': 'Error obteniendo ID del documento creado'}

            docobj = DocumentHeader.objects.using(dbcon).get(pk=doc_id)

            # Usar el número de factura (solo el número, sin formato)
            # El sistema PHP espera un número de máximo 10 dígitos
            id_factura = docobj.doc_numero

            # 6. Actualizar MySQL con el número de factura
            funcionario_codigo = 1
            if userobj and hasattr(userobj, 'id'):
                funcionario_codigo = userobj.id

            self.mysql_client.marcar_factura_emitida(
                acuse_id=int(acuse_id),
                id_factura=id_factura,
                funcionario_codigo=funcionario_codigo
            )

            # 7. Generar PDF de la factura
            pdf_result = msifen.generando_documentheader(
                userobj=userobj,
                qdict={
                    'dbcon': dbcon,
                    'id': doc_id
                }
            )
            ek_pdf_file = pdf_result.get('ek_pdf_file', '')

            # 8. Crear/Actualizar registro en Clientes (Sifen) con anclaje_cliente
            try:
                cliente_codigo = str(factura.get('clientecodigo', ''))
                correo_cliente = correo_frontend or factura.get('email', '')

                # Buscar si ya existe un cliente con este anclaje_cliente
                cliente_sifen = Clientes.objects.using(dbcon).filter(anclaje_cliente=cliente_codigo).first()

                if cliente_sifen:
                    # Actualizar registro existente
                    updated = False
                    if ruc_cliente and cliente_sifen.pdv_ruc != ruc_cliente:
                        cliente_sifen.pdv_ruc = ruc_cliente
                        cliente_sifen.pdv_ruc_dv = int(ruc_dv) if ruc_dv else 0
                        updated = True
                    if nombre_cliente and cliente_sifen.pdv_nombrefactura != nombre_cliente:
                        cliente_sifen.pdv_nombrefactura = nombre_cliente
                        updated = True
                    if correo_cliente and cliente_sifen.pdv_email != correo_cliente:
                        cliente_sifen.pdv_email = correo_cliente
                        updated = True

                    if updated:
                        cliente_sifen.save(using=dbcon)
                        logger.info(f"Cliente actualizado en Sifen: anclaje_cliente={cliente_codigo}")
                else:
                    # Crear nuevo registro
                    # calculate_dv() retorna int, convertir si es necesario
                    ruc_dv_int = int(ruc_dv) if ruc_dv else 0

                    Clientes.objects.using(dbcon).create(
                        anclaje_cliente=cliente_codigo,
                        pdv_ruc=ruc_cliente or '',
                        pdv_ruc_dv=ruc_dv_int,
                        pdv_nombrefactura=nombre_cliente or '',
                        pdv_nombrefantasia=nombre_cliente or '',
                        pdv_email=correo_cliente or '',
                        pdv_innominado=pdv_innominado,
                        pdv_es_contribuyente=pdv_es_contribuyente,
                        pdv_tipocontribuyente=pdv_tipocontribuyente,
                        pdv_direccion_entrega=factura.get('direccion', ''),
                        pdv_telefono=factura.get('telefono', ''),
                        pdv_celular=factura.get('celular', ''),
                        pdv_pais_cod='PRY',
                        pdv_pais='Paraguay',
                    )
                    logger.info(f"Cliente creado en Sifen: anclaje_cliente={cliente_codigo}")
            except Exception as e:
                # No fallar la factura si hay error guardando el cliente
                logger.error(f"Error guardando cliente en Sifen: {e}")

            return {
                'success': True,
                'message': 'Factura generada correctamente',
                'doc_id': doc_id,
                'doc_numero': docobj.doc_numero,
                'numero_factura': id_factura,
                'cdc': docobj.ek_cdc,
                'ek_pdf_file': ek_pdf_file,
            }

        except Exception as e:
            logger.error(f"Error generando factura SIFEN: {e}")
            import traceback
            traceback.print_exc()
            return {'error': f'Error generando factura: {str(e)}'}

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def get_cotizacion(self, *args, **kwargs) -> Dict:
        """Obtiene la cotización USD actual."""
        try:
            cotizacion = self.mysql_client.get_cotizacion_usd()
            return {'cotizacion': float(cotizacion)}
        except Exception as e:
            logger.error(f"Error obteniendo cotización: {e}")
            return {'error': f'Error obteniendo cotización: {str(e)}'}
