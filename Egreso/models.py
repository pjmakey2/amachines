import math
from datetime import datetime
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from num2words import num2words

from OptsIO.io_business import user_label
from OptsIO.io_money import precision_monetaria
from OptsIO.workflow import WorkflowMixin
from Tesoreria.mng_tesoreria import MTesoreria
from Tesoreria.models import Cheque, MovimientoTesoreria


class OrdenCompra(models.Model):
    cct = {'max_digits': 19, 'decimal_places': 6}
    cd_char = {'max_length': 120, 'null': True}
    oc_numero = models.BigIntegerField(default=0)
    oc_fecha = models.DateField()
    oc_estado = models.CharField(max_length=30, default='CREADO')
    oc_estado_pago = models.CharField(max_length=30, default='PENDIENTE')  # PENDIENTE, PARCIAL, PAGADO
    oc_moneda = models.CharField(max_length=10, default='GS')
    oc_condicion = models.CharField(max_length=30, default='Contado')
    oc_condicion_cod = models.IntegerField(default=1)
    oc_vencimiento = models.DateField(null=True)
    oc_cantidad_cuotas = models.IntegerField(default=0)
    oc_interes_pct = models.DecimalField(**cct, default=0)
    oc_interes_monto = models.DecimalField(**cct, default=0)
    oc_observacion = models.CharField(max_length=500, null=True, blank=True)
    # Totales
    oc_total = models.DecimalField(**cct, default=0)
    oc_pagado = models.DecimalField(**cct, default=0)
    oc_saldo = models.DecimalField(**cct, default=0)
    oc_iva = models.DecimalField(**cct, default=0)
    oc_exenta = models.DecimalField(**cct, default=0)
    oc_g10 = models.DecimalField(**cct, default=0)
    oc_i10 = models.DecimalField(**cct, default=0)
    oc_g5 = models.DecimalField(**cct, default=0)
    oc_i5 = models.DecimalField(**cct, default=0)
    oc_descuento = models.DecimalField(**cct, default=0)
    oc_descuento_global = models.DecimalField(**cct, default=0)
    tasa_cambio = models.DecimalField(**cct, default=1)
    # Proveedor
    prov_ruc = models.CharField(max_length=120)
    prov_ruc_dv = models.IntegerField(default=0)
    prov_nombre = models.CharField(max_length=300)
    prov_celular = models.CharField(max_length=30, null=True)
    prov_email = models.CharField(max_length=120, null=True)
    prov_direccion = models.CharField(max_length=300, null=True)
    prov_tipocontribuyente = models.CharField(max_length=120, null=True)
    prov_type_business = models.CharField(max_length=120, null=True, default='B2B')
    # Business
    bs = models.CharField(max_length=60, null=True)
    bs_ruc = models.CharField(max_length=120, null=True)
    # PDF
    oc_pdf_file = models.FileField(upload_to='oc', max_length=500, null=True)
    # Audit
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(**cd_char)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(**cd_char)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(**cd_char)

    def get_numero_display(self):
        return str(self.oc_numero).zfill(7)

    def get_total_venta(self):
        return self.oc_total

    def get_total_venta_gs(self):
        if self.oc_moneda == 'USD':
            return Decimal(self.oc_total) * Decimal(self.tasa_cambio)
        return self.oc_total

    def get_total_ventaword(self):
        if self.oc_moneda == 'GS':
            total_venta = int(self.get_total_venta())
            return num2words(total_venta, lang='es').upper()
        if self.oc_moneda == 'USD':
            total_venta = self.get_total_venta()
            return num2words(total_venta, lang='es', to='currency').upper().replace('EUROS', '')
        return 'ND'

    def get_ordencompradetail(self):
        return self.ordencompradetail_set.filter(anulado=False)

    def get_total_exenta(self):
        return self.ordencompradetail_set.filter(anulado=False).aggregate(t=Sum('exenta'))['t'] or 0

    def get_total_gravada_5(self):
        return self.ordencompradetail_set.filter(anulado=False).aggregate(t=Sum('gravada_5'))['t'] or 0

    def get_total_gravada_10(self):
        return self.ordencompradetail_set.filter(anulado=False).aggregate(t=Sum('gravada_10'))['t'] or 0

    def get_ivas_5_master(self):
        return self.ordencompradetail_set.filter(anulado=False).aggregate(t=Sum('iva_5'))['t'] or 0

    def get_ivas_10_master(self):
        return self.ordencompradetail_set.filter(anulado=False).aggregate(t=Sum('iva_10'))['t'] or 0

    def get_ivas_master(self):
        return self.get_ivas_5_master() + self.get_ivas_10_master()


