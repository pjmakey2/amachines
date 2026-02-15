import logging
from datetime import datetime
from OptsIO.io_serial import IoS
from OptsIO.io_json import to_json, from_json
from OptsIO.ws_utils import ws_send_notification
from Sifen import ekuatia_serials
from Sifen.models import Etimbrado, Eestablecimiento, Enumbers

class SEserial:
    """Serial management for Sifen electronic invoicing numbers"""

    def create_timbrado_ui(self, *args, **kwargs) -> dict:
        """
        Create timbrado and generate number ranges from UI
        This is a wrapper that dispatches to a Celery task for long-running process
        """
        from celery.execute import send_task

        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})

        # Dispatch to Celery task
        task = send_task('Sifen.tasks.create_timbrado_task',
            kwargs={
                'username': userobj.username,
                'qdict': q
            }
        )

        return {
            'success': 'Tarea de creación de timbrado iniciada',
            'task_id': task.id,
            'info': 'Recibirás notificaciones del progreso'
        }

    def get_timbrados(self, *args, **kwargs) -> dict:
        """Get list of timbrados for select"""
        timbrados = Etimbrado.objects.all().values('id', 'timbrado', 'ruc', 'inicio', 'vencimiento')
        return {
            'success': True,
            'timbrados': list(timbrados)
        }

    def get_establecimientos_by_timbrado(self, *args, **kwargs) -> dict:
        """Get establecimientos filtered by timbrado"""
        q: dict = kwargs.get('qdict', {})
        timbrado_id = q.get('timbrado_id')

        if not timbrado_id:
            return {'error': 'Falta el ID del timbrado'}

        establecimientos = Eestablecimiento.objects.filter(
            timbradoobj_id=timbrado_id
        ).values('id', 'establecimiento', 'direccion')

        return {
            'success': True,
            'establecimientos': list(establecimientos)
        }

    def get_enumber_stats(self, *args, **kwargs) -> dict:
        """Get statistics for enumbers by timbrado and establecimiento"""
        q: dict = kwargs.get('qdict', {})
        timbrado_id = q.get('timbrado_id')
        establecimiento = q.get('establecimiento')

        stats = {}
        tipos = ['FE', 'NC', 'ND', 'AF']

        for tipo in tipos:
            query = Enumbers.objects.filter(tipo=tipo)
            if timbrado_id:
                query = query.filter(expobj__timbradoobj_id=timbrado_id)
            if establecimiento:
                query = query.filter(expobj__establecimiento=establecimiento)

            total = query.count()
            available = query.filter(estado='disponible').count()
            used = query.filter(estado='usado').count()

            stats[tipo] = {
                'total': total,
                'available': available,
                'used': used
            }

        return {
            'success': True,
            'stats': stats
        }

    def validate_timbrado_data(self, *args, **kwargs) -> dict:
        """Validate timbrado data before creation"""
        q: dict = kwargs.get('qdict', {})

        ruc = q.get('ruc', '').strip()
        timbrado = q.get('timbrado', '').strip()
        fcsc = q.get('fcsc', '').strip()
        scsc = q.get('scsc', '').strip()

        errors = []

        if not ruc:
            errors.append('RUC es requerido')
        if not timbrado:
            errors.append('Número de timbrado es requerido')
        if not fcsc or len(fcsc) != 32:
            errors.append('FCSC debe tener 32 caracteres')
        if not scsc or len(scsc) != 32:
            errors.append('SCSC debe tener 32 caracteres')

        # Check if timbrado already exists
        if timbrado and Etimbrado.objects.filter(timbrado=timbrado).exists():
            errors.append(f'El timbrado {timbrado} ya existe')

        if errors:
            return {'error': ', '.join(errors)}

        return {'success': 'Datos válidos'}

    def extend_numbers_ui(self, *args, **kwargs) -> dict:
        """
        Extend numbers for existing establecimiento or create new establecimiento
        Dispatches to Celery task for long-running process
        """
        from celery.execute import send_task

        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})

        # Dispatch to Celery task
        task = send_task('Sifen.tasks.extend_numbers_task',
            kwargs={
                'username': userobj.username,
                'qdict': q
            }
        )

        return {
            'success': 'Tarea de extensión de números iniciada',
            'task_id': task.id,
            'info': 'Recibirás notificaciones del progreso'
        }

    def get_current_numbers(self, *args, **kwargs) -> dict:
        """Get current number ranges for an establecimiento"""
        q: dict = kwargs.get('qdict', {})
        timbrado_id = q.get('timbrado_id')
        establecimiento = q.get('establecimiento')

        if not timbrado_id or not establecimiento:
            return {'error': 'Falta timbrado_id o establecimiento'}

        tipos = ['FE', 'NC', 'ND', 'AF']
        current = {}

        for tipo in tipos:
            numbers = Enumbers.objects.filter(
                expobj__timbradoobj_id=timbrado_id,
                expobj__establecimiento=establecimiento,
                tipo=tipo
            ).order_by('numero')

            if numbers.exists():
                first = numbers.first()
                last = numbers.last()
                available = numbers.filter(estado='disponible').count()
                used = numbers.filter(estado='usado').count()

                current[tipo] = {
                    'exists': True,
                    'first': first.numero,
                    'last': last.numero,
                    'total': numbers.count(),
                    'available': available,
                    'used': used,
                    'serie': first.serie,
                    'expd': first.expobj.id
                }
            else:
                current[tipo] = {
                    'exists': False,
                    'first': 0,
                    'last': 0,
                    'total': 0,
                    'available': 0,
                    'used': 0,
                    'serie': '',
                    'expd': 1
                }

        return {
            'success': True,
            'current': current
        }

    def create_establecimiento_ui(self, *args, **kwargs) -> dict:
        """
        Create new establecimiento for existing timbrado
        Dispatches to Celery task for long-running process
        """
        from celery.execute import send_task

        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})

        # Validate
        timbrado_id = q.get('timbrado_id')
        establecimiento = q.get('establecimiento')

        if not timbrado_id:
            return {'error': 'Falta el ID del timbrado'}

        if not establecimiento:
            return {'error': 'Falta el número de establecimiento'}

        # Check if establecimiento already exists for this timbrado
        if Eestablecimiento.objects.filter(
            timbradoobj_id=timbrado_id,
            establecimiento=establecimiento
        ).exists():
            return {'error': f'El establecimiento {establecimiento} ya existe para este timbrado'}

        # Dispatch to Celery task
        task = send_task('Sifen.tasks.create_establecimiento_task',
            kwargs={
                'username': userobj.username,
                'qdict': q
            }
        )

        return {
            'success': 'Tarea de creación de establecimiento iniciada',
            'task_id': task.id,
            'info': 'Recibirás notificaciones del progreso'
        }
