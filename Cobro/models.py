from django.db import models
from django.contrib.auth.models import User


class Pago(models.Model):
    """
    Modelo para registrar pagos de facturas a crédito.
    Permite pagos parciales con trazabilidad completa.
    """
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia Bancaria'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('otro', 'Otro'),
    ]

    # Relación con la factura
    documentheaderobj = models.ForeignKey(
        'Sifen.DocumentHeader',
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name='Factura'
    )

    # Datos del pago
    monto = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        verbose_name='Monto Pagado'
    )
    fecha_pago = models.DateField(
        verbose_name='Fecha de Pago'
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
        default='efectivo',
        verbose_name='Método de Pago'
    )

    # Datos adicionales
    numero_referencia = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Número de Referencia',
        help_text='Número de cheque, transferencia, etc.'
    )
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones'
    )

    # Auditoría
    cargado_fecha = models.DateTimeField(auto_now_add=True)
    cargado_usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pagos_cargados',
        verbose_name='Registrado por'
    )

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago', '-cargado_fecha']

    def __str__(self):
        return f"Pago {self.id} - Factura {self.documentheaderobj.doc_numero} - {self.monto}"

    def save(self, *args, **kwargs):
        """
        Al guardar un pago, actualiza el saldo de la factura.
        """
        is_new = self.pk is None
        old_monto = 0

        if not is_new:
            # Si es una actualización, obtener el monto anterior
            old_pago = Pago.objects.get(pk=self.pk)
            old_monto = old_pago.monto

        super().save(*args, **kwargs)

        # Actualizar el saldo de la factura
        if is_new:
            # Nuevo pago: restar del saldo
            self.documentheaderobj.doc_saldo -= self.monto
        else:
            # Actualización: ajustar la diferencia
            diferencia = self.monto - old_monto
            self.documentheaderobj.doc_saldo -= diferencia

        self.documentheaderobj.save(update_fields=['doc_saldo'])

    def delete(self, *args, **kwargs):
        """
        Al eliminar un pago, restaura el saldo de la factura.
        """
        # Restaurar el monto al saldo
        self.documentheaderobj.doc_saldo += self.monto
        self.documentheaderobj.save(update_fields=['doc_saldo'])
        super().delete(*args, **kwargs)