class OrdenCompraDetail(models.Model):
    cct = {'max_digits': 19, 'decimal_places': 6, 'default': 0}
    ordencompraobj = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE)
    prod_autocreado = models.BooleanField(default=False)
    prod_cod = models.IntegerField()
    prod_descripcion = models.CharField(max_length=500)
    prod_unidad_medida = models.IntegerField(default=77)
    prod_unidad_medida_desc = models.CharField(max_length=20, default='UNI')
    porcentaje_iva = models.IntegerField(default=10)
    precio_unitario = models.DecimalField(max_digits=19, decimal_places=6)
    cantidad = models.DecimalField(max_digits=19, decimal_places=6)
    exenta_pct = models.DecimalField(**cct)
    g5_pct = models.DecimalField(**cct)
    g10_pct = models.DecimalField(**cct)
    exenta = models.DecimalField(**cct)
    iva_5 = models.DecimalField(**cct)
    gravada_5 = models.DecimalField(**cct)
    base_gravada_5 = models.DecimalField(**cct)
    iva_10 = models.DecimalField(**cct)
    gravada_10 = models.DecimalField(**cct)
    base_gravada_10 = models.DecimalField(**cct)
    descuento = models.DecimalField(**cct)
    per_descuento = models.DecimalField(**cct)
    observacion = models.CharField(max_length=245, null=True)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado = models.BooleanField(default=False)

    def get_cantidad(self):
        if self.cantidad != math.floor(self.cantidad):
            return round(float(self.cantidad), 2)
        return int(self.cantidad)


class OrdenCompraCuota(models.Model):
    ordencompraobj = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='cuotas')
    cuota_numero = models.IntegerField(default=1)
    monto = models.DecimalField(max_digits=19, decimal_places=6, default=0)
    monto_pagado = models.DecimalField(max_digits=19, decimal_places=6, default=0)
    estado = models.CharField(max_length=20, default='PENDIENTE')  # PENDIENTE/PARCIAL/PAGADO
    vencimiento = models.DateField()
    cargado_fecha = models.DateTimeField(auto_now_add=True)


class OrdenCompraPago(models.Model):
    ordencompraobj = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE, related_name='pagos')
    cuotaobj = models.ForeignKey(OrdenCompraCuota, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    monto = models.DecimalField(max_digits=19, decimal_places=6, default=0)
    fecha_pago = models.DateField()
    metodo_pago = models.CharField(max_length=50, default='Efectivo')
    referencia = models.CharField(max_length=120, null=True, blank=True)
    cargado_fecha = models.DateTimeField(auto_now_add=True)
    cargado_usuario = models.CharField(max_length=120, null=True)


# =====================================================================================
# Gastos, pagos a proveedores y transferencias internas (multi-tenant + workflow)
# =====================================================================================

MONEDAS = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]
CCT = {'max_digits': 19, 'decimal_places': 6}


class EgresoTrack(models.Model):
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        abstract = True


class Proveedor(EgresoTrack):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    ruc = models.CharField(max_length=30)
    ruc_dv = models.IntegerField(default=0)
    nombre = models.CharField(max_length=300)
    nombre_fantasia = models.CharField(max_length=300, blank=True, default='')
    direccion = models.CharField(max_length=300, blank=True, default='')
    telefono = models.CharField(max_length=60, blank=True, default='')
    email = models.CharField(max_length=120, blank=True, default='')
    contacto = models.CharField(max_length=120, blank=True, default='')
    # Datos para pagarle por transferencia
    banco_nombre = models.CharField(max_length=120, blank=True, default='')
    banco_cuenta = models.CharField(max_length=60, blank=True, default='')
    plazo_dias = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'ruc')
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.ruc}-{self.ruc_dv})"

    def get_descripcion(self):
        return str(self)

    @precision_monetaria
    def get_saldo_pendiente(self):
        return self.gasto_set.filter(anulado=False, estado='aprobado').aggregate(t=Sum('saldo'))['t'] or 0


