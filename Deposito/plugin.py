"""Plugin de Depositos: control y carga de depositos bancarios (efectivo, cheques, transferencias, tarjetas)."""
from typing import Dict, List

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    name = "deposito"
    display_name = "Depósitos"
    description = "Depósitos bancarios; el cierre de un cobro genera sus depósitos pendientes automáticamente"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen', 'tesoreria']
    icon = "mdi mdi-bank-transfer-in"
    category = "finanzas"

    def get_menus(self) -> List[Dict]:
        return [{
            'menu': 'Tesorería',
            'menu_icon': 'mdi mdi-bank',
            'prioridad': 25,
            'items': [{'app_name': 'deposito_depositos', 'friendly_name': 'Depósitos', 'icon': 'mdi mdi-bank-transfer-in',
                       'url': 'Deposito/DepositoUi.html', 'prioridad': 8, 'background': '#0F766E'}],
        }]

    def get_event_handlers(self) -> Dict[str, List[str]]:
        return {'cobro.recibo.aprobado': ['Deposito.handlers.generar_depositos_de_cobro']}
