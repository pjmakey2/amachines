from OptsIO.io_tasks import LogErrorsTask
from OptsIO.io_json import from_json
from django.contrib.auth.models import User
from Sifen.mng_sifen import MSifen
from Sifen.mng_sifen_ruc_mapper import RMap
from celery import shared_task
import pandas as pd


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=60, time_limit=120)
def crear_documentheader_pdf(self, *args, **kwargs):
    username = kwargs.get('username')
    userobj = User.objects.get(username=username)
    ms = MSifen()
    ret = ms.crear_documentheader_pdf(*args, 
                mname='crear_documentheader_pdf', 
                task_id=self.request.id,
                userobj=userobj,
                **kwargs)
    return {'exitos': 'Proceso en curso'}


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=60, time_limit=120)
def send_invoice(self, *args, **kwargs):
    q: dict = kwargs.get('qdict')
    username = kwargs.get('username')
    userobj = User.objects.get(username=username)
    docpk = q.get('docpk')
    ms = MSifen()
    ret = ms.send_invoice(*args,
                mname='send_invoice',
                task_id=f'documentheader_{ docpk }',
                userobj=userobj,
                **kwargs)
    return {'exitos': 'Proceso en curso'}


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=300, time_limit=600)
def sync_database(self, df_dict):
    """
    Sync RUC dataframe to database
    Args:
        df_dict: Dictionary representation of DataFrame
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()
    task_id = self.request.id

    # Send start notification
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.update",
                "task_id": task_id,
                "status": "processing",
                "message": f"Processing {len(df_dict)} records...",
                "progress": 0
            }
        )

    rmap = RMap()
    df = pd.DataFrame(df_dict)
    created, updated, errors = rmap.sync_to_database(df)

    result = {
        'created': created,
        'updated': updated,
        'errors': errors,
        'total': len(df)
    }

    # Send completion notification
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f"task_{task_id}",
            {
                "type": "task.complete",
                "task_id": task_id,
                "status": "completed",
                "message": f"Completed: {created} created, {updated} updated, {errors} errors",
                "result": result
            }
        )

    return result


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=600, time_limit=900)
def create_timbrado_task(self, *args, **kwargs):
    """
    Create timbrado and generate number ranges
    Long-running task with WebSocket notifications
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    from django.http import QueryDict
    from Sifen import ekuatia_serials
    from OptsIO.ws_utils import ws_send_notification, ws_send_task_update, ws_send_task_complete, ws_send_task_error

    username = kwargs.get('username')
    userobj = User.objects.get(username=username)
    q: dict = kwargs.get('qdict', {})

    task_id = self.request.id
    task_name = f'Crear Timbrado {q.get("timbrado", "")}'

    # Send start notification to task bell
    ws_send_task_update(
        username,
        task_id,
        task_name,
        'Iniciando creación de timbrado...',
        progress=0
    )

    try:
        # Build QueryDict for ekuatia_serials
        qdict = QueryDict(mutable=True)
        qdict.update({
            'ruc': q.get('ruc'),
            'dv': q.get('dv'),
            'timbrado': q.get('timbrado'),
            'inicio': q.get('inicio'),
            'fcsc': q.get('fcsc'),
            'scsc': q.get('scsc'),
        })

        # Handle lists - parse JSON strings from frontend
        def parse_list(value, default=[]):
            if not value:
                return default
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                try:
                    parsed = from_json(value)
                    if isinstance(parsed, list):
                        return parsed
                except:
                    return [value]
            return [value]

        establecimientos = parse_list(q.get('establecimiento'))
        qdict.setlist('establecimiento', establecimientos)

        tipos = parse_list(q.get('tipo'))
        qdict.setlist('tipo', tipos)

        expds = parse_list(q.get('expd'))
        qdict.setlist('expd', [int(x) for x in expds])

        series = parse_list(q.get('serie'))
        qdict.setlist('serie', series)

        nstarts = parse_list(q.get('nstart'))
        qdict.setlist('nstart', [int(x) for x in nstarts])

        nends = parse_list(q.get('nend'))
        qdict.setlist('nend', [int(x) for x in nends])

        # Create timbrado
        eser = ekuatia_serials.Eserial()
        result = eser.create_timbrado(userobj, qdict=qdict)

        # Send success notification to task bell
        ws_send_task_complete(
            username,
            task_id,
            task_name,
            f'Timbrado {q.get("timbrado")} creado exitosamente con {len(tipos)} tipos de documento',
            result={'timbrado': q.get('timbrado'), 'tipos': tipos}
        )

        return {
            'success': True,
            'timbrado': q.get('timbrado'),
            'tipos': tipos
        }

    except Exception as e:
        # Send error notification to task bell
        ws_send_task_error(
            username,
            task_id,
            task_name,
            str(e),
            f'Error al crear timbrado: {str(e)}'
        )
        raise


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=600, time_limit=900)
def extend_numbers_task(self, *args, **kwargs):
    """
    Extend numbers for existing establecimiento
    Long-running task with WebSocket notifications
    """
    from Sifen import ekuatia_serials
    from Sifen.models import Etimbrado
    from OptsIO.ws_utils import ws_send_task_update, ws_send_task_complete, ws_send_task_error

    username = kwargs.get('username')
    userobj = User.objects.get(username=username)
    q: dict = kwargs.get('qdict', {})

    task_id = self.request.id
    task_name = f'Extender Números Est. {q.get("establecimiento", "")}'

    # Send start notification to task bell
    ws_send_task_update(
        username,
        task_id,
        task_name,
        'Iniciando extensión de números...',
        progress=0
    )

    try:
        timbrado_id = q.get('timbrado_id')
        establecimiento = q.get('establecimiento')
        ranges = q.get('ranges', [])

        # Parse JSON string if needed
        if isinstance(ranges, str):
            ranges = from_json(ranges)

        timbradoobj = Etimbrado.objects.get(pk=timbrado_id)
        eser = ekuatia_serials.Eserial()

        total_created = 0
        total_ranges = len(ranges)
        for idx, r in enumerate(ranges):
            tipo = r.get('tipo')
            expd = int(r.get('expd', 1))
            serie = r.get('serie', 'ZZZ')
            nstart = int(r.get('nstart', 1))
            nend = int(r.get('nend', 1000))

            # Generate numbers
            eser.generate_numbers_timbrado(
                timbradoobj.timbrado,
                tipo,
                establecimiento,
                expd,
                serie,
                nstart,
                nend
            )

            created = nend - nstart + 1
            total_created += created

            # Update progress
            progress = int(((idx + 1) / total_ranges) * 100)
            ws_send_task_update(
                username,
                task_id,
                task_name,
                f'Creados {created} números para {tipo}',
                progress=progress
            )

        # Send success notification to task bell
        ws_send_task_complete(
            username,
            task_id,
            task_name,
            f'Extensión completada: {total_created} números creados',
            result={'total_created': total_created}
        )

        return {
            'success': True,
            'total_created': total_created
        }

    except Exception as e:
        ws_send_task_error(
            username,
            task_id,
            task_name,
            str(e),
            f'Error al extender números: {str(e)}'
        )
        raise


