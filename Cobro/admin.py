from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'documentheaderobj', 'monto', 'fecha_pago', 'metodo_pago', 'cargado_fecha']
    list_filter = ['metodo_pago', 'fecha_pago']
    search_fields = ['documentheaderobj__doc_numero', 'numero_referencia']
    date_hierarchy = 'fecha_pago'
