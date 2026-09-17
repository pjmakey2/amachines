from datetime import datetime
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum

from OptsIO.io_business import user_label
from OptsIO.io_money import precision_monetaria
from OptsIO.workflow import WorkflowMixin

CCT = {'max_digits': 19, 'decimal_places': 6}


class AlmacenError(Exception):
    """Regla de inventario incumplida (stock insuficiente, ubicacion ajena...)."""


class AlmacenTrack(models.Model):
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        abstract = True


class Bodega(AlmacenTrack):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=300, blank=True, default='')
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Ubicacion(AlmacenTrack):
    """Lugar fisico dentro de una bodega. El despacho toma stock en orden picking -> almacenaje -> recepcion."""
    TIPOS = [('recepcion', 'Recepción (muelle)'), ('almacenaje', 'Almacenaje'), ('picking', 'Picking'), ('averiados', 'Averiados / no vendible')]
    PRIORIDAD_DESPACHO = {'picking': 1, 'almacenaje': 2, 'recepcion': 3}

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    bodegaobj = models.ForeignKey(Bodega, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=40, help_text='Ej: A-01-03 (pasillo-estante-nivel)')
    descripcion = models.CharField(max_length=200, blank=True, default='')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='almacenaje')
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('bodegaobj', 'codigo')
        ordering = ['bodegaobj__nombre', 'codigo']

    def __str__(self):
        return f"{self.bodegaobj.nombre} / {self.codigo}"

    def get_descripcion(self):
        return f"{self} ({self.get_tipo_display()})"

    @property
    def vendible(self) -> bool:
        return self.tipo in self.PRIORIDAD_DESPACHO


class StockUbicacion(models.Model):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    ubicacionobj = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    cantidad = models.DecimalField(**CCT, default=0)

    class Meta:
        unique_together = ('productoobj', 'ubicacionobj')
        ordering = ['productoobj__descripcion']
        constraints = [models.CheckConstraint(name='almacen_stock_no_negativo', condition=models.Q(cantidad__gte=0))]

    def get_ubicacion(self):
        return str(self.ubicacionobj)


class ReservaStock(models.Model):
    """Stock comprometido por un pedido todavia no despachado. disponible = stock vendible - reservas activas."""
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    cantidad = models.DecimalField(**CCT)
    activa = models.BooleanField(default=True, db_index=True)
    origen_app = models.CharField(max_length=80)
    origen_model = models.CharField(max_length=80)
    origen_id = models.BigIntegerField()
    cargado_fecha = models.DateTimeField(default=datetime.now)

    class Meta:
        unique_together = ('productoobj', 'origen_app', 'origen_model', 'origen_id')


class MovimientoStock(models.Model):
    """Libro de inventario: todo cambio de stock pasa por aca."""
    TIPOS = [('recepcion', 'Recepción'), ('traslado', 'Traslado'), ('despacho', 'Despacho / venta'),
             ('ajuste', 'Ajuste de inventario'), ('devolucion', 'Devolución'), ('reverso', 'Reverso')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=datetime.now, db_index=True)
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    ubicacionobj = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    # Positiva = entra a la ubicacion; negativa = sale
    cantidad = models.DecimalField(**CCT)
    saldo = models.DecimalField(**CCT, default=0)
    costo_unitario = models.DecimalField(**CCT, default=0)
    concepto = models.CharField(max_length=300, blank=True, default='')
    origen_app = models.CharField(max_length=80, blank=True, default='')
    origen_model = models.CharField(max_length=80, blank=True, default='')
    origen_id = models.BigIntegerField(null=True, blank=True)
    clave = models.CharField(max_length=255, unique=True, null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def get_ubicacion(self):
        return str(self.ubicacionobj)


class Recepcion(WorkflowMixin, AlmacenTrack):
    """Recepcion de mercaderia. El stock entra a la ubicacion de cada linea recien al aprobarse."""
    WORKFLOW_EVENT = 'almacen.recepcion'

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField(db_index=True)
    bodegaobj = models.ForeignKey(Bodega, on_delete=models.PROTECT)
    proveedor = models.CharField(max_length=300, blank=True, default='')
    documento_ref = models.CharField(max_length=120, blank=True, default='', help_text='Remisión / factura del proveedor')
    orden_compra_ref = models.CharField(max_length=60, blank=True, default='')
    observacion = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('recepcion_verificado', 'Verificar recepción'), ('recepcion_aprobado', 'Aprobar recepción'),
                       ('recepcion_anulado', 'Anular recepción')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='almacen_recepcion_numero_unico')]

    def __str__(self):
        return f"Recepción {self.numero}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    def workflow_validar(self, estado):
        if estado in ('verificado', 'aprobado') and not self.detalles.filter(cantidad_recibida__gt=0).exists():
            return "La recepción no tiene cantidades recibidas"
        if estado == 'anulado' and self.estado == self.estado_final:
            for d in self.detalles.filter(cantidad_recibida__gt=0):
                if stock_en_ubicacion(d.productoobj, d.ubicacionobj) < d.cantidad_recibida:
                    return f"{d.productoobj.descripcion}: la mercadería ya se movió o despachó de {d.ubicacionobj}; trasládela de vuelta para anular"
        return ''

    def workflow_on_enter(self, estado, userobj):
        aprobada = self.estado == self.estado_final
        for d in self.detalles.filter(cantidad_recibida__gt=0).select_related('productoobj', 'ubicacionobj'):
            if estado == 'aprobado':
                mover_stock(self.businessobj, d.productoobj, d.ubicacionobj, d.cantidad_recibida, 'recepcion',
                            f"Recepción {self.get_numero_display()} {self.proveedor}".strip(), costo_unitario=d.costo_unitario,
                            origen=self, clave=f"almacen.recepcion:{self.pk}:{d.pk}", userobj=userobj)
                if d.costo_unitario > 0:
                    type(d.productoobj).objects.filter(pk=d.productoobj_id).update(costo=d.costo_unitario)
            if estado == 'anulado' and aprobada:
                mover_stock(self.businessobj, d.productoobj, d.ubicacionobj, -d.cantidad_recibida, 'reverso',
                            f"Anulación recepción {self.get_numero_display()}", origen=self,
                            clave=f"almacen.recepcion:{self.pk}:{d.pk}:reverso", userobj=userobj)

    def get_workflow_payload(self):
        return {'numero': self.numero, 'fecha': str(self.fecha), 'proveedor': self.proveedor, 'documento': self.documento_ref,
                'lineas': [{'producto_id': d.productoobj_id, 'cantidad': str(d.cantidad_recibida), 'costo': str(d.costo_unitario)}
                           for d in self.detalles.all()]}


