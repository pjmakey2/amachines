"""
Cliente MySQL para conexión directa a frontlin_db (Sistema Frontliner Legacy)

Este módulo proporciona acceso directo a la base de datos MySQL del sistema
Frontliner para las operaciones de facturación.
"""

import os
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime, date

import MySQLdb
from MySQLdb.cursors import DictCursor

logger = logging.getLogger(__name__)


class FLMySQLClient:
    """
    Cliente para conexión directa a MySQL del sistema Frontliner.

    Configuración via variables de entorno:
    - FL_MYSQL_HOST: Host del servidor MySQL (default: localhost)
    - FL_MYSQL_PORT: Puerto (default: 3306)
    - FL_MYSQL_DATABASE: Nombre de la base de datos (default: frontlin_db)
    - FL_MYSQL_USER: Usuario (default: frontlin_user)
    - FL_MYSQL_PASSWORD: Contraseña
    """

    def __init__(self):
        self.host = os.environ.get('FL_MYSQL_HOST', 'localhost')
        self.port = int(os.environ.get('FL_MYSQL_PORT', 3306))
        self.database = os.environ.get('FL_MYSQL_DATABASE', 'frontlin_db')
        self.user = os.environ.get('FL_MYSQL_USER', 'frontlin_user')
        self.password = os.environ.get('FL_MYSQL_PASSWORD', 'admin')
        self.charset = 'utf8mb4'

    @contextmanager
    def get_connection(self):
        """Context manager para obtener una conexión a MySQL."""
        conn = None
        try:
            conn = MySQLdb.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.database,
                charset=self.charset,
                cursorclass=DictCursor
            )
            yield conn
        except MySQLdb.Error as e:
            logger.error(f"Error conectando a MySQL: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Ejecuta una consulta SELECT y retorna los resultados."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()

    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Ejecuta una consulta SELECT y retorna un solo resultado."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Ejecuta una consulta UPDATE/INSERT/DELETE y retorna rows affected."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Ejecuta un INSERT y retorna el ID insertado."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid

    # =========================================================================
    # CLIENTES
    # =========================================================================

    def buscar_clientes(self, termino: str, sucursal: int = None, limit: int = 50) -> List[Dict]:
        """
        Busca clientes por nombre, apellido o código.
        Replica exactamente la lógica de ClienteBusqueda.php::buscarClienteParaEntrega()

        La búsqueda:
        1. Divide el término por espacios
        2. Cada palabra debe coincidir con LIKE AND en la etiqueta
        3. Solo clientes con estado habilitado (estado=1)

        Args:
            termino: Texto a buscar (puede ser múltiples palabras)
            sucursal: Filtrar por sucursal (opcional)
            limit: Máximo de resultados
        """
        # Construir condiciones LIKE para cada palabra (como PHP)
        palabras = [p.strip().upper() for p in termino.split() if p.strip()]

        if not palabras:
            return []

        # Construir query con subconsulta que genera etiqueta igual que PHP
        # CONCAT('', clientecodigo, '- ', clientenombre, ' ', clienteapellido) AS etiqueta
        condiciones_like = []
        params = []

        for palabra in palabras:
            condiciones_like.append("etiqueta LIKE %s")
            params.append(f'%{palabra}%')

        condicion_where = " AND ".join(condiciones_like)

        query = f"""
            SELECT codigo as clientecodigo, etiqueta,
                   clientenombre, clienteapellido, ruc, clienteci,
                   clientedireccion, clientetelefono, clientecelular, clientemail,
                   sucursal, tarifa, estante
            FROM (
                SELECT
                    clientecodigo AS codigo,
                    CONCAT('', clientecodigo, '- ', clientenombre, ' ', clienteapellido) AS etiqueta,
                    clientenombre, clienteapellido, ruc, clienteci,
                    clientedireccion, clientetelefono, clientecelular, clientemail,
                    sucursal, tarifa, estante
                FROM clientes
                WHERE estado = 1
            ) AS CLIENTE
            WHERE {condicion_where}
        """

        if sucursal:
            query += " AND sucursal = %s"
            params.append(sucursal)

        query += f" ORDER BY etiqueta LIMIT {limit}"

        return self.execute_query(query, tuple(params))

    def get_cliente(self, clientecodigo: int) -> Optional[Dict]:
        """Obtiene un cliente por su código."""
        query = """
            SELECT
                clientecodigo,
                clientenombre,
                clienteapellido,
                ruc,
                clienteci,
                clientedireccion,
                clientetelefono,
                clientecelular,
                clientemail,
                sucursal,
                tarifa,
                estante
            FROM clientes
            WHERE clientecodigo = %s
        """
        return self.execute_one(query, (clientecodigo,))

    # =========================================================================
    # SUCURSALES
    # =========================================================================

    def get_sucursal(self, sucursalcodigo: int) -> Optional[Dict]:
        """
        Obtiene datos de una sucursal por su código.
        Usada para obtener el color de fondo y nombre de la sucursal.

        Tabla: sucursal (singular)
        Columnas: sucursal (código), nombre, colorbgnd, colortxt
        """
        query = """
            SELECT
                sucursal as sucursalcodigo,
                nombre as sucursalnombre,
                colorbgnd as sucursalcolorfondo,
                colortxt as sucursalcolortexto
            FROM sucursal
            WHERE sucursal = %s
        """
        return self.execute_one(query, (sucursalcodigo,))

    # =========================================================================
    # PAQUETES
    # =========================================================================

    def get_paquetes_pendientes_cliente(self, clientecodigo: int) -> List[Dict]:
        """
        Obtiene los paquetes pendientes de entrega para un cliente.
        Según PHP: estado='B' y embarque en 'UBICANDO' o 'ASUNCION'
        """
        query = """
            SELECT
                p.paquetecodigo,
                p.paquetetracking as tracking,
                p.paquetedescripcion as descripcion,
                p.paquetepeso as peso_real,
                p.embarquecodigo,
                e.estadoembarquedescripcion,
                e.embarquefecha as fecha_embarque,
                e.fechallegada as fecha_llegada
            FROM paquetes p
            LEFT JOIN embarques e ON p.embarquecodigo = e.embarquecodigo
            WHERE p.clientecodigo = %s
            AND p.estado = 'B'
            AND (e.estadoembarquedescripcion = 'UBICANDO' OR e.estadoembarquedescripcion = 'ASUNCION')
            ORDER BY e.embarquefecha DESC
        """
        return self.execute_query(query, (clientecodigo,))

    def get_paquetes_por_acuse(self, acuse_id: int) -> List[Dict]:
        """Obtiene los paquetes asociados a un acuse."""
        query = """
            SELECT
                p.paquetecodigo,
                p.paquetetracking as tracking,
                p.paquetedescripcion as descripcion,
                p.paquetepeso as peso_real,
                fd.tarifacli as tarifa,
                COALESCE(fd.montogsdet, fd.tarifacli * p.paquetepeso * f.dolar_venta) as montogsdet,
                COALESCE(fd.montousddet, fd.tarifacli * p.paquetepeso) as montousddet
            FROM facturasdet fd
            JOIN paquetes p ON fd.paquetecodigo = p.paquetecodigo
            JOIN facturas f ON fd.acuse_id = f.acuse_id
            WHERE fd.acuse_id = %s
            ORDER BY fd.acuse_detalle_id
        """
        return self.execute_query(query, (acuse_id,))

    # =========================================================================
    # FACTURAS / ACUSES
    # =========================================================================

    def get_facturas_pendientes(self, sucursal: int = None, limit: int = 100) -> List[Dict]:
        """
        Obtiene las facturas/acuses pendientes de facturar.
        estado = 2 significa que ya se confirmó el pago
        facturaemitida = 2 significa que aún no se emitió la factura
        """
        query = """
            SELECT
                f.acuse_id,
                f.clientecodigo,
                f.fecha,
                f.estado,
                f.facturaemitida,
                f.montousd,
                f.montogs,
                f.rucusado,
                f.razonsocial,
                f.id_factura,
                f.obs,
                f.dolar_venta,
                c.clientenombre,
                c.clienteapellido,
                c.ruc,
                c.sucursal
            FROM facturas f
            LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
            WHERE f.estado = 2 AND f.facturaemitida = 2
        """
        params = []

        if sucursal:
            query += " AND c.sucursal = %s"
            params.append(sucursal)

        query += f" ORDER BY f.acuse_id DESC LIMIT {limit}"

        return self.execute_query(query, tuple(params) if params else None)

    def buscar_acuses_para_facturar(self, termino: str, limit: int = 30) -> List[Dict]:
        """
        Busca acuses PENDIENTES por número o por nombre de cliente.
        Solo retorna acuses donde:
        - estado = 1 (pendiente de pago)
        - facturaemitida = 2 (no facturado aún)

        Args:
            termino: Número de acuse o nombre de cliente
            limit: Máximo de resultados
        """
        # Si es numérico, buscar por acuse_id
        if termino.isdigit():
            query = """
                SELECT
                    f.acuse_id,
                    f.clientecodigo,
                    f.fecha,
                    f.estado,
                    f.facturaemitida,
                    f.montousd,
                    f.montogs,
                    f.id_factura,
                    c.clientenombre,
                    c.clienteapellido,
                    c.ruc
                FROM facturas f
                LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
                WHERE (f.acuse_id = %s OR CAST(f.acuse_id AS CHAR) LIKE %s)
                AND f.estado = 1
                AND f.facturaemitida = 2
                ORDER BY f.acuse_id DESC
                LIMIT %s
            """
            return self.execute_query(query, (int(termino), f'{termino}%', limit))
        else:
            # Buscar por nombre de cliente (igual que clientes)
            palabras = [p.strip().upper() for p in termino.split() if p.strip()]
            if not palabras:
                return []

            condiciones_like = []
            params = []

            for palabra in palabras:
                condiciones_like.append("CONCAT(c.clientenombre, ' ', c.clienteapellido) LIKE %s")
                params.append(f'%{palabra}%')

            condicion_where = " AND ".join(condiciones_like)

            query = f"""
                SELECT
                    f.acuse_id,
                    f.clientecodigo,
                    f.fecha,
                    f.estado,
                    f.facturaemitida,
                    f.montousd,
                    f.montogs,
                    f.id_factura,
                    c.clientenombre,
                    c.clienteapellido,
                    c.ruc
                FROM facturas f
                LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
                WHERE {condicion_where}
                AND f.estado = 1
                AND f.facturaemitida = 2
                ORDER BY f.acuse_id DESC
                LIMIT {limit}
            """
            return self.execute_query(query, tuple(params))

    def get_todas_facturas(self, sucursal: int = None, limit: int = 100,
                           offset: int = 0, filtros: Dict = None) -> List[Dict]:
        """
        Obtiene todas las facturas con filtros opcionales.
        """
        query = """
            SELECT
                f.acuse_id,
                f.clientecodigo,
                f.fecha,
                f.estado,
                f.facturaemitida,
                f.montousd,
                f.montogs,
                f.montoefegs,
                f.montoefeusd,
                f.montotcgs,
                f.montotcusd,
                f.montotdgs,
                f.montotdusd,
                f.montochkgs,
                f.montochkusd,
                f.montopendiente,
                f.rucusado,
                f.razonsocial,
                f.id_factura,
                f.obs,
                f.dolar_venta,
                c.clientenombre,
                c.clienteapellido,
                c.ruc,
                c.sucursal
            FROM facturas f
            LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
            WHERE 1=1
        """
        params = []

        if sucursal:
            query += " AND c.sucursal = %s"
            params.append(sucursal)

        if filtros:
            if filtros.get('acuse_id'):
                query += " AND f.acuse_id = %s"
                params.append(filtros['acuse_id'])
            if filtros.get('clientecodigo'):
                query += " AND f.clientecodigo = %s"
                params.append(filtros['clientecodigo'])
            if filtros.get('clientenombre'):
                query += " AND c.clientenombre LIKE %s"
                params.append(f"%{filtros['clientenombre']}%")
            if filtros.get('facturaemitida'):
                query += " AND f.facturaemitida = %s"
                params.append(filtros['facturaemitida'])
            if filtros.get('fecha_desde'):
                query += " AND f.fecha >= %s"
                params.append(filtros['fecha_desde'])
            if filtros.get('fecha_hasta'):
                query += " AND f.fecha <= %s"
                params.append(filtros['fecha_hasta'])

        query += f" ORDER BY f.acuse_id DESC LIMIT {limit} OFFSET {offset}"

        return self.execute_query(query, tuple(params) if params else None)

    def get_factura(self, acuse_id: int) -> Optional[Dict]:
        """Obtiene una factura/acuse por su ID."""
        query = """
            SELECT
                f.acuse_id,
                f.clientecodigo,
                f.fecha,
                f.estado,
                f.facturaemitida,
                f.montousd,
                f.montogs,
                f.montoefegs,
                f.montoefeusd,
                f.montotcgs,
                f.montotcusd,
                f.montotdgs,
                f.montotdusd,
                f.montochkgs,
                f.montochkusd,
                f.montopendiente,
                f.descuento,
                f.rucusado,
                f.razonsocial,
                f.id_factura,
                f.obs,
                f.dolar_venta,
                f.peso_real,
                f.tarifa,
                f.otroconcepto,
                f.montogsexenta,
                f.montogsgravada,
                f.montoivags,
                c.clientenombre,
                c.clienteapellido,
                c.ruc,
                c.clienteci,
                c.clientedireccion,
                c.clientetelefono,
                c.clientecelular,
                c.clientemail,
                c.sucursal,
                c.tarifa as cliente_tarifa,
                c.estante
            FROM facturas f
            LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
            WHERE f.acuse_id = %s
        """
        return self.execute_one(query, (acuse_id,))

    def count_facturas(self, sucursal: int = None, filtros: Dict = None) -> int:
        """Cuenta el total de facturas con los filtros aplicados."""
        query = """
            SELECT COUNT(*) as total
            FROM facturas f
            LEFT JOIN clientes c ON f.clientecodigo = c.clientecodigo
            WHERE 1=1
        """
        params = []

        if sucursal:
            query += " AND c.sucursal = %s"
            params.append(sucursal)

        if filtros:
            if filtros.get('acuse_id'):
                query += " AND f.acuse_id = %s"
                params.append(filtros['acuse_id'])
            if filtros.get('clientecodigo'):
                query += " AND f.clientecodigo = %s"
                params.append(filtros['clientecodigo'])
            if filtros.get('facturaemitida'):
                query += " AND f.facturaemitida = %s"
                params.append(filtros['facturaemitida'])

        result = self.execute_one(query, tuple(params) if params else None)
        return result['total'] if result else 0

    # =========================================================================
    # GENERAR TICKET (ACUSE)
    # =========================================================================

    def generar_ticket(self, clientecodigo: int, paquetes_codigos: List[int],
                       tarifa: float, tasa_usd: float, peso_total: float,
                       funcionario_codigo: int) -> int:
        """
        Genera un ticket/acuse de entrega.
        Replica exactamente la lógica de Ticket.php::guardar()

        1. Si existe acuse con estado=1 para este cliente → elimina y reutiliza acuse_id
        2. Sino → obtiene nuevo acuse_id (MAX + 1)
        3. Crea registro en facturas (estado=1, facturaemitida=2)
        4. Crea registros en facturasdet desde paquetes
        5. NO actualiza estado de paquetes (se hace al confirmar pago)

        Returns:
            acuse_id generado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Obtener datos del cliente
                cursor.execute(
                    "SELECT ruc FROM clientes WHERE clientecodigo = %s",
                    (clientecodigo,)
                )
                cliente = cursor.fetchone()
                ruc = cliente['ruc'] if cliente and cliente['ruc'] else ''

                # Verificar si existe acuse pendiente (estado=1) para este cliente
                cursor.execute(
                    "SELECT acuse_id FROM facturas WHERE clientecodigo = %s AND estado = 1",
                    (clientecodigo,)
                )
                existing = cursor.fetchone()

                if existing:
                    # Eliminar acuse existente y reutilizar ID
                    acuse_id = existing['acuse_id']
                    cursor.execute("DELETE FROM facturasdet WHERE acuse_id = %s", (acuse_id,))
                    cursor.execute("DELETE FROM facturas WHERE acuse_id = %s", (acuse_id,))
                else:
                    # Obtener siguiente acuse_id
                    cursor.execute("SELECT MAX(acuse_id) as max_id FROM facturas")
                    result = cursor.fetchone()
                    acuse_id = (result['max_id'] or 0) + 1

                # Calcular montos con redondeo según PHP
                monto_usd = float(peso_total) * float(tarifa)
                monto_gs_raw = monto_usd * float(tasa_usd)
                # Redondear a miles (round(x/1000)*1000)
                monto_gs = round(monto_gs_raw / 1000) * 1000
                monto_usd_rounded = round(monto_usd)
                redondeo = monto_gs - monto_gs_raw

                fecha = datetime.now().strftime('%Y-%m-%d')

                # Insertar en facturas (igual que Ticket.php)
                cursor.execute("""
                    INSERT INTO facturas (
                        acuse_id, clientecodigo, tarifa, dolar_venta, fecha, ruc,
                        estado, peso_real, arqueo, facturaemitida, obs,
                        funcionariocodigo, montousd, montogs, redondeo_guaranies
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        1, %s, 2, 2, 'Servicio de traslado de paquetes',
                        %s, %s, %s, %s
                    )
                """, (
                    acuse_id, clientecodigo, tarifa, tasa_usd, fecha, ruc,
                    peso_total, funcionario_codigo, monto_usd_rounded, monto_gs, redondeo
                ))

                # Insertar detalles desde paquetes (como hace Ticket.php con SELECT INSERT)
                placeholders = ','.join(['%s'] * len(paquetes_codigos))
                cursor.execute(f"""
                    INSERT INTO facturasdet (
                        acuse_id, acuse_detalle_id, peso, descripcion, tarifacli,
                        anualidad, paquetetracking, paquetecodigo
                    )
                    SELECT
                        %s AS acuse_id,
                        paquetecodigo AS acuse_detalle_id,
                        paquetepeso,
                        paquetedescripcion,
                        %s AS tarifacli,
                        2 AS anualidad,
                        paquetetracking,
                        paquetecodigo
                    FROM paquetes
                    WHERE paquetecodigo IN ({placeholders})
                """, (acuse_id, tarifa, *paquetes_codigos))

                # Registrar en bitácora (usando código V_104 como en PHP Constante::TICKET_GENERAR)
                cursor.execute("""
                    INSERT INTO bitacora (funcionariocodigo, codopcion, fecha, hora, accion, nroip)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    funcionario_codigo, 'V_104', fecha,
                    datetime.now().strftime('%H:%M:%S'),
                    f'Ticket: {acuse_id}; Tarifa: {tarifa}; Monto(USD): {monto_usd_rounded}; Cotizacion: {tasa_usd}; Peso Total: {peso_total}',
                    '127.0.0.1'
                ))

                conn.commit()
                logger.info(f"Ticket generado: acuse_id={acuse_id}")
                return acuse_id

            except Exception as e:
                conn.rollback()
                logger.error(f"Error generando ticket: {e}")
                raise

    # =========================================================================
    # CONFIRMAR PAGO
    # =========================================================================

    def confirmar_pago(self, acuse_id: int, pagos: Dict,
                       ruc_factura: str, nombre_factura: str,
                       observaciones: str, funcionario_codigo: int) -> bool:
        """
        Confirma el pago de un acuse.
        Replica la lógica de facturar.php::ValidarFormulario()

        1. Actualiza paquetes: estado='C', acuse_id, fecharetiro, usuario_entrega
        2. Actualiza facturas: estado=2, pagos, datos factura
        3. Si hay pendiente > 0: inserta en ctacte

        Args:
            acuse_id: ID del acuse
            pagos: Dict con montos de pago
            ruc_factura: RUC para la factura
            nombre_factura: Nombre/Razón social para la factura
            observaciones: Observaciones
            funcionario_codigo: Código del funcionario

        Returns:
            True si se confirmó correctamente
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Obtener factura actual
                cursor.execute(
                    "SELECT * FROM facturas WHERE acuse_id = %s",
                    (acuse_id,)
                )
                factura = cursor.fetchone()

                if not factura:
                    raise ValueError(f"Acuse {acuse_id} no encontrado")

                clientecodigo = factura['clientecodigo']
                tasa = float(factura['dolar_venta'] or 1)
                monto_total_gs = float(factura['montogs'] or 0)
                peso_real = float(factura['peso_real'] or 0)
                tarifa = float(factura['tarifa'] or 0)

                # Obtener pagos
                efectivo_gs = float(pagos.get('efectivo_gs', 0))
                efectivo_usd = float(pagos.get('efectivo_usd', 0))
                tc_gs = float(pagos.get('tc_gs', 0))
                tc_usd = float(pagos.get('tc_usd', 0))
                td_gs = float(pagos.get('td_gs', 0))
                td_usd = float(pagos.get('td_usd', 0))
                cheque_gs = float(pagos.get('cheque_gs', 0))
                cheque_usd = float(pagos.get('cheque_usd', 0))
                descuento = float(pagos.get('descuento', 0))

                # Total pagado en Gs (como en PHP)
                suma = (
                    (efectivo_usd * tasa) + efectivo_gs +
                    (tc_usd * tasa) + tc_gs +
                    (td_usd * tasa) + td_gs +
                    (cheque_usd * tasa) + cheque_gs +
                    descuento
                )

                pendiente = int(max(0, monto_total_gs - suma))

                # Calcular IVA (según PHP)
                tarifa_parte_exenta = 10  # USD por kg exento
                usd_exenta = tarifa_parte_exenta * peso_real
                usd_gravada = (tarifa - tarifa_parte_exenta) * peso_real
                monto_exenta = usd_exenta * tasa
                monto_gravada = usd_gravada * tasa
                iva_gravada = monto_gravada / 11

                fecha_acuse = datetime.now().strftime('%Y-%m-%d')

                # 1. Actualizar PAQUETES
                cursor.execute("SELECT paquetecodigo FROM facturasdet WHERE acuse_id = %s", (acuse_id,))
                detalles = cursor.fetchall()
                for det in detalles:
                    if det['paquetecodigo']:
                        cursor.execute("""
                            UPDATE paquetes SET
                                estado = 'C',
                                acuse_id = %s,
                                fecharetiro = %s,
                                usuario_entrega = %s
                            WHERE paquetecodigo = %s
                        """, (acuse_id, fecha_acuse, funcionario_codigo, det['paquetecodigo']))

                # 2. Actualizar FACTURAS
                obs = observaciones.strip() if observaciones else 'Servicio de traslado de paquetes'
                monto_usd = peso_real * tarifa

                cursor.execute("""
                    UPDATE facturas SET
                        estado = 2,
                        obs = %s,
                        otroconcepto = 2,
                        montousd = %s,
                        montogs = %s,
                        montotcgs = %s,
                        montotcusd = %s,
                        montoefegs = %s,
                        montoefeusd = %s,
                        montotdgs = %s,
                        montotdusd = %s,
                        montochkgs = %s,
                        montochkusd = %s,
                        montopendiente = %s,
                        descuento = %s,
                        montogsexenta = %s,
                        montogsgravada = %s,
                        montoivags = %s,
                        rucusado = %s,
                        razonsocial = %s,
                        funcionariocodigo = %s
                    WHERE acuse_id = %s
                """, (
                    obs, monto_usd, monto_total_gs,
                    tc_gs, tc_usd, efectivo_gs, efectivo_usd,
                    td_gs, td_usd, cheque_gs, cheque_usd,
                    pendiente, descuento,
                    monto_exenta, monto_gravada, iva_gravada,
                    ruc_factura, nombre_factura,
                    funcionario_codigo, acuse_id
                ))

                # 3. Actualizar FACTURASDET
                cursor.execute("""
                    UPDATE facturasdet SET otroconcepto = 2 WHERE acuse_id = %s
                """, (acuse_id,))

                # 4. Eliminar entrada anterior en CTACTE para este acuse
                cursor.execute("DELETE FROM ctacte WHERE acuse_id = %s", (acuse_id,))

                # 5. Si hay pendiente, insertar en CTACTE
                if pendiente > 0:
                    cursor.execute("""
                        SELECT COALESCE(MAX(norden), 0) + 1 as nuevo_norden
                        FROM ctacte WHERE clientecodigo = %s
                    """, (clientecodigo,))
                    result = cursor.fetchone()
                    norden = result['nuevo_norden']

                    saldo_iva = iva_gravada * (pendiente / monto_total_gs) if monto_total_gs > 0 else 0
                    pendiente_usd = pendiente / tasa

                    cursor.execute("""
                        INSERT INTO ctacte (
                            clientecodigo, norden, acuse_id, fecha,
                            montousd, montogs, ivadeuda, saldoiva, saldo, tasa,
                            montogravadototalgs, montoexentatotalgs, paquete
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'SI')
                    """, (
                        clientecodigo, norden, acuse_id, fecha_acuse,
                        pendiente_usd, pendiente, saldo_iva, saldo_iva, pendiente, tasa,
                        monto_gravada, monto_exenta
                    ))

                conn.commit()
                logger.info(f"Pago confirmado para acuse_id={acuse_id}, pendiente={pendiente}")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Error confirmando pago: {e}")
                raise

    # =========================================================================
    # ACTUALIZAR FACTURA EMITIDA (después de SIFEN)
    # =========================================================================

    def marcar_factura_emitida(self, acuse_id: int, id_factura: str,
                                funcionario_codigo: int) -> bool:
        """
        Marca una factura como emitida después de generar en SIFEN.

        Args:
            acuse_id: ID del acuse
            id_factura: CDC o número de factura SIFEN
            funcionario_codigo: Código del funcionario

        Returns:
            True si se actualizó correctamente
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Actualizar factura
                cursor.execute("""
                    UPDATE facturas SET
                        facturaemitida = 1,
                        id_factura = %s,
                        funcionariocodigo = %s
                    WHERE acuse_id = %s
                """, (id_factura, funcionario_codigo, acuse_id))

                # Actualizar detalles
                cursor.execute("""
                    UPDATE facturasdet SET
                        id_factura = %s
                    WHERE acuse_id = %s
                """, (id_factura, acuse_id))

                # Actualizar estado de paquetes a 'C' (Completado/Entregado)
                cursor.execute("""
                    UPDATE paquetes SET
                        estado = 'C'
                    WHERE acuse_id = %s
                """, (acuse_id,))

                conn.commit()
                logger.info(f"Factura marcada como emitida: acuse_id={acuse_id}, id_factura={id_factura}")
                return True

            except Exception as e:
                conn.rollback()
                logger.error(f"Error marcando factura emitida: {e}")
                raise

    # =========================================================================
    # CUENTA CORRIENTE
    # =========================================================================

    def get_deuda_cliente(self, clientecodigo: int) -> Decimal:
        """Obtiene la deuda total de un cliente."""
        query = """
            SELECT COALESCE(SUM(saldo), 0) as deuda
            FROM ctacte
            WHERE clientecodigo = %s AND saldo > 0
        """
        result = self.execute_one(query, (clientecodigo,))
        return Decimal(str(result['deuda'])) if result else Decimal('0')

    # =========================================================================
    # COTIZACIÓN USD
    # =========================================================================

    def get_cotizacion_usd(self) -> Decimal:
        """
        Obtiene la cotización USD actual de conf_gral.monto
        Igual que en PHP: SELECT * FROM conf_gral → $row['monto']
        """
        try:
            query = "SELECT monto FROM conf_gral LIMIT 1"
            result = self.execute_one(query)
            if result and result.get('monto'):
                return Decimal(str(result['monto']))
        except Exception as e:
            logger.warning(f"Error obteniendo cotización: {e}")

        # Valor por defecto
        return Decimal('7500')
