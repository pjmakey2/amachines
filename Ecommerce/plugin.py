"""Plugin de Ecommerce: tiendas online con temas (CSS propio), catalogo publicado desde el maestro de productos, carrito y pedidos."""
from typing import Dict, List

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    name = "ecommerce"
    display_name = "Tienda Online"
    description = "Tiendas públicas con temas, colecciones, carrito, pedidos con reserva de stock y facturación electrónica"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen', 'almacen']
    icon = "mdi mdi-storefront-outline"
    category = "ventas"

    def get_menus(self) -> List[Dict]:
        def item(app, nombre, icon, tmpl, prio, bg='#9D174D'):
            return {'app_name': app, 'friendly_name': nombre, 'icon': icon, 'url': f'Ecommerce/{tmpl}', 'prioridad': prio, 'background': bg}
        return [{
            'menu': 'Tienda Online',
            'menu_icon': 'mdi mdi-storefront-outline',
            'prioridad': 40,
            'items': [
                item('ecommerce_pedidos', 'Pedidos', 'mdi mdi-cart-check', 'PedidoUi.html', 1),
                item('ecommerce_productos', 'Productos Publicados', 'mdi mdi-tag-outline', 'ProductoTiendaUi.html', 2),
                item('ecommerce_colecciones', 'Colecciones', 'mdi mdi-shape-outline', 'ColeccionUi.html', 3),
                item('ecommerce_promos', 'Promociones de portada', 'mdi mdi-bullhorn-outline', 'PromoTiendaUi.html', 4),
                item('ecommerce_tiendas', 'Tiendas', 'mdi mdi-storefront-outline', 'TiendaUi.html', 5, '#831843'),
                item('ecommerce_temas', 'Temas (apariencia y CSS)', 'mdi mdi-palette-outline', 'TemaTiendaUi.html', 6, '#831843'),
            ],
        }]

    def get_event_handlers(self) -> Dict[str, List[str]]:
        return {'ecommerce.pedido.pagado': ['Ecommerce.handlers.facturar_pedido']}
