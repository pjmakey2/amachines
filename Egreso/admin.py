from django.contrib import admin
from .models import OrdenCompra, OrdenCompraDetail, OrdenCompraCuota, OrdenCompraPago


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ['id', 'oc_numero', 'oc_fecha', 'prov_nombre', 'prov_ruc', 'oc_total', 'oc_saldo', 'oc_estado_pago']
    list_filter = ['oc_estado', 'oc_estado_pago', 'oc_moneda', 'oc_condicion']
    search_fields = ['prov_nombre', 'prov_ruc', 'oc_numero']
    date_hierarchy = 'oc_fecha'
