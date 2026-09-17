import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

base = dict(pkg='mng_contabilidad', attr='MContabilidad')
TIPOS = [('activo', 'Activo'), ('pasivo', 'Pasivo'), ('patrimonio', 'Patrimonio Neto'), ('ingreso', 'Ingreso'), ('costo', 'Costo'), ('gasto', 'Gasto')]

specs = [
    dict(base, key='plancuenta', model='PlanCuenta', title='Plan de Cuentas', singular='Cuenta', c_a='create_cuenta',
         create_label='Nueva cuenta', delete_mname='delete_cuentas', search=['codigo', 'nombre'], order_col=1,
         cols=[col('codigo', 'Código'),
               col('nombre', 'Cuenta', render="let pad = (rowobj.nivel - 1) * 18; return `<span style=\"padding-left:${pad}px; ${rowobj.imputable ? '' : 'font-weight:600;'}\">${$('<span>').text(data).html()}</span>`;"),
               col('tipo', 'Tipo'), col('nivel', 'Nivel', 'int', 'align-center'),
               col('imputable', 'Imputable', 'bool', 'align-center', BOOL), col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='codigo', label='Código', type='text', required=True, col=4, ph='6.1.13', readonly_on_edit=True,
                      help='La cuenta cuelga del código más cercano (6.1.13 cuelga de 6.1) y hereda su tipo.'),
                 dict(name='nombre', label='Nombre', type='text', required=True, col=8),
                 dict(name='tipo', label='Tipo (solo cuentas de primer nivel)', type='select', options=TIPOS, col=6),
                 dict(name='activo', label='Activa', type='bool', col=6)]),

    dict(base, key='formatoasiento', model='FormatoAsiento', title='Formatos de Asiento', create=False, delete=False, edit=True,
         search=['nombre', 'evento'], order_col=1,
         cols=[col('nombre', 'Formato'), col('evento', 'Evento que lo dispara'), col('concepto', 'Concepto del asiento'),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)]),

    dict(base, key='asiento', model='Asiento', title='Asientos Contables', singular='Asiento', workflow=True,
         create_label='Asiento manual', search=['concepto', 'evento'], order_col=1, order_dir='desc',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('concepto', 'Concepto'), col('origen', 'Origen'),
               col('evento', 'Evento'), col('total', 'Total', 'float', 'align-right', MONEY),
               col('estado', 'Estado', render=ESTADO_BADGE)]),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Contabilidad', specs, os.path.join(BASE, 'Contabilidad', 'templates', 'Contabilidad'))