class CategoriaGasto(EgresoTrack):
    """Concepto del gasto (alquiler, servicios, honorarios...). Contabilidad lo mapea a una cuenta."""
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class GastoRecurrente(EgresoTrack):
    """Definido en la ficha del proveedor: genera el Gasto automaticamente en cada fecha de aplicacion."""
    FRECUENCIAS = [('mensual', 'Mensual'), ('bimestral', 'Bimestral'), ('trimestral', 'Trimestral'),
                   ('semestral', 'Semestral'), ('anual', 'Anual')]
    MESES = {'mensual': 1, 'bimestral': 2, 'trimestral': 3, 'semestral': 6, 'anual': 12}

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    proveedorobj = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    categoriaobj = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)
    concepto = models.CharField(max_length=300)
    monto = models.DecimalField(**CCT)
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIAS, default='mensual')
    # Dia del mes en que se genera el gasto (si el mes es mas corto, el ultimo dia)
    dia_aplicacion = models.IntegerField(default=1)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    proxima_fecha = models.DateField(db_index=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['proxima_fecha']

    def __str__(self):
        return f"{self.concepto} - {self.proveedorobj.nombre} ({self.get_frecuencia_display()})"


class Gasto(WorkflowMixin, EgresoTrack):
    """
    comun:      gasto con factura en mano (puede venir de un GastoRecurrente).
    a_rendir:   sin factura aun, contra presupuesto; se entrega el dinero y luego se rinde.
    caja_chica: gasto menor pagado desde una caja chica; se paga solo al aprobarse.
    """
    WORKFLOW_EVENT = 'egreso.gasto'
    TIPOS = [('comun', 'Gasto común'), ('a_rendir', 'Gasto a rendir'), ('caja_chica', 'Caja chica')]
    ESTADOS_PAGO = [('PENDIENTE', 'Pendiente'), ('PARCIAL', 'Parcial'), ('PAGADO', 'Pagado')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    tipo = models.CharField(max_length=20, choices=TIPOS, default='comun', db_index=True)
    fecha = models.DateField(db_index=True)
    proveedorobj = models.ForeignKey(Proveedor, on_delete=models.PROTECT, null=True, blank=True)
    beneficiario = models.CharField(max_length=200, blank=True, default='')
    categoriaobj = models.ForeignKey(CategoriaGasto, on_delete=models.PROTECT)
    concepto = models.CharField(max_length=300)
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    tasa_cambio = models.DecimalField(**CCT, default=1)
    # Comprobante (en a_rendir se completa al rendir)
    factura_numero = models.CharField(max_length=30, blank=True, default='')
    factura_timbrado = models.CharField(max_length=20, blank=True, default='')
    factura_fecha = models.DateField(null=True, blank=True)
    factura_condicion = models.CharField(max_length=20, default='contado')
    vencimiento = models.DateField(null=True, blank=True)
    exenta = models.DecimalField(**CCT, default=0)
    gravada_5 = models.DecimalField(**CCT, default=0)
    gravada_10 = models.DecimalField(**CCT, default=0)
    iva_5 = models.DecimalField(**CCT, default=0)
    iva_10 = models.DecimalField(**CCT, default=0)
    total = models.DecimalField(**CCT, default=0)
    archivo = models.FileField(upload_to='egreso/gastos', max_length=500, null=True, blank=True)
    # A rendir
    presupuesto_monto = models.DecimalField(**CCT, default=0)
    presupuesto_ref = models.CharField(max_length=120, blank=True, default='')
    responsable = models.CharField(max_length=120, blank=True, default='')
    rendido = models.BooleanField(default=False)
    rendido_fecha = models.DateTimeField(null=True, blank=True)
    rendido_usuario = models.CharField(max_length=120, null=True, blank=True)
    # Caja chica
    cajaobj = models.ForeignKey('Tesoreria.Caja', on_delete=models.PROTECT, null=True, blank=True)
    # Recurrente: (recurrenteobj, periodo) unico => la generacion automatica es idempotente
    recurrenteobj = models.ForeignKey(GastoRecurrente, on_delete=models.SET_NULL, null=True, blank=True)
    periodo = models.CharField(max_length=10, blank=True, default='')
    # Pago
    pagado = models.DecimalField(**CCT, default=0)
    saldo = models.DecimalField(**CCT, default=0)
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='PENDIENTE', db_index=True)

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('gasto_verificado', 'Verificar gasto'), ('gasto_aprobado', 'Aprobar gasto'),
                       ('gasto_anulado', 'Anular gasto')]
        constraints = [
            models.UniqueConstraint(fields=['businessobj', 'numero'], name='egreso_gasto_numero_unico'),
            models.UniqueConstraint(fields=['recurrenteobj', 'periodo'], name='egreso_gasto_recurrente_periodo',
                                    condition=models.Q(recurrenteobj__isnull=False)),
        ]

    def __str__(self):
        return f"Gasto {self.numero} - {self.concepto}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    def get_beneficiario(self):
        return self.proveedorobj.nombre if self.proveedorobj_id else self.beneficiario

    @property
    def monto_a_pagar(self):
        """En a_rendir sin rendir se paga el presupuesto; en el resto, el total del comprobante."""
        if self.tipo == 'a_rendir' and not self.rendido:
            return self.presupuesto_monto
        return self.total

    @precision_monetaria
    def recalcular_pago(self):
        self.saldo = self.monto_a_pagar - self.pagado
        self.estado_pago = 'PAGADO' if self.saldo <= 0 and self.pagado > 0 else ('PARCIAL' if self.pagado > 0 else 'PENDIENTE')

    def get_workflow_payload(self):
        return {'numero': self.numero, 'fecha': str(self.fecha), 'tipo': self.tipo, 'concepto': self.concepto,
                'beneficiario': self.get_beneficiario(), 'moneda': self.moneda, 'tasa_cambio': str(self.tasa_cambio),
                'total': str(self.total), 'exenta': str(self.exenta), 'gravada_5': str(self.gravada_5),
                'gravada_10': str(self.gravada_10), 'iva_5': str(self.iva_5), 'iva_10': str(self.iva_10),
                'categoria_id': self.categoriaobj_id, 'proveedor_id': self.proveedorobj_id, 'caja_id': self.cajaobj_id}

    def workflow_validar(self, estado):
        if estado == 'anulado' and self.pagado > 0 and self.tipo != 'caja_chica':
            return "El gasto tiene pagos aplicados: anule primero los pagos"
        if estado == 'aprobado':
            if self.monto_a_pagar <= 0:
                return "El gasto no tiene monto"
            if self.tipo == 'comun' and not self.factura_numero:
                return "Un gasto común requiere el número de factura"
            if self.tipo == 'caja_chica':
                if not self.cajaobj_id:
                    return "Indique la caja chica que paga el gasto"
                return MTesoreria().validar_movimiento('egreso', self.total, cajaobj=self.cajaobj)
        return ''

    def workflow_on_enter(self, estado, userobj):
        if estado == 'aprobado':
            self.recalcular_pago()
            if self.tipo == 'caja_chica':
                MTesoreria().registrar_movimiento(
                    self.businessobj, self.fecha, 'egreso', self.total, f"Caja chica: {self.concepto}",
                    cajaobj=self.cajaobj, referencia=self.factura_numero, origen=self,
                    clave=f"egreso.gasto:{self.pk}:caja_chica", userobj=userobj)
                self.pagado = self.total
                self.recalcular_pago()
            self.save(update_fields=['pagado', 'saldo', 'estado_pago'])
        if estado == 'anulado' and self.tipo == 'caja_chica':
            MovimientoTesoreria.objects.filter(clave=f"egreso.gasto:{self.pk}:caja_chica").update(
                anulado=True, anulado_fecha=datetime.now(), anulado_usuario=user_label(userobj))
            self.pagado = 0
            self.recalcular_pago()
            self.save(update_fields=['pagado', 'saldo', 'estado_pago'])


