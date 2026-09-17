from datetime import datetime

from django.db import models

from OptsIO.io_business import user_label
from OptsIO.workflow import WorkflowMixin
from Tesoreria.mng_tesoreria import MTesoreria
from Tesoreria.models import MovimientoTesoreria

MONEDAS = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]
CCT = {'max_digits': 19, 'decimal_places': 6}


class Deposito(WorkflowMixin):
    """
    Ingreso de valores cobrados a una cuenta bancaria. Se carga a mano o lo genera el cierre
    de un cobro (uno por tipo de valor). Al aprobarse acredita la cuenta en Tesoreria.
    """
    WORKFLOW_EVENT = 'deposito.deposito'
    TIPOS = [('efectivo', 'Efectivo'), ('cheque', 'Cheques'), ('transferencia', 'Transferencia recibida'),
             ('tarjeta', 'Acreditación de tarjetas')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField(db_index=True)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='efectivo', db_index=True)
    cuentaobj = models.ForeignKey('Tesoreria.CuentaBancaria', on_delete=models.PROTECT, null=True, blank=True)
    boleta_numero = models.CharField(max_length=60, blank=True, default='')
    monto = models.DecimalField(**CCT)
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    observacion = models.CharField(max_length=300, blank=True, default='')
    # Generado por el cierre de un cobro: `clave` unica hace idempotente la generacion
    automatico = models.BooleanField(default=False)
    clave = models.CharField(max_length=255, unique=True, null=True, blank=True)
    origen_app = models.CharField(max_length=80, blank=True, default='')
    origen_model = models.CharField(max_length=80, blank=True, default='')
    origen_id = models.BigIntegerField(null=True, blank=True)
    origen_desc = models.CharField(max_length=200, blank=True, default='')
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('deposito_verificado', 'Verificar depósito'), ('deposito_aprobado', 'Aprobar depósito'),
                       ('deposito_anulado', 'Anular depósito')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='deposito_numero_unico')]

    def __str__(self):
        return f"Depósito {self.numero} - {self.get_tipo_display()} {self.monto}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    def get_cuenta(self):
        return str(self.cuentaobj) if self.cuentaobj_id else 'PENDIENTE'

    def get_workflow_payload(self):
        return {'numero': self.numero, 'fecha': str(self.fecha), 'tipo': self.tipo, 'monto': str(self.monto),
                'moneda': self.moneda, 'cuenta_id': self.cuentaobj_id, 'origen': self.origen_desc}

    def workflow_validar(self, estado):
        if estado in ('verificado', 'aprobado'):
            if not self.cuentaobj_id:
                return "Indique la cuenta bancaria donde se depositó"
            if self.cuentaobj.moneda != self.moneda:
                return f"El depósito es en {self.moneda} y la cuenta en {self.cuentaobj.moneda}"
            if self.tipo in ('efectivo', 'cheque') and not self.boleta_numero:
                return "Cargue el número de boleta de depósito"
            return MTesoreria().validar_movimiento('ingreso', self.monto, cuentaobj=self.cuentaobj)
        return ''

    def workflow_on_enter(self, estado, userobj):
        clave = f"deposito.deposito:{self.pk}"
        if estado == 'aprobado':
            MTesoreria().registrar_movimiento(
                self.businessobj, self.fecha, 'ingreso', self.monto,
                f"Depósito {self.get_numero_display()} ({self.get_tipo_display()}) {self.origen_desc}".strip(),
                cuentaobj=self.cuentaobj, referencia=self.boleta_numero, origen=self, clave=clave, userobj=userobj)
        if estado == 'anulado':
            MovimientoTesoreria.objects.filter(clave=clave).update(
                anulado=True, anulado_fecha=datetime.now(), anulado_usuario=user_label(userobj))


class DepositoCheque(models.Model):
    """Cheques de terceros incluidos en un deposito (control de valores)."""
    depositoobj = models.ForeignKey(Deposito, on_delete=models.CASCADE, related_name='cheques')
    banco = models.CharField(max_length=120)
    numero = models.CharField(max_length=60)
    librador = models.CharField(max_length=200, blank=True, default='')
    fecha = models.DateField(null=True, blank=True)
    monto = models.DecimalField(**CCT)