class RecepcionDetalle(models.Model):
    recepcionobj = models.ForeignKey(Recepcion, on_delete=models.CASCADE, related_name='detalles')
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    ubicacionobj = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    cantidad_esperada = models.DecimalField(**CCT, default=0)
    cantidad_recibida = models.DecimalField(**CCT)
    costo_unitario = models.DecimalField(**CCT, default=0)
    lote = models.CharField(max_length=80, blank=True, default='')
    vencimiento = models.DateField(null=True, blank=True)


class AjusteStock(WorkflowMixin, AlmacenTrack):
    """Conteo fisico de un producto en una ubicacion. Al aprobarse lleva el stock a lo contado."""
    WORKFLOW_EVENT = 'almacen.ajuste'

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField()
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    ubicacionobj = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    cantidad_sistema = models.DecimalField(**CCT, default=0)
    cantidad_contada = models.DecimalField(**CCT)
    motivo = models.CharField(max_length=300)

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('ajustestock_verificado', 'Verificar ajuste'), ('ajustestock_aprobado', 'Aprobar ajuste'),
                       ('ajustestock_anulado', 'Anular ajuste')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='almacen_ajuste_numero_unico')]

    def get_producto(self):
        return self.productoobj.descripcion

    def get_ubicacion(self):
        return str(self.ubicacionobj)

    def workflow_validar(self, estado):
        if estado == 'anulado' and self.estado == self.estado_final:
            return "Un ajuste aprobado no se anula: cargue un nuevo conteo"
        return ''

    def workflow_on_enter(self, estado, userobj):
        if estado == 'aprobado':
            diferencia = self.cantidad_contada - stock_en_ubicacion(self.productoobj, self.ubicacionobj)
            if diferencia:
                mover_stock(self.businessobj, self.productoobj, self.ubicacionobj, diferencia, 'ajuste',
                            f"Ajuste {self.numero}: {self.motivo}", origen=self, clave=f"almacen.ajuste:{self.pk}", userobj=userobj)


# =====================================================================================
# Motor de stock (vive junto a los modelos porque sus hooks de workflow lo usan)
# =====================================================================================

def stock_en_ubicacion(productoobj, ubicacionobj) -> Decimal:
    fila = StockUbicacion.objects.filter(productoobj=productoobj, ubicacionobj=ubicacionobj).first()
    return fila.cantidad if fila else Decimal(0)


@precision_monetaria
def stock_fisico_vendible(businessobj, productoobj) -> Decimal:
    return StockUbicacion.objects.filter(
        businessobj=businessobj, productoobj=productoobj, ubicacionobj__activo=True,
        ubicacionobj__tipo__in=list(Ubicacion.PRIORIDAD_DESPACHO)).aggregate(t=Sum('cantidad'))['t'] or Decimal(0)


@precision_monetaria
def stock_disponible(businessobj, productoobj) -> Decimal:
    """Stock vendible (picking/almacenaje/recepcion) menos lo reservado por pedidos sin despachar."""
    fisico = StockUbicacion.objects.filter(
        businessobj=businessobj, productoobj=productoobj, ubicacionobj__activo=True,
        ubicacionobj__tipo__in=list(Ubicacion.PRIORIDAD_DESPACHO)).aggregate(t=Sum('cantidad'))['t'] or Decimal(0)
    reservado = ReservaStock.objects.filter(businessobj=businessobj, productoobj=productoobj, activa=True).aggregate(
        t=Sum('cantidad'))['t'] or Decimal(0)
    return fisico - reservado


