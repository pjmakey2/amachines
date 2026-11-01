from django.db import models
from django.db.models import Sum

from Contabilidad.codigos import FORMATO_DEFAULT, corto, nivel as nivel_de
from OptsIO.io_money import precision_monetaria
from OptsIO.workflow import WorkflowMixin

CCT = {'max_digits': 19, 'decimal_places': 6}


class ContaTrack(models.Model):
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        abstract = True


class ConfigContable(ContaTrack):
    """Parametros contables del negocio."""
    businessobj = models.OneToOneField('Sifen.Business', on_delete=models.CASCADE)
    plantilla = models.CharField(max_length=60, blank=True, default='')
    # Digitos por nivel del codigo de cuenta (Contabilidad/codigos.py). Solo se cambia con el plan vacio.
    formato_codigo = models.CharField(max_length=30, default=FORMATO_DEFAULT)
    # Documentos con fecha anterior no generan asiento (arranque de la contabilidad)
    fecha_inicio = models.DateField(null=True, blank=True)


class PlanCuenta(ContaTrack):
    TIPOS = [('activo', 'Activo'), ('pasivo', 'Pasivo'), ('patrimonio', 'Patrimonio Neto'),
             ('ingreso', 'Ingreso'), ('costo', 'Costo'), ('gasto', 'Gasto')]
    DEUDORAS = ('activo', 'costo', 'gasto')

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    # Codigo completo de largo fijo segun ConfigContable.formato_codigo, ej: 003.001.003.000.000.000
    codigo = models.CharField(max_length=60)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    padreobj = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='hijas')
    nivel = models.IntegerField(default=1)
    # Solo las cuentas imputables reciben movimientos; el resto agrupa
    imputable = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'codigo')
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} {self.nombre}"

    def get_descripcion(self):
        return str(self)

    def get_codigo_corto(self):
        return corto(self.codigo)

    def get_ruta(self) -> str:
        """Nombres desde el primer nivel hasta la cuenta: 'GASTOS - GASTOS OPERATIVOS - ... - Software'."""
        nombres, nodo = [], self
        while nodo is not None:
            nombres.append(nodo.nombre)
            nodo = nodo.padreobj
        return ' - '.join(reversed(nombres))

    @property
    def deudora(self) -> bool:
        return self.tipo in self.DEUDORAS


class CuentaRol(ContaTrack):
    """
    Que cuenta cumple cada funcion en los asientos automaticos (clientes, IVA debito, caja...).
    Los formatos de asiento hablan de roles, no de codigos: asi una plantilla sirve a cualquier plan.
    """
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    rol = models.CharField(max_length=60)
    cuentaobj = models.ForeignKey(PlanCuenta, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('businessobj', 'rol')
        ordering = ['rol']

    def __str__(self):
        return f"{self.rol} -> {self.cuentaobj}"


class MapeoCuenta(ContaTrack):
    """Cuenta especifica para un registro de otro plugin (una cuenta bancaria, una caja, una categoria de gasto)."""
    TIPOS = [('cuenta_bancaria', 'Cuenta bancaria'), ('caja', 'Caja'), ('categoria_gasto', 'Categoría de gasto')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=30, choices=TIPOS)
    ref_id = models.BigIntegerField()
    ref_desc = models.CharField(max_length=200, blank=True, default='')
    cuentaobj = models.ForeignKey(PlanCuenta, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('businessobj', 'tipo', 'ref_id')
        ordering = ['tipo', 'ref_desc']


class FormatoAsiento(ContaTrack):
    """Como se arma el asiento de un evento. Editable por negocio; nace de una plantilla."""
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    evento = models.CharField(max_length=120)
    nombre = models.CharField(max_length=200)
    concepto = models.CharField(max_length=300, help_text='Texto del asiento; admite {variables} del evento')
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'evento')
        ordering = ['evento']

    def __str__(self):
        return f"{self.nombre} ({self.evento})"


class FormatoAsientoLinea(models.Model):
    LADOS = [('debe', 'Debe'), ('haber', 'Haber')]

    formatoobj = models.ForeignKey(FormatoAsiento, on_delete=models.CASCADE, related_name='lineas')
    orden = models.IntegerField(default=1)
    lado = models.CharField(max_length=5, choices=LADOS)
    # Rol a resolver (CuentaRol / MapeoCuenta) o, si se prefiere, una cuenta fija
    rol = models.CharField(max_length=60, blank=True, default='')
    cuentaobj = models.ForeignKey(PlanCuenta, on_delete=models.PROTECT, null=True, blank=True)
    # Clave del monto que calcula el handler del evento (total, neto_10, iva_10, ...)
    monto = models.CharField(max_length=60)
    glosa = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['orden', 'id']


class Asiento(WorkflowMixin, ContaTrack):
    """Asiento del libro diario. Los automaticos nacen aprobados; los manuales siguen el workflow."""
    WORKFLOW_EVENT = None
    ORIGENES = [('automatico', 'Automático'), ('manual', 'Manual'), ('reverso', 'Reverso')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField(db_index=True)
    concepto = models.CharField(max_length=300)
    origen = models.CharField(max_length=20, choices=ORIGENES, default='manual')
    evento = models.CharField(max_length=120, blank=True, default='')
    origen_app = models.CharField(max_length=80, blank=True, default='')
    origen_model = models.CharField(max_length=80, blank=True, default='')
    origen_id = models.BigIntegerField(null=True, blank=True)
    # Idempotencia: un evento genera su asiento una sola vez
    clave = models.CharField(max_length=255, unique=True, null=True, blank=True)
    reversaobj = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='reversos')
    total = models.DecimalField(**CCT, default=0)

    class Meta:
        ordering = ['-fecha', '-numero']
        permissions = [('asiento_verificado', 'Verificar asiento'), ('asiento_aprobado', 'Aprobar asiento'),
                       ('asiento_anulado', 'Anular asiento')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='conta_asiento_numero_unico')]
        indexes = [models.Index(fields=['origen_app', 'origen_model', 'origen_id'])]

    def __str__(self):
        return f"Asiento {self.numero} - {self.concepto}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    @precision_monetaria
    def get_totales(self):
        t = self.detalles.aggregate(d=Sum('debe'), h=Sum('haber'))
        return (t['d'] or 0), (t['h'] or 0)

    def workflow_validar(self, estado):
        if estado == 'anulado' and self.origen != 'manual':
            return "Un asiento automático se revierte anulando la operación que lo originó"
        if estado in ('verificado', 'aprobado'):
            debe, haber = self.get_totales()
            if debe <= 0:
                return "El asiento no tiene movimientos"
            if debe != haber:
                return f"El asiento no balancea: debe {debe:,.2f} / haber {haber:,.2f}"
        return ''


class AsientoDetalle(models.Model):
    asientoobj = models.ForeignKey(Asiento, on_delete=models.CASCADE, related_name='detalles')
    cuentaobj = models.ForeignKey(PlanCuenta, on_delete=models.PROTECT)
    debe = models.DecimalField(**CCT, default=0)
    haber = models.DecimalField(**CCT, default=0)
    glosa = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['id']
