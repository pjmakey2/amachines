"""
URL configuration for Amachine project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from OptsIO.views import base
from OptsIO.mng_setup import (
    setup_index, setup_validate_database, setup_step2, setup_finalize,
    setup_business, setup_reference_data_status
)

urlpatterns = [
    # Redirección de raíz a apps
    path('', RedirectView.as_view(url='/io/apps/', permanent=False), name='home'),

    path('admin/', admin.site.urls),

    # Setup routes (nivel raíz, sin prefijo)
    path('setup/', setup_index, name='setup_index'),
    path('setup/validate-db/', setup_validate_database, name='setup_validate_database'),
    path('setup/step2/', setup_step2, name='setup_step2'),
    path('setup/finalize/', setup_finalize, name='setup_finalize'),
    path('setup/business/', setup_business, name='setup_business'),
    path('setup/reference-data-status/', setup_reference_data_status, name='setup_reference_data_status'),

    # OptsIO URLs (incluye login, logout, api, etc.)
    path('io/', include('OptsIO.urls')),
]

# Servir archivos estáticos y media en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