@precision_monetaria
def mover_stock(businessobj, productoobj, ubicacionobj, cantidad, tipo, concepto, costo_unitario=0,
                origen=None, clave=None, userobj=None) -> MovimientoStock:
    """
    Unico punto que modifica stock. `cantidad` positiva entra, negativa sale. Con `clave`, repetir la
    llamada devuelve el movimiento existente (idempotente). Nunca deja stock negativo.
    """
    cantidad = Decimal(str(cantidad))
    if ubicacionobj.businessobj_id != businessobj.pk:
        raise AlmacenError("La ubicación no pertenece al negocio")
    with transaction.atomic():
        if clave:
            existente = MovimientoStock.objects.filter(clave=clave).first()
            if existente:
                return existente
        fila, _ = StockUbicacion.objects.select_for_update().get_or_create(
            productoobj=productoobj, ubicacionobj=ubicacionobj, defaults={'businessobj': businessobj})
        if fila.cantidad + cantidad < 0:
            raise AlmacenError(f"Stock insuficiente de {productoobj.descripcion} en {ubicacionobj}: hay {fila.cantidad:,.2f}")
        fila.cantidad = fila.cantidad + cantidad
        fila.save(update_fields=['cantidad'])
        mov = MovimientoStock.objects.create(
            businessobj=businessobj, productoobj=productoobj, ubicacionobj=ubicacionobj, tipo=tipo, cantidad=cantidad,
            saldo=fila.cantidad, costo_unitario=costo_unitario or 0, concepto=concepto[:300], clave=clave,
            origen_app=origen._meta.app_label if origen else '', origen_model=origen._meta.model_name if origen else '',
            origen_id=origen.pk if origen else None, cargado_usuario=user_label(userobj))
        # El maestro de productos del core refleja el stock total
        total = StockUbicacion.objects.filter(productoobj=productoobj).aggregate(t=Sum('cantidad'))['t'] or 0
        type(productoobj).objects.filter(pk=productoobj.pk).update(stock=total)
    return mov


@precision_monetaria
def reservar(businessobj, productoobj, cantidad, origen) -> str:
    """Reserva stock para `origen` (un pedido). Devuelve '' o el motivo por el que no se pudo. Idempotente por origen."""
    cantidad = Decimal(str(cantidad))
    with transaction.atomic():
        type(productoobj).objects.select_for_update().get(pk=productoobj.pk)
        llaves = dict(productoobj=productoobj, origen_app=origen._meta.app_label, origen_model=origen._meta.model_name, origen_id=origen.pk)
        if ReservaStock.objects.filter(activa=True, **llaves).exists():
            return ''
        disponible = stock_disponible(businessobj, productoobj)
        if cantidad > disponible:
            return f"{productoobj.descripcion}: quedan {disponible:,.0f} disponibles"
        ReservaStock.objects.update_or_create(defaults={'businessobj': businessobj, 'cantidad': cantidad, 'activa': True}, **llaves)
    return ''


def liberar_reservas(origen):
    ReservaStock.objects.filter(origen_app=origen._meta.app_label, origen_model=origen._meta.model_name,
                                origen_id=origen.pk, activa=True).update(activa=False)


@precision_monetaria
def despachar(businessobj, productoobj, cantidad, origen, concepto, userobj=None) -> list:
    """
    Saca `cantidad` del stock vendible recorriendo picking -> almacenaje -> recepcion, y consume la reserva
    del origen. Idempotente: si el origen ya despacho ese producto no vuelve a descontar.
    """
    base = f"almacen.despacho:{origen._meta.label_lower}:{origen.pk}:{productoobj.pk}"
    if MovimientoStock.objects.filter(clave__startswith=base).exists():
        return []
    pendiente, movimientos = Decimal(str(cantidad)), []
    with transaction.atomic():
        filas = list(StockUbicacion.objects.select_for_update().filter(
            businessobj=businessobj, productoobj=productoobj, cantidad__gt=0, ubicacionobj__activo=True,
            ubicacionobj__tipo__in=list(Ubicacion.PRIORIDAD_DESPACHO)).select_related('ubicacionobj'))
        filas.sort(key=lambda f: (Ubicacion.PRIORIDAD_DESPACHO[f.ubicacionobj.tipo], f.ubicacionobj.codigo))
        if sum(f.cantidad for f in filas) < pendiente:
            raise AlmacenError(f"Stock insuficiente de {productoobj.descripcion} para despachar {pendiente:,.2f}")
        for fila in filas:
            if pendiente <= 0:
                break
            tomar = min(fila.cantidad, pendiente)
            movimientos.append(mover_stock(businessobj, productoobj, fila.ubicacionobj, -tomar, 'despacho', concepto,
                                           origen=origen, clave=f"{base}:{fila.ubicacionobj_id}", userobj=userobj))
            pendiente -= tomar
        ReservaStock.objects.filter(productoobj=productoobj, origen_app=origen._meta.app_label,
                                    origen_model=origen._meta.model_name, origen_id=origen.pk).update(activa=False)
    return movimientos
