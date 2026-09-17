"""Endpoints genericos (iom) para operar el workflow de cualquier modelo con WorkflowMixin."""
from django.apps import apps

from OptsIO.io_business import get_active_business, is_tenant_model
from OptsIO.workflow import WorkflowMixin


class MWorkflow:
    def _get_obj(self, userobj, q):
        model = apps.get_app_config(q.get('model_app_name', '')).get_model(q.get('model_name', ''))
        if not issubclass(model, WorkflowMixin):
            return None
        qs = model.objects.filter(pk=q.get('id') or 0)
        if is_tenant_model(model):
            qs = qs.filter(businessobj=get_active_business(userobj))
        return qs.first()

    def avanzar(self, *args, **kwargs) -> dict:
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        obj = self._get_obj(userobj, q)
        if not obj:
            return {'error': 'Registro inexistente'}
        error = obj.validar_avance(userobj, q.get('estado') or None)
        if error:
            return {'error': error}
        obj.avanzar(userobj, q.get('estado') or None, q.get('nota', ''))
        return {'success': f'Operación {obj.pk}: {obj.estado}', 'estado': obj.estado}

    def anular(self, *args, **kwargs) -> dict:
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        obj = self._get_obj(userobj, q)
        if not obj:
            return {'error': 'Registro inexistente'}
        error = obj.validar_anulacion(userobj)
        if error:
            return {'error': error}
        obj.anular(userobj, q.get('motivo', ''))
        return {'success': f'Operación {obj.pk} anulada'}

    def get_log(self, *args, **kwargs) -> dict:
        obj = self._get_obj(kwargs.get('userobj'), kwargs.get('qdict', {}))
        if not obj:
            return {'error': 'Registro inexistente'}
        return {'success': True, 'estado': obj.estado, 'anulado': obj.anulado, 'log': obj.workflow_log}
