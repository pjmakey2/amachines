"""
Workflow de estados para operaciones (cargado -> verificado -> aprobado).

Cada modulo hereda WorkflowMixin y puede extender WORKFLOW_STATES. Al avanzar
de estado se emite el evento '<WORKFLOW_EVENT>.<estado>' en el bus (OptsIO.events);
la contabilidad y demas automatismos se cuelgan del estado final.
"""
from datetime import datetime

from django.db import models, transaction

from OptsIO import events


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
    estado_usuario = models.CharField(max_length=120, blank=True)
    estado_fecha = models.DateTimeField(null=True, blank=True)
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
            from Sifen.models import Business
            business = Business.objects.filter(ruc=self.bs_ruc).first()
        return business

    def get_workflow_payload(self) -> dict:
        """Datos extra para los handlers del evento. Sobrescribir en el modelo."""
        return {}

    def registrar_carga(self, userobj):
        """Llamar al crear el registro para dejar asentado quien lo cargo."""
        self.estado = self.WORKFLOW_STATES[0]
        self._stamp(userobj, self.estado, '')

    def avanzar(self, userobj, estado: str = None, nota: str = ''):
        """
        Pasa al siguiente estado (o a `estado`, que debe ser exactamente el siguiente).
        Valida permiso y segregacion de usuarios, registra el paso y emite el evento.
        """
        with transaction.atomic():
            locked = type(self).objects.select_for_update().get(pk=self.pk)
            siguiente = locked.siguiente_estado()
            if siguiente is None:
                raise WorkflowError(f"La operacion ya esta en su estado final ({locked.estado})")
            if estado and estado != siguiente:
                raise WorkflowError(f"Transicion invalida: {locked.estado} -> {estado} (corresponde {siguiente})")
            if not userobj.has_perm(locked.workflow_perm(siguiente)):
                raise WorkflowError(f"El usuario {userobj.username} no tiene permiso para pasar a '{siguiente}'")
            if self.WORKFLOW_DISTINCT_USERS and locked.estado_usuario == userobj.username:
                raise WorkflowError(f"El paso '{siguiente}' debe hacerlo un usuario distinto al que hizo '{locked.estado}'")

            locked.estado = siguiente
            locked._stamp(userobj, siguiente, nota)
            locked.save(update_fields=['estado', 'estado_usuario', 'estado_fecha', 'workflow_log'])

            if self.WORKFLOW_EVENT:
                events.emit(
                    f"{self.WORKFLOW_EVENT}.{siguiente}",
                    locked,
                    business=locked.get_workflow_business(),
                    payload=locked.get_workflow_payload(),
                    userobj=userobj,
                )

        self.estado = locked.estado
        self.estado_usuario = locked.estado_usuario
        self.estado_fecha = locked.estado_fecha
        self.workflow_log = locked.workflow_log
        return self

    def _stamp(self, userobj, estado: str, nota: str):
        ahora = datetime.now()
        self.estado_usuario = getattr(userobj, 'username', '') or ''
        self.estado_fecha = ahora
        self.workflow_log = list(self.workflow_log or []) + [{
            'estado': estado,
            'usuario': self.estado_usuario,
            'fecha': ahora.strftime('%Y-%m-%d %H:%M:%S'),
            'nota': nota,
        }]
