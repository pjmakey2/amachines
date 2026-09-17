"""Plugin de Almacen (warehouse): recepcion de mercaderia, almacenaje por ubicacion, ajustes y libro de stock."""
from typing import Dict, List

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    name = "almacen"
    display_name = "Almacén"
    description = "Bodegas y ubicaciones, recepción de mercadería, almacenaje, ajustes de inventario y reservas de stock"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen']
    icon = "mdi mdi-warehouse"
    category = "inventario"

    def get_menus(self) -> List[Dict]:
        def item(app, nombre, icon, tmpl, prio, bg='#075985'):
            return {'app_name': app, 'friendly_name': nombre, 'icon': icon, 'url': f'Almacen/{tmpl}', 'prioridad': prio, 'background': bg}
        return [{
            'menu': 'Almacén',
            'menu_icon': 'mdi mdi-warehouse',
            'prioridad': 35,
            'items': [
                item('almacen_recepciones', 'Recepción de Mercadería', 'mdi mdi-truck-delivery-outline', 'RecepcionUi.html', 1),
                item('almacen_stock', 'Stock por Ubicación', 'mdi mdi-package-variant-closed', 'StockUbicacionUi.html', 2),
                item('almacen_movimientos', 'Movimientos de Stock', 'mdi mdi-swap-horizontal', 'MovimientoStockUi.html', 3),
                item('almacen_ajustes', 'Ajustes de Inventario', 'mdi mdi-clipboard-edit-outline', 'AjusteStockUi.html', 4),
                item('almacen_ubicaciones', 'Ubicaciones', 'mdi mdi-map-marker-outline', 'UbicacionUi.html', 5, '#0C4A6E'),
                item('almacen_bodegas', 'Bodegas', 'mdi mdi-warehouse', 'BodegaUi.html', 6, '#0C4A6E'),
            ],
        }]
