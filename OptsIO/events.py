"""
Bus de eventos de negocio (outbox + Celery).

- emit(): registra el evento una sola vez (idempotency_key unica) y lo despacha
  a Celery cuando la transaccion hace commit. El procesamiento es siempre por Celery.
- process_event(): ejecuta cada handler suscripto una sola vez con exito
  (BusinessEventDelivery unique(event, handler)); reintentos seguros.
- Los plugins se suscriben via BasePlugin.get_event_handlers().
"""
import logging
import traceback
from datetime import datetime
from fnmatch import fnmatch
from importlib import import_module
from typing import Callable, Dict, List, Optional

from celery import current_app
from django.db import transaction

from OptsIO.models import BusinessEvent, BusinessEventDelivery
from OptsIO.plugin_manager import plugin_manager

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5


def _registry() -> Dict[str, List[str]]:
    if not plugin_manager._plugins:
        plugin_manager.discover_plugins()
    registry: Dict[str, List[str]] = {}
    for plugin in plugin_manager.get_all_plugins().values():
        for pattern, handlers in plugin.get_event_handlers().items():
            registry.setdefault(pattern, []).extend(handlers)
    return registry


def get_handlers(event_type: str) -> List[str]:
    """Paths de handlers suscriptos al evento. Los patrones aceptan comodines (ej: '*.aprobado')."""
    handlers: List[str] = []
    for pattern, paths in _registry().items():
        if fnmatch(event_type, pattern):
            handlers.extend(p for p in paths if p not in handlers)
    return handlers


def _load(path: str) -> Callable:
    module_path, func_name = path.rsplit('.', 1)
    return getattr(import_module(module_path), func_name)


def emit(event_type: str, source, business=None, payload: Optional[dict] = None,
         userobj=None, key_suffix: str = ''):
    """
    Registra un evento para `source` (instancia de modelo ya guardada).
    Emitir dos veces el mismo evento para el mismo objeto devuelve el evento original
    sin volver a despacharlo. key_suffix permite eventos repetibles (ej: numero de cuota).
    """
    meta = source._meta
    key = f"{event_type}:{meta.app_label}.{meta.model_name}:{source.pk}"
    if key_suffix:
        key = f"{key}:{key_suffix}"

    event, created = BusinessEvent.objects.get_or_create(
        idempotency_key=key,
        defaults={
            'event_type': event_type,
            'business': business,
            'source_app': meta.app_label,
            'source_model': meta.model_name,
            'source_id': source.pk,
            'payload': payload or {},
            'created_by': getattr(userobj, 'username', '') or '',
        },
    )
    if created:
        transaction.on_commit(lambda: dispatch(event.pk))
    return event


def dispatch(event_id: int) -> bool:
    """Encola el evento en Celery. Si el broker no responde queda 'pending' (recuperable con process_events)."""
    try:
        current_app.send_task('OptsIO.tasks.process_business_event', args=[event_id])
        return True
    except Exception as e:
        logger.warning(f"Evento {event_id} no pudo encolarse en Celery, queda pendiente: {e}")
        return False


def process_event(event_id: int) -> dict:
    """Ejecuta los handlers pendientes del evento. Seguro de re-ejecutar."""
    with transaction.atomic():
        event = BusinessEvent.objects.select_for_update().get(pk=event_id)
        if event.status == 'done':
            return {'event': event_id, 'status': 'done', 'skipped': True}
        event.status = 'processing'
        event.attempts += 1
        event.save(update_fields=['status', 'attempts'])

    errors = []
    for path in get_handlers(event.event_type):
        delivery, _ = BusinessEventDelivery.objects.get_or_create(event=event, handler=path)
        if delivery.status == 'done':
            continue
        try:
            # El efecto del handler y la marca 'done' se confirman juntos.
            # El lock de fila serializa ejecuciones concurrentes del mismo handler.
            with transaction.atomic():
                delivery = BusinessEventDelivery.objects.select_for_update().get(pk=delivery.pk)
                if delivery.status == 'done':
                    continue
                result = _load(path)(event)
                delivery.status = 'done'
                delivery.attempts += 1
                delivery.last_error = ''
                delivery.result = result if isinstance(result, dict) else {}
                delivery.processed_at = datetime.now()
                delivery.save()
        except Exception as e:
            logger.error(f"Handler {path} fallo para evento {event_id}: {e}")
            BusinessEventDelivery.objects.filter(pk=delivery.pk).update(
                status='error',
                attempts=delivery.attempts + 1,
                last_error=traceback.format_exc()[-4000:],
            )
            errors.append(f"{path}: {e}")

    event.status = 'error' if errors else 'done'
    event.last_error = '\n'.join(errors)[-4000:]
    event.processed_at = datetime.now()
    event.save(update_fields=['status', 'last_error', 'processed_at'])
    return {'event': event_id, 'status': event.status, 'errors': errors}


def process_pending(limit: int = 200) -> dict:
    """Recuperacion manual de eventos pendientes o con error (hasta MAX_ATTEMPTS). No programar en cron."""
    ids = list(
        BusinessEvent.objects.filter(status__in=['pending', 'error', 'processing'], attempts__lt=MAX_ATTEMPTS)
        .order_by('created_at').values_list('pk', flat=True)[:limit]
    )
    done = error = 0
    for event_id in ids:
        if process_event(event_id).get('status') == 'done':
            done += 1
        else:
            error += 1
    return {'processed': len(ids), 'done': done, 'error': error}
