"""
Workflow de estados para operaciones (cargado -> verificado -> aprobado).

Cada modulo hereda WorkflowMixin y puede extender WORKFLOW_STATES. Al avanzar
de estado se emite el evento '<WORKFLOW_EVENT>.<estado>' en el bus (OptsIO.events);
la contabilidad y demas automatismos se cuelgan del estado final.

Auditoria con la convencion del proyecto: <paso>_fecha / <paso>_usuario. Un paso
extra (ej: 'pagado') se agrega a WORKFLOW_STATES y, si se quiere auditar en columnas,
se declaran pagado_fecha / pagado_usuario en el modelo; el historial completo queda
siempre en workflow_log.
"""
from datetime import datetime

from django.db import models, transaction

from OptsIO import events
from OptsIO.io_business import user_label
from OptsIO.io_money import precision_monetaria
from Sifen.models import Business


class WorkflowError(Exception):
    pass


class WorkflowMixin(models.Model):
    # Secuencia ordenada; el ultimo estado es el cierre de la operacion.
    WORKFLOW_STATES = ['cargado', 'verificado', 'aprobado']
    # Prefijo del evento, ej: 'egreso.gasto' -> 'egreso.gasto.aprobado'. None = no emite.
    WORKFLOW_EVENT = None
    # True = quien ejecuto un paso no puede ejecutar el siguiente (segregacion de funciones).
    WORKFLOW_DISTINCT_USERS = False

    estado = models.CharField(max_length=30, default='cargado', db_index=True)
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    verificado_fecha = models.DateTimeField(null=True, blank=True)
    verificado_usuario = models.CharField(max_length=120, null=True, blank=True)
    aprobado_fecha = models.DateTimeField(null=True, blank=True)
    aprobado_usuario = models.CharField(max_length=120, null=True, blank=True)
    anulado = models.BooleanField(default=False, db_index=True)
    anulado_fecha = models.DateTimeField(null=True, blank=True)
    anulado_usuario = models.CharField(max_length=120, null=True, blank=True)
    anulado_motivo = models.CharField(max_length=300, blank=True, default='')
    workflow_log = models.JSONField(default=list, blank=True)

    class Meta:
        abstract = True

    @property
    def estado_final(self) -> str:
        return self.WORKFLOW_STATES[-1]

    @property
    def cerrado(self) -> bool:
        return self.estado == self.estado_final

    def siguiente_estado(self):
        idx = self.WORKFLOW_STATES.index(self.estado)
        if idx + 1 < len(self.WORKFLOW_STATES):
            return self.WORKFLOW_STATES[idx + 1]
        return None

    def workflow_perm(self, estado: str) -> str:
        """Permiso requerido para pasar a `estado`. Declararlo en Meta.permissions del modelo."""
        return f"{self._meta.app_label}.{self._meta.model_name}_{estado}"

    def get_workflow_business(self):
        business = getattr(self, 'businessobj', None)
        if business is None and getattr(self, 'bs_ruc', None):
            business = Business.objects.filter(ruc=self.bs_ruc).first()
        return business

    def get_workflow_payload(self) -> dict:
        """Datos extra para los handlers del evento. Sobrescribir en el modelo."""
        return {}

    def registrar_carga(self, userobj):
        """Llamar al crear el registro para dejar asentado quien lo cargo."""
        self.estado = self.WORKFLOW_STATES[0]
        self._stamp(userobj, self.estado, '')

    def workflow_validar(self, estado: str) -> str:
        """Regla de negocio del modelo para entrar a `estado` ('anulado' incluido). '' = ok. Sobrescribir."""
        return ''

    def workflow_on_enter(self, estado: str, userobj):
        """Efectos propios del modelo al entrar a `estado`, dentro de la transaccion. Sobrescribir."""

    @precision_monetaria
    def validar_avance(self, userobj, estado: str = None) -> str:
        """Mensaje de error si no se puede avanzar, o ''. No modifica nada (apto para endpoints)."""
        if self.anulado:
            return "La operacion esta anulada"
        siguiente = self.siguiente_estado()
        if siguiente is None:
            return f"La operacion ya esta en su estado final ({self.estado})"
        if estado and estado != siguiente:
            return f"Transicion invalida: {self.estado} -> {estado} (corresponde {siguiente})"
        if not userobj.has_perm(self.workflow_perm(siguiente)):
            return f"El usuario {userobj.username} no tiene permiso para pasar a '{siguiente}'"
        ultimo = (self.workflow_log or [{}])[-1].get('username')
        if self.WORKFLOW_DISTINCT_USERS and ultimo == userobj.username:
            return f"El paso '{siguiente}' debe hacerlo un usuario distinto al que hizo '{self.estado}'"
        return self.workflow_validar(siguiente)

    @precision_monetaria
    def validar_anulacion(self, userobj) -> str:
        if self.anulado:
            return "La operacion ya esta anulada"
        if not userobj.has_perm(self.workflow_perm('anulado')):
            return f"El usuario {userobj.username} no tiene permiso para anular"
        return self.workflow_validar('anulado')

    @precision_monetaria
    def avanzar(self, userobj, estado: str = None, nota: str = ''):
        """Pasa al siguiente estado: valida, registra el paso, aplica efectos y emite el evento."""
        with transaction.atomic():
            locked = type(self).objects.select_for_update().get(pk=self.pk)
            error = locked.validar_avance(userobj, estado)
            if error:
                raise WorkflowError(error)
            siguiente = locked.siguiente_estado()
            locked.estado = siguiente
            locked._stamp(userobj, siguiente, nota)
            locked.save()
            locked.workflow_on_enter(siguiente, userobj)
            locked._emit(siguiente, userobj)
        self.refresh_from_db()
        return self

    @precision_monetaria
    def anular(self, userobj, motivo: str = ''):
        """Anula la operacion en cualquier estado y emite '<WORKFLOW_EVENT>.anulado' (reversos)."""
        with transaction.atomic():
            locked = type(self).objects.select_for_update().get(pk=self.pk)
            error = locked.validar_anulacion(userobj)
            if error:
                raise WorkflowError(error)
            locked.anulado = True
            locked.anulado_motivo = (motivo or '')[:300]
            locked._stamp(userobj, 'anulado', motivo)
            locked.save()
            locked.workflow_on_enter('anulado', userobj)
            locked._emit('anulado', userobj)
        self.refresh_from_db()
        return self

    def _emit(self, estado: str, userobj):
        if self.WORKFLOW_EVENT:
            events.emit(
                f"{self.WORKFLOW_EVENT}.{estado}",
                self,
                business=self.get_workflow_business(),
                payload=self.get_workflow_payload(),
                userobj=userobj,
            )

    def _stamp(self, userobj, estado: str, nota: str):
        ahora = datetime.now()
        if hasattr(self, f'{estado}_fecha'):
            setattr(self, f'{estado}_fecha', ahora)
            setattr(self, f'{estado}_usuario', user_label(userobj))
        self.workflow_log = list(self.workflow_log or []) + [{
            'estado': estado,
            'username': getattr(userobj, 'username', '') or '',
            'usuario': user_label(userobj),
            'fecha': ahora.strftime('%Y-%m-%d %H:%M:%S'),
            'nota': nota,
        }]
