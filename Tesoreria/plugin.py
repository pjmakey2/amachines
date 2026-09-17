"""
Plugin de Tesoreria: bancos, cuentas bancarias, chequeras, cheques, cajas (con tope
para caja chica) y libro de movimientos. Base de Egreso, Deposito y Cobro.
"""
from typing import List, Dict

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    name = "tesoreria"
    display_name = "Tesorería"
    description = "Bancos, cuentas bancarias, chequeras, cajas y movimientos de fondos"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen']
    icon = "mdi mdi-bank"
    category = "finanzas"

    def get_menus(self) -> List[Dict]:
        def item(app, nombre, icon, tmpl, prio, bg):
            return {'app_name': app, 'friendly_name': nombre, 'icon': icon,
                    'url': f'Tesoreria/{tmpl}', 'prioridad': prio, 'background': bg}
        return [{
            'menu': 'Tesorería',
            'menu_icon': 'mdi mdi-bank',
            'prioridad': 25,
            'items': [
                item('tesoreria_saldos', 'Saldos', 'mdi mdi-scale-balance', 'SaldosUi.html', 1, '#0F766E'),
                item('tesoreria_movimientos', 'Movimientos', 'mdi mdi-swap-vertical', 'MovimientoTesoreriaUi.html', 2, '#0F766E'),
                item('tesoreria_cuentas', 'Cuentas Bancarias', 'mdi mdi-bank-outline', 'CuentaBancariaUi.html', 3, '#115E59'),
                item('tesoreria_chequeras', 'Chequeras', 'mdi mdi-checkbook', 'ChequeraUi.html', 4, '#115E59'),
                item('tesoreria_cheques', 'Cheques Emitidos', 'mdi mdi-file-sign', 'ChequeUi.html', 5, '#115E59'),
                item('tesoreria_cajas', 'Cajas', 'mdi mdi-cash-register', 'CajaUi.html', 6, '#134E4A'),
                item('tesoreria_bancos', 'Bancos', 'mdi mdi-domain', 'BancoUi.html', 7, '#134E4A'),
            ],
        }]
