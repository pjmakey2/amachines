from django.db import models


class UserFLSucursal(models.Model):
    """
    Relación entre un UserProfile de Django y las sucursales FL (MySQL).
    Si un usuario no tiene ningún registro aquí, puede ver todas las sucursales.
    """
    userprofileobj = models.ForeignKey(
        'OptsIO.UserProfile',
        on_delete=models.CASCADE,
        related_name='fl_sucursales'
    )
    sucursal = models.IntegerField()

    class Meta:
        unique_together = ('userprofileobj', 'sucursal')
        verbose_name = 'Sucursal FL por Usuario'
        verbose_name_plural = 'Sucursales FL por Usuario'

    def __str__(self):
        return f'{self.userprofileobj.username} - Sucursal {self.sucursal}'
