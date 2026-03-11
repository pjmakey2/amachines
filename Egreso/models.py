import math
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from num2words import num2words


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
