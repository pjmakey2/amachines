from OptsIO.models import UserTask, FailedTask
from OptsIO import io_json
from OptsIO.io_json import to_json
from datetime import datetime
from celery import Task


class LogErrorsTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.save_failed_task(exc, task_id, args, kwargs, einfo)
        super(LogErrorsTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def save_failed_task(self, exc, task_id, args, kwargs, traceback):
        """
        :type exc: Exception
        """
        task = FailedTask()
        task.celery_task_id = task_id
        task.full_name = self.name
        task.name = self.name.split('.')[-1]
        task.exception_class = exc.__class__.__name__
        task.exception_msg = str(exc).strip()
        task.traceback = str(traceback).strip()
        task.updated_at = datetime.now()

        if args:
            task.args = to_json(list(args))
        if kwargs:
            task.kwargs = to_json(kwargs)

        # Find if task with same args, name and exception already exists
        # If it do, update failures count and last updated_at
        #: :type: FailedTask
        existing_task = FailedTask.objects.filter(
            args=task.args,
            kwargs=task.kwargs,
            full_name=task.full_name,
            exception_class=task.exception_class,
            exception_msg=task.exception_msg,
        )

        if len(existing_task):
            existing_task = existing_task[0]
            existing_task.failures += 1
            existing_task.updated_at = task.updated_at
            existing_task.save(force_update=True,
                               update_fields=('updated_at', 'failures'))
        else:
            task.save(force_insert=True)


class IOTasks:
    """Maneja operaciones relacionadas con las tareas de usuario"""

    def dismiss_task(self, *args, **kwargs) -> dict:
        """
        Marca una tarea como descartada para que no aparezca en las notificaciones
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        task_id = q.get('task_id')

        if not task_id:
            return {'error': 'Falta el task_id'}

        if not userobj or not userobj.is_authenticated:
            return {'error': 'Usuario no autenticado'}

        username = userobj.username

        try:
            # Buscar la tarea del usuario
            task = UserTask.objects.get(task_id=task_id, username=username)
            task.dismissed = True
            task.save()

            return {'success': 'Tarea descartada exitosamente'}

        except UserTask.DoesNotExist:
            return {'error': 'Tarea no encontrada'}
        except Exception as e:
            return {'error': f'Error al descartar tarea: {str(e)}'}

    def dismiss_multiple_tasks(self, *args, **kwargs) -> dict:
        """
        Marca múltiples tareas como descartadas
        """
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        task_ids = io_json.from_json(q.get('task_ids', '[]'))

        if not task_ids:
            return {'error': 'Falta la lista de task_ids'}

        if not userobj or not userobj.is_authenticated:
            return {'error': 'Usuario no autenticado'}

        username = userobj.username

        try:
            # Actualizar todas las tareas del usuario en una sola operación
            count = UserTask.objects.filter(
                task_id__in=task_ids,
                username=username
            ).update(dismissed=True)

            return {'success': f'{count} tarea(s) descartada(s) exitosamente', 'count': count}

        except Exception as e:
            return {'error': f'Error al descartar tareas: {str(e)}'}
