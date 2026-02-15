from django.contrib import admin

# Register your models here.
from .models import DocumentHeader, DocumentDetail, TrackLote, Ciudades, Departamentos, Paises, Business, Retencion

admin.site.register(DocumentHeader)
admin.site.register(DocumentDetail)
admin.site.register(TrackLote)
admin.site.register(Ciudades)
admin.site.register(Departamentos)
admin.site.register(Paises)
admin.site.register(Business)
admin.site.register(Retencion)