class PagoProveedor(WorkflowMixin, EgresoTrack):
    """Pago de uno o varios gastos aprobados. Al aprobarse emite el cheque (si aplica) y mueve los fondos."""
    WORKFLOW_EVENT = 'egreso.pago'
    MEDIOS = [('efectivo', 'Efectivo (caja)'), ('transferencia', 'Transferencia bancaria'), ('cheque', 'Cheque')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField(db_index=True)
    proveedorobj = models.ForeignKey(Proveedor, on_delete=models.PROTECT, null=True, blank=True)
    beneficiario = models.CharField(max_length=200)
    medio = models.CharField(max_length=20, choices=MEDIOS)
    cajaobj = models.ForeignKey('Tesoreria.Caja', on_delete=models.PROTECT, null=True, blank=True)
    cuentaobj = models.ForeignKey('Tesoreria.CuentaBancaria', on_delete=models.PROTECT, null=True, blank=True)
    chequeraobj = models.ForeignKey('Tesoreria.Chequera', on_delete=models.PROTECT, null=True, blank=True)
    chequeobj = models.ForeignKey('Tesoreria.Cheque', on_delete=models.PROTECT, null=True, blank=True)
    cheque_fecha_pago = models.DateField(null=True, blank=True)
    referencia = models.CharField(max_length=120, blank=True, default='')
    moneda = models.CharField(max_length=4, choices=MONEDAS, default='PYG')
    total = models.DecimalField(**CCT, default=0)
    observacion = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('pagoproveedor_verificado', 'Verificar pago a proveedor'),
                       ('pagoproveedor_aprobado', 'Aprobar pago a proveedor'),
                       ('pagoproveedor_anulado', 'Anular pago a proveedor')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='egreso_pago_numero_unico')]

    def __str__(self):
        return f"Pago {self.numero} - {self.beneficiario}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    def get_origen_fondos(self):
        return str(self.cajaobj or self.cuentaobj or (self.chequeraobj.cuentaobj if self.chequeraobj_id else ''))

    def get_cheque_numero(self):
        return self.chequeobj.numero if self.chequeobj_id else ''

    def get_total_word(self):
        return num2words(int(self.total), lang='es').upper()

    def get_workflow_payload(self):
        cuenta_id = self.chequeraobj.cuentaobj_id if self.chequeraobj_id else self.cuentaobj_id
        return {'numero': self.numero, 'fecha': str(self.fecha), 'beneficiario': self.beneficiario, 'medio': self.medio,
                'total': str(self.total), 'moneda': self.moneda, 'proveedor_id': self.proveedorobj_id,
                'cuenta_id': cuenta_id, 'caja_id': self.cajaobj_id,
                'gastos': [{'gasto_id': d.gastoobj_id, 'monto': str(d.monto), 'tipo': d.gastoobj.tipo}
                           for d in self.detalles.select_related('gastoobj')]}

    def _clave(self):
        return f"egreso.pago:{self.pk}"

    def workflow_validar(self, estado):
        if estado == 'anulado':
            if self.chequeobj_id and self.chequeobj.estado == 'cobrado':
                return "El cheque del pago ya fue cobrado"
            return ''
        if estado != 'aprobado':
            return ''
        detalles = list(self.detalles.select_related('gastoobj'))
        if not detalles:
            return "El pago no tiene gastos asignados"
        for d in detalles:
            g = d.gastoobj
            if g.anulado or g.estado != 'aprobado':
                return f"El gasto {g.get_numero_display()} no esta aprobado"
            if d.monto > g.saldo:
                return f"El gasto {g.get_numero_display()} tiene saldo {g.saldo:,.0f} y se intenta pagar {d.monto:,.0f}"
        if self.medio == 'efectivo':
            if not self.cajaobj_id:
                return "Indique la caja que paga"
            return MTesoreria().validar_movimiento('egreso', self.total, cajaobj=self.cajaobj)
        if self.medio == 'transferencia' and not self.cuentaobj_id:
            return "Indique la cuenta bancaria que paga"
        if self.medio == 'cheque':
            if not self.chequeraobj_id:
                return "Indique la chequera"
            if not self.chequeraobj.activo or self.chequeraobj.disponibles < 1:
                return f"La chequera {self.chequeraobj} no tiene cheques disponibles"
            if self.chequeraobj.tipo == 'vista' and self.cheque_fecha_pago and self.cheque_fecha_pago != self.fecha:
                return "Una chequera a la vista no admite fecha de pago diferida"
        return ''

    def workflow_on_enter(self, estado, userobj):
        mt = MTesoreria()
        if estado == 'aprobado':
            cuenta = self.cuentaobj
            fecha_mov = self.fecha
            if self.medio == 'cheque':
                self.chequeobj = mt.emitir_cheque(
                    self.chequeraobj, self.beneficiario, self.total, self.fecha,
                    fecha_pago=self.cheque_fecha_pago or self.fecha,
                    concepto=f"Pago {self.get_numero_display()}", origen=self, userobj=userobj)
                self.save(update_fields=['chequeobj'])
                cuenta = self.chequeraobj.cuentaobj
                fecha_mov = self.chequeobj.fecha_pago
            mt.registrar_movimiento(
                self.businessobj, fecha_mov, 'egreso', self.total,
                f"Pago {self.get_numero_display()} a {self.beneficiario}",
                cuentaobj=cuenta if self.medio != 'efectivo' else None,
                cajaobj=self.cajaobj if self.medio == 'efectivo' else None,
                referencia=str(self.chequeobj.numero) if self.chequeobj_id else self.referencia,
                chequeobj=self.chequeobj, origen=self, clave=self._clave(), userobj=userobj)
            self._aplicar_a_gastos(1)
        if estado == 'anulado' and self.estado == self.estado_final:
            MovimientoTesoreria.objects.filter(clave=self._clave()).update(
                anulado=True, anulado_fecha=datetime.now(), anulado_usuario=user_label(userobj))
            if self.chequeobj_id:
                Cheque.objects.filter(pk=self.chequeobj_id).update(
                    estado='anulado', anulado_fecha=datetime.now(), anulado_usuario=user_label(userobj),
                    anulado_motivo=f"Anulacion del pago {self.get_numero_display()}")
            self._aplicar_a_gastos(-1)

    def _aplicar_a_gastos(self, signo):
        for d in self.detalles.select_related('gastoobj'):
            g = Gasto.objects.select_for_update().get(pk=d.gastoobj_id)
            g.pagado = g.pagado + signo * d.monto
            g.recalcular_pago()
            g.save(update_fields=['pagado', 'saldo', 'estado_pago'])