@shared_task(bind=True, base=LogErrorsTask, soft_time_limit=600, time_limit=900)
def create_establecimiento_task(self, *args, **kwargs):
    """
    Create new establecimiento for existing timbrado
    Long-running task with WebSocket notifications
    """
    from Sifen import ekuatia_serials
    from Sifen.models import Etimbrado, Eestablecimiento
    from OptsIO.ws_utils import ws_send_task_update, ws_send_task_complete, ws_send_task_error

    username = kwargs.get('username')
    userobj = User.objects.get(username=username)
    q: dict = kwargs.get('qdict', {})

    task_id = self.request.id
    establecimiento_num = q.get('establecimiento', '')
    task_name = f'Crear Establecimiento {establecimiento_num}'

    # Send start notification to task bell
    ws_send_task_update(
        username,
        task_id,
        task_name,
        'Iniciando creación de establecimiento...',
        progress=0
    )

    try:
        timbrado_id = q.get('timbrado_id')
        establecimiento = int(q.get('establecimiento'))
        direccion = q.get('direccion', '')
        ranges = q.get('ranges', [])

        # Parse JSON string if needed
        if isinstance(ranges, str):
            ranges = from_json(ranges)

        timbradoobj = Etimbrado.objects.get(pk=timbrado_id)

        # Create Eestablecimiento
        estab_obj = Eestablecimiento.objects.create(
            timbradoobj=timbradoobj,
            establecimiento=establecimiento,
            direccion=direccion
        )

        ws_send_task_update(
            username,
            task_id,
            task_name,
            f'Establecimiento {establecimiento} creado',
            progress=10
        )

        # Generate numbers for each range
        eser = ekuatia_serials.Eserial()
        total_created = 0
        total_ranges = len(ranges)

        for idx, r in enumerate(ranges):
            tipo = r.get('tipo')
            expd = int(r.get('expd', 1))
            serie = r.get('serie', 'ZZZ')
            nstart = int(r.get('nstart', 1))
            nend = int(r.get('nend', 1000))

            # Generate numbers
            eser.generate_numbers_timbrado(
                timbradoobj.timbrado,
                tipo,
                establecimiento,
                expd,
                serie,
                nstart,
                nend
            )

            created = nend - nstart + 1
            total_created += created

            # Update progress (10% for establecimiento creation, 90% for numbers)
            progress = 10 + int(((idx + 1) / total_ranges) * 90)
            ws_send_task_update(
                username,
                task_id,
                task_name,
                f'Creados {created} números para {tipo}',
                progress=progress
            )

        # Send success notification to task bell
        ws_send_task_complete(
            username,
            task_id,
            task_name,
            f'Establecimiento {establecimiento} creado con {total_created} números',
            result={'establecimiento': establecimiento, 'total_created': total_created}
        )

        return {
            'success': True,
            'establecimiento': establecimiento,
            'total_created': total_created
        }

    except Exception as e:
        ws_send_task_error(
            username,
            task_id,
            task_name,
            str(e),
            f'Error al crear establecimiento: {str(e)}'
        )
        raise