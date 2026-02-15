### Creacion de menu del sidebar.

Se lee el modelo Apps para crear este arbol.

Por ejemplo la entrada.

entry = {
    'prioridad': 100,
    'menu': 'Maestros', #Lo que pongas aqui ya creara la entrada de menu automaticmanete.
    'app_name': 'PorcentajeIva',
    'friendly_name': 'Porcentajes IVA',
    'icon': 'mdi mdi-percent',
    'url': 'Sifen/PorcentajeIvaUi.html',
    'version': 1,
    'background': '#FFFFFF',
    'active': True,
},


Creara la carpeta de Menu "Maestros" y dentro de ella la opcion PorcentajeIva,

Asi por cada registro encontrado en Apps.

entry = {
    'prioridad': 100,
    'menu': 'Maestros', #Lo que pongas aqui ya creara la entrada de menu automaticmanete.
    'app_name': 'Producto',
    'friendly_name': 'Productos',
    'icon': 'mdi mdi-product',
    'url': 'Sifen/ProductoUi.html',
    'version': 1,
    'background': '#FFFFFF',
    'active': True,
},

Este anhadiri la app Producto al menu Maestros