class PagoProveedorDetalle(models.Model):
    pagoobj = models.ForeignKey(PagoProveedor, on_delete=models.CASCADE, related_name='detalles')
    gastoobj = models.ForeignKey(Gasto, on_delete=models.PROTECT, related_name='pagos')
    monto = models.DecimalField(**CCT)

    class Meta:
        unique_together = ('pagoobj', 'gastoobj')


class TransferenciaInterna(WorkflowMixin, EgresoTrack):
    """Movimiento de fondos propios: banco->banco, banco->caja (reposicion de caja chica), caja->banco."""
    WORKFLOW_EVENT = 'egreso.transferencia'

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    numero = models.BigIntegerField(default=0)
    fecha = models.DateField(db_index=True)
    origen_cuentaobj = models.ForeignKey('Tesoreria.CuentaBancaria', on_delete=models.PROTECT, null=True, blank=True, related_name='transferencias_salida')
    origen_cajaobj = models.ForeignKey('Tesoreria.Caja', on_delete=models.PROTECT, null=True, blank=True, related_name='transferencias_salida')
    destino_cuentaobj = models.ForeignKey('Tesoreria.CuentaBancaria', on_delete=models.PROTECT, null=True, blank=True, related_name='transferencias_entrada')
    destino_cajaobj = models.ForeignKey('Tesoreria.Caja', on_delete=models.PROTECT, null=True, blank=True, related_name='transferencias_entrada')
    monto = models.DecimalField(**CCT)
    # Solo si origen y destino tienen distinta moneda
    monto_destino = models.DecimalField(**CCT, default=0)
    concepto = models.CharField(max_length=300, blank=True, default='')
    referencia = models.CharField(max_length=120, blank=True, default='')

    class Meta:
        ordering = ['-fecha', '-id']
        permissions = [('transferenciainterna_verificado', 'Verificar transferencia interna'),
                       ('transferenciainterna_aprobado', 'Aprobar transferencia interna'),
                       ('transferenciainterna_anulado', 'Anular transferencia interna')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='egreso_transf_numero_unico')]

    def __str__(self):
        return f"Transferencia {self.numero}: {self.get_origen()} -> {self.get_destino()}"

    def get_numero_display(self):
        return str(self.numero).zfill(7)

    def get_origen(self):
        return str(self.origen_cuentaobj or self.origen_cajaobj or '')

    def get_destino(self):
        return str(self.destino_cuentaobj or self.destino_cajaobj or '')

    def get_monto_destino(self):
        origen, destino = self.origen_cuentaobj or self.origen_cajaobj, self.destino_cuentaobj or self.destino_cajaobj
        return self.monto if origen.moneda == destino.moneda else self.monto_destino

    def get_workflow_payload(self):
        origen = self.origen_cuentaobj or self.origen_cajaobj
        return {'numero': self.numero, 'fecha': str(self.fecha), 'monto': str(self.monto), 'moneda': origen.moneda,
                'monto_destino': str(self.get_monto_destino()), 'origen': self.get_origen(), 'destino': self.get_destino(),
                'origen_cuenta_id': self.origen_cuentaobj_id, 'origen_caja_id': self.origen_cajaobj_id,
                'destino_cuenta_id': self.destino_cuentaobj_id, 'destino_caja_id': self.destino_cajaobj_id}

    def workflow_validar(self, estado):
        if estado != 'aprobado':
            return ''
        if bool(self.origen_cuentaobj_id) == bool(self.origen_cajaobj_id):
            return "Indique un origen: cuenta bancaria o caja"
        if bool(self.destino_cuentaobj_id) == bool(self.destino_cajaobj_id):
            return "Indique un destino: cuenta bancaria o caja"
        if (self.origen_cuentaobj_id and self.origen_cuentaobj_id == self.destino_cuentaobj_id) or \
                (self.origen_cajaobj_id and self.origen_cajaobj_id == self.destino_cajaobj_id):
            return "El origen y el destino no pueden ser el mismo"
        if self.get_monto_destino() <= 0:
            return "Origen y destino tienen distinta moneda: indique el monto que ingresa al destino"
        mt = MTesoreria()
        return (mt.validar_movimiento('egreso', self.monto, cuentaobj=self.origen_cuentaobj, cajaobj=self.origen_cajaobj)
                or mt.validar_movimiento('ingreso', self.get_monto_destino(), cuentaobj=self.destino_cuentaobj, cajaobj=self.destino_cajaobj))

    def workflow_on_enter(self, estado, userobj):
        mt = MTesoreria()
        clave = f"egreso.transferencia:{self.pk}"
        if estado == 'aprobado':
            texto = f"Transferencia {self.get_numero_display()}: {self.get_origen()} -> {self.get_destino()}"
            mt.registrar_movimiento(self.businessobj, self.fecha, 'egreso', self.monto, texto,
                                    cuentaobj=self.origen_cuentaobj, cajaobj=self.origen_cajaobj,
                                    referencia=self.referencia, origen=self, clave=f"{clave}:out", userobj=userobj)
            mt.registrar_movimiento(self.businessobj, self.fecha, 'ingreso', self.get_monto_destino(), texto,
                                    cuentaobj=self.destino_cuentaobj, cajaobj=self.destino_cajaobj,
                                    referencia=self.referencia, origen=self, clave=f"{clave}:in", userobj=userobj)
        if estado == 'anulado':
            MovimientoTesoreria.objects.filter(clave__in=[f"{clave}:out", f"{clave}:in"]).update(
                anulado=True, anulado_fecha=datetime.now(), anulado_usuario=user_label(userobj))
