import json
import logging
from django.utils import timezone
from Sifen.models import Etimbrado
from OptsIO.io_json import from_json

logger = logging.getLogger(__name__)


class MEtimbrado:
    """
    Clase para operaciones CRUD de timbrados desde la UI.
    """

    def save_etimbrado(self, *args, **kwargs) -> tuple:
        """
        Guarda o actualiza un registro de Etimbrado.
        Llamado desde process_record via c_a.
        """
        q = kwargs.get('qdict', {})
        uc_fields = from_json(q.get('uc_fields', {}))
        userobj = kwargs.get('userobj')
        username = userobj.username if userobj else 'system'

        try:
            pk = uc_fields.get('id')

            if pk:
                # Actualizar existente
                try:
                    etimbrado = Etimbrado.objects.get(pk=pk)
                except Etimbrado.DoesNotExist:
                    return {'error': f'Timbrado con ID {pk} no encontrado'}, args, kwargs

                etimbrado.actualizado_fecha = timezone.now()
                etimbrado.actualizado_usuario = username
            else:
                # Crear nuevo
                etimbrado = Etimbrado()
                etimbrado.cargado_fecha = timezone.now()
                etimbrado.cargado_usuario = username

            # Asignar campos
            etimbrado.ruc = uc_fields.get('ruc', '')
            etimbrado.dv = uc_fields.get('dv', '')
            etimbrado.timbrado = uc_fields.get('timbrado', '')
            etimbrado.serie = uc_fields.get('serie', '')
            etimbrado.fcsc = uc_fields.get('fcsc', '')
            etimbrado.scsc = uc_fields.get('scsc', '')

            # Fechas
            inicio = uc_fields.get('inicio')
            if inicio:
                etimbrado.inicio = inicio

            vencimiento = uc_fields.get('vencimiento')
            if vencimiento:
                etimbrado.vencimiento = vencimiento

            etimbrado.save()

            action = 'actualizado' if pk else 'creado'
            return {'success': f'Timbrado {action} correctamente'}, args, kwargs

        except Exception as e:
            logger.exception("Error guardando timbrado")
            return {'error': f'Error al guardar timbrado: {str(e)}'}, args, kwargs

    def delete_etimbrado(self, *args, **kwargs) -> tuple:
        """
        Elimina uno o mas registros de Etimbrado.
        """
        q = kwargs.get('qdict', {})
        ids_str = q.get('ids', '[]')

        try:
            ids = json.loads(ids_str)
        except json.JSONDecodeError:
            return {'error': 'IDs invalidos'}, args, kwargs

        if not ids:
            return {'error': 'No se proporcionaron IDs para eliminar'}, args, kwargs

        try:
            deleted_count = Etimbrado.objects.filter(pk__in=ids).delete()[0]
            return {'success': f'{deleted_count} timbrado(s) eliminado(s) correctamente'}, args, kwargs

        except Exception as e:
            logger.exception("Error eliminando timbrados")
            return {'error': f'Error al eliminar timbrados: {str(e)}'}, args, kwargs
