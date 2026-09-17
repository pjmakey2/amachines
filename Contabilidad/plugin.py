"""
Plugin de Contabilidad: plan de cuentas por plantillas, asientos automaticos desde el cierre de
ventas, cobros, depositos y egresos, libros contables, estado de resultados y RG90.
Ningun plugin depende de Contabilidad: solo escucha eventos.
"""
from typing import Dict, List

from OptsIO.plugin_manager import BasePlugin


class Plugin(BasePlugin):
    name = "contabilidad"
    display_name = "Contabilidad"
    description = "Plan de cuentas, asientos automáticos, libros, estado de resultados y RG90"
    version = "1.0.0"
    author = "Alta Machines"
    is_core = False
    dependencies = ['sifen']
    icon = "mdi mdi-book-open-page-variant"
    category = "finanzas"

    def get_menus(self) -> List[Dict]:
        def item(app, nombre, icon, tmpl, prio, bg='#3730A3'):
            return {'app_name': app, 'friendly_name': nombre, 'icon': icon, 'url': f'Contabilidad/{tmpl}',
                    'prioridad': prio, 'background': bg}
        return [{
            'menu': 'Contabilidad',
            'menu_icon': 'mdi mdi-book-open-page-variant',
            'prioridad': 30,
            'items': [
                item('conta_asientos', 'Asientos', 'mdi mdi-book-edit-outline', 'AsientoUi.html', 1),
                item('conta_reportes', 'Libros y Reportes', 'mdi mdi-chart-box-outline', 'ReportesUi.html', 2),
                item('conta_rg90', 'RG90 / Libros IVA', 'mdi mdi-file-export-outline', 'Rg90Ui.html', 3),
                item('conta_plan', 'Plan de Cuentas', 'mdi mdi-file-tree', 'PlanCuentaUi.html', 4, '#312E81'),
                item('conta_formatos', 'Formatos de Asiento', 'mdi mdi-format-list-text', 'FormatoAsientoUi.html', 5, '#312E81'),
                item('conta_config', 'Configuración Contable', 'mdi mdi-cog-outline', 'ConfigContableUi.html', 6, '#312E81'),
            ],
        }]

    def get_event_handlers(self) -> Dict[str, List[str]]:
        return {
            'sifen.documento.aprobado': ['Contabilidad.handlers.asiento_venta'],
            'sifen.documento.cancelado': ['Contabilidad.handlers.reverso'],
            'cobro.recibo.aprobado': ['Contabilidad.handlers.asiento_cobro'],
            'deposito.deposito.aprobado': ['Contabilidad.handlers.asiento_deposito'],
            'egreso.gasto.aprobado': ['Contabilidad.handlers.asiento_gasto'],
            'egreso.gasto.rendido': ['Contabilidad.handlers.asiento_gasto_rendido'],
            'egreso.pago.aprobado': ['Contabilidad.handlers.asiento_pago'],
            'egreso.transferencia.aprobado': ['Contabilidad.handlers.asiento_transferencia'],
            '*.anulado': ['Contabilidad.handlers.reverso'],
        }
