from django.urls import path

from Ecommerce import views

# Amachine/urls.py monta las URLs de cada plugin bajo su URL_PREFIX
URL_PREFIX = 'tienda/'

urlpatterns = [
    path('<slug:slug>/', views.home, name='ecommerce_home'),
    path('<slug:slug>/coleccion/<slug:coleccion_slug>/', views.coleccion, name='ecommerce_coleccion'),
    path('<slug:slug>/producto/<slug:producto_slug>/', views.producto, name='ecommerce_producto'),
    path('<slug:slug>/carrito/', views.carrito_ver, name='ecommerce_carrito'),
    path('<slug:slug>/carrito/agregar/', views.carrito_agregar, name='ecommerce_carrito_agregar'),
    path('<slug:slug>/carrito/actualizar/', views.carrito_actualizar, name='ecommerce_carrito_actualizar'),
    path('<slug:slug>/checkout/', views.checkout, name='ecommerce_checkout'),
    path('<slug:slug>/pedido/<uuid:token>/', views.pedido, name='ecommerce_pedido'),
]
