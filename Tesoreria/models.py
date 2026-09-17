from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum

MONEDAS = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]
CCT = {'max_digits': 19, 'decimal_places': 6}


class TrackMixin(models.Model):
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        abstract = True


class Banco(TrackMixin):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    codigo = models.CharField(max_length=20, blank=True, default='')
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class SaldoMixin:
    """Saldo = saldo_inicial + ingresos - egresos de los movimientos no anulados."""
    _mov_field = None

    def get_saldo(self) -> Decimal:
        qs = MovimientoTesoreria.objects.filter(anulado=False, **{self._mov_field: self})
        tot = {r['tipo']: r['t'] for r in qs.values('tipo').annotate(t=Sum('monto'))}
        return (self.saldo_inicial or 0) + (tot.get('ingreso') or 0) - (tot.get('egreso') or 0)


class CuentaBancaria(SaldoMixin, TrackMixin):
    _mov_field = 'cuentaobj'
    TIPOS = [('cta_cte', 'Cuenta Corriente'), ('caja_ahorro', 'Caja de Ahorro')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    bancoobj = models.ForeignKey(Banco, on_delete=models.PROTECT)
    numero = models.CharField(max_length=60)
    titular = models.CharField(max_length=200, blank=True, default='')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='cta_cte')
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    saldo_inicial = models.DecimalField(**CCT, default=0)
    saldo_inicial_fecha = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'bancoobj', 'numero')
        ordering = ['bancoobj__nombre', 'numero']

    def __str__(self):
        return f"{self.bancoobj.nombre} {self.numero} ({self.moneda})"

    def get_descripcion(self):
        return str(self)


class Chequera(TrackMixin):
    TIPOS = [('vista', 'A la vista'), ('diferido', 'Pago diferido')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    cuentaobj = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='vista')
    serie = models.CharField(max_length=20, blank=True, default='')
    numero_desde = models.BigIntegerField()
    numero_hasta = models.BigIntegerField()
    proximo_numero = models.BigIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['cuentaobj', 'numero_desde']

    def __str__(self):
        return f"{self.cuentaobj} {self.serie} {self.numero_desde}-{self.numero_hasta}"

    def get_descripcion(self):
        return f"{self.cuentaobj} | {self.get_tipo_display()} {self.serie} ({self.disponibles} disp.)"

    @property
    def disponibles(self) -> int:
        return max(0, self.numero_hasta - self.proximo_numero + 1)

    def tomar_numero(self) -> int:
        """Reserva el proximo numero de cheque. El lock de fila evita numeros duplicados."""
        with transaction.atomic():
            ch = Chequera.objects.select_for_update().get(pk=self.pk)
            if not ch.activo or ch.proximo_numero > ch.numero_hasta:
                raise ValueError(f"La chequera {ch} no tiene cheques disponibles")
            numero = ch.proximo_numero
            ch.proximo_numero = numero + 1
            ch.save(update_fields=['proximo_numero'])
        self.proximo_numero = numero + 1
        return numero


class Cheque(TrackMixin):
    ESTADOS = [
        ('emitido', 'Emitido'),
        ('entregado', 'Entregado'),
        ('cobrado', 'Cobrado'),
        ('anulado', 'Anulado'),
    ]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    chequeraobj = models.ForeignKey(Chequera, on_delete=models.PROTECT)
    numero = models.BigIntegerField()
    fecha_emision = models.DateField()
    fecha_pago = models.DateField()
    beneficiario = models.CharField(max_length=200)
    monto = models.DecimalField(**CCT)
    concepto = models.CharField(max_length=300, blank=True, default='')
    a_la_orden = models.BooleanField(default=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='emitido', db_index=True)
    # Operacion que origino el cheque (ej: Egreso.PagoProveedor)
    origen_app = models.CharField(max_length=80, blank=True, default='')
    origen_model = models.CharField(max_length=80, blank=True, default='')
    origen_id = models.BigIntegerField(null=True, blank=True)
    anulado_fecha = models.DateTimeField(null=True, blank=True)
    anulado_usuario = models.CharField(max_length=120, null=True, blank=True)
    anulado_motivo = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        unique_together = ('chequeraobj', 'numero')
        ordering = ['-fecha_emision', '-numero']

    def __str__(self):
        return f"Cheque {self.numero} - {self.beneficiario}"


class Caja(SaldoMixin, TrackMixin):
    _mov_field = 'cajaobj'
    TIPOS = [('general', 'Caja General'), ('chica', 'Caja Chica')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='general')
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    # Caja chica: el saldo nunca puede superar el tope (0 = sin tope)
    tope = models.DecimalField(**CCT, default=0)
    responsable = models.CharField(max_length=120, blank=True, default='')
    saldo_inicial = models.DecimalField(**CCT, default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.moneda})"


class MovimientoTesoreria(TrackMixin):
    """Libro de movimientos de cuentas bancarias y cajas. Todo saldo sale de aca."""
    TIPOS = [('ingreso', 'Ingreso'), ('egreso', 'Egreso')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    fecha = models.DateField(db_index=True)
    cuentaobj = models.ForeignKey(CuentaBancaria, on_delete=models.PROTECT, null=True, blank=True)
    cajaobj = models.ForeignKey(Caja, on_delete=models.PROTECT, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    monto = models.DecimalField(**CCT)
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    concepto = models.CharField(max_length=300)
    referencia = models.CharField(max_length=120, blank=True, default='')
    chequeobj = models.ForeignKey(Cheque, on_delete=models.PROTECT, null=True, blank=True)
    # Operacion que origino el movimiento (ej: Deposito, PagoProveedor, Transferencia)
    origen_app = models.CharField(max_length=80, blank=True, default='')
    origen_model = models.CharField(max_length=80, blank=True, default='')
    origen_id = models.BigIntegerField(null=True, blank=True)
    # Clave de idempotencia: registrar dos veces la misma clave devuelve el movimiento existente
    clave = models.CharField(max_length=255, unique=True, null=True, blank=True)
    anulado = models.BooleanField(default=False)
    anulado_fecha = models.DateTimeField(null=True, blank=True)
    anulado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ['-fecha', '-id']
        constraints = [
            models.CheckConstraint(
                name='mov_tesoreria_cuenta_xor_caja',
                condition=(
                    models.Q(cuentaobj__isnull=False, cajaobj__isnull=True)
                    | models.Q(cuentaobj__isnull=True, cajaobj__isnull=False)
                ),
            ),
            models.CheckConstraint(name='mov_tesoreria_monto_positivo', condition=models.Q(monto__gt=0)),
        ]

    def __str__(self):
        return f"{self.fecha} {self.tipo} {self.monto} {self.cuentaobj or self.cajaobj}"

    def get_destino(self):
        return str(self.cuentaobj or self.cajaobj)
