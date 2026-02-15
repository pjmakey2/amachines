"""
Plugin SIFEN para Amachine ERP

Este plugin proporciona:
- Facturación Electrónica SIFEN (Paraguay)
- Datos de referencia: Geografías, Actividades Económicas, Medidas, etc.
- Menús de facturación
- Tareas Celery para envío de documentos
"""

from typing import List, Dict, Tuple
from datetime import datetime
import pandas as pd
import logging

from django.conf import settings

from OptsIO.plugin_manager import BasePlugin

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """Plugin de Facturación Electrónica SIFEN."""

    name = "sifen"
    display_name = "SIFEN - Facturación Electrónica"
    description = "Sistema Integrado de Facturación Electrónica Nacional (Paraguay)"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = True  # Plugin core, siempre activo
    dependencies = []
    icon = "mdi mdi-file-document-outline"
    category = "facturacion"

    def get_reference_data(self) -> List[Dict]:
        """Define los datos de referencia que carga este plugin."""
        return [
            {
                'name': 'tipo_contribuyente',
                'display_name': 'Tipos de Contribuyente',
                'description': 'Física, Jurídica',
                'loader': 'load_tipo_contribuyente',
                'source_file': '',
                'required': True,
                'order': 1,
            },
            {
                'name': 'geografias',
                'display_name': 'Geografías',
                'description': 'Departamentos, Distritos, Ciudades, Barrios de Paraguay',
                'loader': 'load_geografias',
                'source_file': 'Sifen/rf/CODIGO DE REFERENCIA GEOGRAFICA.xlsx',
                'required': True,
                'order': 2,
            },
            {
                'name': 'actividades',
                'display_name': 'Actividades Económicas',
                'description': 'Códigos de actividades económicas SIFEN',
                'loader': 'load_actividades',
                'source_file': 'Sifen/rf/actividades_economicas_utf8.csv',
                'required': True,
                'order': 3,
            },
            {
                'name': 'medidas',
                'display_name': 'Unidades de Medida',
                'description': 'Unidades de medida para productos (kg, m, lt, etc.)',
                'loader': 'load_medidas',
                'source_file': '',
                'required': True,
                'order': 4,
            },
            {
                'name': 'porcentaje_iva',
                'display_name': 'Porcentajes de IVA',
                'description': 'Tasas de IVA (10%, 5%, Exento)',
                'loader': 'load_porcentaje_iva',
                'source_file': '',
                'required': True,
                'order': 5,
            },
            {
                'name': 'metodos_pago',
                'display_name': 'Métodos de Pago',
                'description': 'Efectivo, Tarjeta, Transferencia, etc.',
                'loader': 'load_metodos_pago',
                'source_file': '',
                'required': True,
                'order': 6,
            },
        ]

    def get_celery_tasks(self) -> List[str]:
        """Tareas Celery del plugin."""
        return [
            'Sifen.tasks.send_document_to_sifen',
            'Sifen.tasks.track_lotes',
            'Sifen.tasks.send_email_notifications',
            'Sifen.tasks.sync_rucs',
        ]

    def get_setup_steps(self) -> List[Dict]:
        """Pasos de setup específicos de SIFEN."""
        return [
            {
                'name': 'load_reference_data',
                'display_name': 'Cargar Datos de Referencia',
                'description': 'Carga geografías, actividades económicas, medidas, etc.',
                'order': 10,
                'handler': 'setup_load_reference_data',
                'required': True,
            },
            {
                'name': 'configure_business',
                'display_name': 'Configurar Empresa',
                'description': 'Configurar datos de la empresa para facturación',
                'order': 20,
                'handler': 'setup_configure_business',
                'required': True,
            },
        ]

    def load_reference_data(self, data_name: str, progress_callback=None) -> Tuple[bool, str, Dict]:
        """
        Carga datos de referencia específicos.

        Args:
            data_name: Nombre del conjunto de datos
            progress_callback: Función para reportar progreso (percent, message)

        Returns:
            Tuple de (success, message, stats)
        """
        loaders = {
            'tipo_contribuyente': self._load_tipo_contribuyente,
            'geografias': self._load_geografias,
            'actividades': self._load_actividades,
            'medidas': self._load_medidas,
            'porcentaje_iva': self._load_porcentaje_iva,
            'metodos_pago': self._load_metodos_pago,
        }

        loader = loaders.get(data_name)
        if not loader:
            return False, f"Loader no encontrado para {data_name}", {}

        try:
            return loader(progress_callback)
        except Exception as e:
            logger.exception(f"Error cargando {data_name}")
            return False, str(e), {}

    def _load_tipo_contribuyente(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga tipos de contribuyente."""
        from Sifen.models import TipoContribuyente

        if progress_callback:
            progress_callback(10, "Creando tipos de contribuyente...")

        tipos = [
            (1, 'Fisica'),
            (2, 'Juridica'),
        ]

        created = 0
        for codigo, tipo in tipos:
            obj, was_created = TipoContribuyente.objects.get_or_create(
                codigo=codigo,
                tipo=tipo
            )
            if was_created:
                created += 1

        if progress_callback:
            progress_callback(100, "Tipos de contribuyente cargados")

        return True, f"Tipos de contribuyente cargados ({created} creados)", {
            'loaded': created,
            'updated': 0,
            'skipped': len(tipos) - created,
        }

    def _load_geografias(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga datos geográficos desde Excel."""
        from Sifen.models import (
            Geografias, AreasPoliticas, Paises, Departamentos,
            Distrito, Ciudades, Barrios
        )

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(5, "Creando estructura geográfica base...")

        # Crear estructura base
        gobj, _ = Geografias.objects.get_or_create(
            continente='America',
            descripcion='America',
            comentarios=''
        )

        areobj, _ = AreasPoliticas.objects.get_or_create(
            geografia=gobj,
            area_politica='SUDAMERICA',
            descripcion='',
            comentarios='',
        )

        paisobj, _ = Paises.objects.get_or_create(
            nombre_pais='PARAGUAY',
            codigo_pais=600,
            alfa_uno='PY',
            alfa_dos='PRY',
            areapolitica=areobj,
            adjetivo='PARAGUAYO',
            nacionalidad='PARAGUAYA',
            habitante='PARAGUAYOS',
            descripcion='ND',
            comentarios='ND'
        )

        if progress_callback:
            progress_callback(10, "Leyendo archivo Excel de geografías...")

        # Cargar desde Excel
        file_path = f'{settings.BASE_DIR}/Sifen/rf/CODIGO DE REFERENCIA GEOGRAFICA.xlsx'
        try:
            dfg = pd.read_excel(file_path, dtype=str)
            dfg.fillna('', inplace=True)
        except Exception as e:
            return False, f"Error leyendo archivo Excel: {e}", stats

        total_rows = len(dfg)
        fuente = 'SET'

        if progress_callback:
            progress_callback(15, f"Procesando {total_rows} registros...")

        for idx, data in dfg.iterrows():
            # Reportar progreso cada 100 registros
            if progress_callback and idx % 100 == 0:
                percent = 15 + int((idx / total_rows) * 80)
                progress_callback(percent, f"Procesando registro {idx + 1} de {total_rows}...")

            # Departamento
            dobj, created = Departamentos.objects.get_or_create(
                fuente=fuente,
                pais=paisobj,
                codigo_departamento=data.DEP_COD,
                defaults={
                    'nombre_departamento': data.DEP,
                    'habitante': 'ND',
                    'descripcion': 'ND',
                    'comentarios': 'ND'
                }
            )
            if created:
                stats['loaded'] += 1

            # Distrito
            disobj, created = Distrito.objects.get_or_create(
                dptoobj=dobj,
                fuente=fuente,
                codigo_distrito=data.DIS_COD,
                defaults={
                    'nombre_distrito': data.DIS,
                    'habitante': 'ND',
                    'descripcion': 'ND',
                    'comentarios': 'ND'
                }
            )
            if created:
                stats['loaded'] += 1

            # Ciudad
            if str(data.CIU_COD).strip() != '':
                ciuobj, created = Ciudades.objects.get_or_create(
                    distritoobj=disobj,
                    fuente=fuente,
                    codigo_ciudad=data.CIU_COD,
                    defaults={
                        'nombre_ciudad': data.CIU,
                        'habitante': 'ND',
                        'descripcion': 'ND',
                        'comentarios': 'ND'
                    }
                )
                if created:
                    stats['loaded'] += 1

                # Barrio
                if str(data.BAR_COD).strip() != '':
                    barobj, created = Barrios.objects.get_or_create(
                        ciudad=ciuobj,
                        fuente=fuente,
                        codigo_barrio=data.BAR_COD,
                        defaults={
                            'nombre_barrio': data.BAR,
                            'habitante': 'ND',
                            'descripcion': 'ND',
                            'comentarios': 'ND'
                        }
                    )
                    if created:
                        stats['loaded'] += 1

        if progress_callback:
            progress_callback(100, "Geografías cargadas exitosamente")

        return True, f"Geografías cargadas ({stats['loaded']} registros)", stats

    def _load_actividades(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga actividades económicas desde CSV."""
        from Sifen.models import ActividadEconomica

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(10, "Leyendo archivo CSV de actividades...")

        file_path = f'{settings.BASE_DIR}/Sifen/rf/actividades_economicas_utf8.csv'
        try:
            df = pd.read_csv(file_path, sep=',', encoding='utf-8', quotechar='"')
        except Exception as e:
            return False, f"Error leyendo archivo CSV: {e}", stats

        total_rows = len(df)

        if progress_callback:
            progress_callback(20, f"Procesando {total_rows} actividades...")

        for idx, data in df.iterrows():
            if progress_callback and idx % 100 == 0:
                percent = 20 + int((idx / total_rows) * 75)
                progress_callback(percent, f"Procesando actividad {idx + 1} de {total_rows}...")

            aobj, created = ActividadEconomica.objects.get_or_create(
                codigo_actividad=data.codigo,
                defaults={
                    'nombre_actividad': data.descripcion,
                    'cargado_fecha': datetime.now(),
                    'cargado_usuario': 'SETUP'
                }
            )

            if created:
                stats['loaded'] += 1
            else:
                stats['skipped'] += 1

        if progress_callback:
            progress_callback(100, "Actividades económicas cargadas")

        return True, f"Actividades económicas cargadas ({stats['loaded']} nuevas)", stats

    def _load_medidas(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga unidades de medida."""
        from Sifen.models import Medida

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(10, "Cargando unidades de medida...")

        medidas = [
            (87, 'm', 'Metros'),
            (2366, 'CPM', 'Costo por Mil'),
            (2329, 'UI', 'Unidad Internacional'),
            (110, 'M3', 'Metros cúbicos'),
            (77, 'UNI', 'Unidad'),
            (86, 'g', 'Gramos'),
            (89, 'LT', 'Litros'),
            (90, 'MG', 'Miligramos'),
            (91, 'CM', 'Centimetros'),
            (92, 'CM2', 'Centimetros cuadrados'),
            (93, 'CM3', 'Centimetros cubicos'),
            (94, 'PUL', 'Pulgadas'),
            (96, 'MM2', 'Milímetros cuadrados'),
            (79, 'kg/m²', 'Kilogramos s/ metrocuadrado'),
            (97, 'AA', 'Año'),
            (98, 'ME', 'Mes'),
            (99, 'TN', 'Tonelada'),
            (100, 'Hs', 'Hora'),
            (101, 'Mi', 'Minuto'),
            (104, 'DET', 'Determinación'),
            (103, 'Ya', 'Yardas'),
            (108, 'MT', 'Metros'),
            (109, 'M2', 'Metros cuadrados'),
            (95, 'MM', 'Milímetros'),
            (666, 'Se', 'Segundo'),
            (102, 'Di', 'Día'),
            (83, 'kg', 'Kilogramos'),
            (88, 'ML', 'Mililitros'),
            (625, 'Km', 'Kilómetros'),
            (660, 'ml', 'Metro lineal'),
            (885, 'GL', 'Unidad Medida Global'),
            (891, 'pm', 'Por Milaje'),
            (869, 'ha', 'Hectáreas'),
            (569, 'ración', 'Ración'),
        ]

        for idx, (cod, med, desc) in enumerate(medidas):
            if progress_callback:
                percent = 10 + int((idx / len(medidas)) * 85)
                progress_callback(percent, f"Cargando medida {med}...")

            obj, created = Medida.objects.get_or_create(
                medida_cod=cod,
                medida=med,
                medida_descripcion=desc
            )
            if created:
                obj.cargado_usuario = 'SETUP'
                obj.cargado_fecha = datetime.now()
                obj.save()
                stats['loaded'] += 1
            else:
                stats['skipped'] += 1

        if progress_callback:
            progress_callback(100, "Unidades de medida cargadas")

        return True, f"Unidades de medida cargadas ({stats['loaded']} nuevas)", stats

    def _load_porcentaje_iva(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga porcentajes de IVA."""
        from Sifen.models import PorcentajeIva

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(20, "Cargando porcentajes de IVA...")

        # Porcentajes IVA según SIFEN Paraguay
        porcentajes = [
            (10, 'IVA 10%'),
            (5, 'IVA 5%'),
            (0, 'Exento'),
        ]

        for idx, (porcentaje, descripcion) in enumerate(porcentajes):
            if progress_callback:
                percent = 20 + int((idx / len(porcentajes)) * 70)
                progress_callback(percent, f"Cargando {descripcion}...")

            obj, created = PorcentajeIva.objects.get_or_create(
                porcentaje=porcentaje,
                defaults={
                    'descripcion': descripcion,
                    'activo': True,
                }
            )
            if created:
                stats['loaded'] += 1
            else:
                stats['skipped'] += 1

        if progress_callback:
            progress_callback(100, "Porcentajes IVA cargados")

        return True, f"Porcentajes IVA cargados ({stats['loaded']} nuevos)", stats

    def _load_metodos_pago(self, progress_callback=None) -> Tuple[bool, str, Dict]:
        """Carga métodos de pago."""
        from Sifen.models import MetodosPago

        stats = {'loaded': 0, 'updated': 0, 'skipped': 0}

        if progress_callback:
            progress_callback(20, "Cargando métodos de pago...")

        # Métodos de pago según SIFEN
        metodos = [
            ('Efectivo', 'Pago en efectivo'),
            ('Cheque', 'Pago con cheque'),
            ('Tarjeta de Crédito', 'Pago con tarjeta de crédito'),
            ('Tarjeta de Débito', 'Pago con tarjeta de débito'),
            ('Transferencia', 'Transferencia bancaria'),
            ('Giro', 'Giro bancario'),
            ('Billetera Electrónica', 'Billetera electrónica'),
            ('Tarjeta Empresarial', 'Tarjeta empresarial'),
            ('Vale', 'Vale o cupón'),
            ('Retención', 'Retención'),
            ('Pago Móvil', 'Pago móvil'),
            ('Otro', 'Otro método de pago'),
        ]

        for idx, (nombre, descripcion) in enumerate(metodos):
            if progress_callback:
                percent = 20 + int((idx / len(metodos)) * 70)
                progress_callback(percent, f"Cargando {nombre}...")

            obj, created = MetodosPago.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'activo': True,
                }
            )
            if created:
                stats['loaded'] += 1
            else:
                stats['skipped'] += 1

        if progress_callback:
            progress_callback(100, "Métodos de pago cargados")

        return True, f"Métodos de pago cargados ({stats['loaded']} nuevos)", stats
