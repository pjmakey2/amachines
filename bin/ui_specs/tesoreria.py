import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

MON = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]
base = dict(pkg='mng_tesoreria', attr='MTesoreria')

specs = [
    dict(base, key='banco', model='Banco', title='Bancos', singular='Banco',
         delete_extra={'model_name': 'Banco'}, search=['nombre', 'codigo'],
         cols=[col('nombre', 'Nombre'), col('codigo', 'Código'),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True, col=8),
                 dict(name='codigo', label='Código', type='text', col=4),
                 dict(name='activo', label='Activo', type='bool', col=4)]),
    dict(base, key='cuentabancaria', model='CuentaBancaria', title='Cuentas Bancarias', singular='Cuenta Bancaria',
         delete_extra={'model_name': 'CuentaBancaria'}, search=['numero', 'titular', 'bancoobj__nombre'],
         cols=[col('bancoobj__nombre', 'Banco'), col('numero', 'Número'), col('titular', 'Titular'),
               col('tipo', 'Tipo'), col('moneda', 'Moneda'),
               col('saldo_inicial', 'Saldo Inicial', 'float', 'align-right', MONEY),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)],
         fields=[dict(name='bancoobj_id', label='Banco', type='fk', fk_model='Banco', required=True),
                 dict(name='numero', label='Número de cuenta', type='text', required=True),
                 dict(name='titular', label='Titular', type='text', col=12),
                 dict(name='tipo', label='Tipo', type='select', col=4,
                      options=[('cta_cte', 'Cuenta Corriente'), ('caja_ahorro', 'Caja de Ahorro')]),
                 dict(name='moneda', label='Moneda', type='select', options=MON, col=4),
                 dict(name='activo', label='Activa', type='bool', col=4),
                 dict(name='saldo_inicial', label='Saldo inicial', type='number', default='0'),
                 dict(name='saldo_inicial_fecha', label='Fecha del saldo inicial', type='date')]),
    dict(base, key='chequera', model='Chequera', title='Chequeras', singular='Chequera', c_a='create_chequera',
         delete_extra={'model_name': 'Chequera'}, search=['serie', 'cuentaobj__numero', 'cuentaobj__bancoobj__nombre'],
         cols=[col('cuentaobj__bancoobj__nombre', 'Banco'), col('cuentaobj__numero', 'Cuenta'),
               col('tipo', 'Tipo'), col('serie', 'Serie'),
               col('numero_desde', 'Desde', 'int', 'align-right'), col('numero_hasta', 'Hasta', 'int', 'align-right'),
               col('proximo_numero', 'Próximo', 'int', 'align-right'),
               col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='cuentaobj_id', label='Cuenta bancaria', type='fk', fk_model='CuentaBancaria', required=True,
                      col=12, display=['get_descripcion'], methods=['get_descripcion']),
                 dict(name='tipo', label='Tipo', type='select', col=4,
                      options=[('vista', 'A la vista'), ('diferido', 'Pago diferido')]),
                 dict(name='serie', label='Serie', type='text', col=4),
                 dict(name='activo', label='Activa', type='bool', col=4),
                 dict(name='numero_desde', label='Número desde', type='number', required=True, integer=True),
                 dict(name='numero_hasta', label='Número hasta', type='number', required=True, integer=True,
                      help='El próximo número a emitir arranca en "desde" y avanza solo.')]),
    dict(base, key='caja', model='Caja', title='Cajas', singular='Caja',
         delete_extra={'model_name': 'Caja'}, search=['nombre', 'responsable'],
         cols=[col('nombre', 'Nombre'), col('tipo', 'Tipo'), col('moneda', 'Moneda'),
               col('tope', 'Tope', 'float', 'align-right', MONEY), col('responsable', 'Responsable'),
               col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True, col=8),
                 dict(name='tipo', label='Tipo', type='select', col=4,
                      options=[('general', 'Caja General'), ('chica', 'Caja Chica')]),
                 dict(name='moneda', label='Moneda', type='select', options=MON, col=4),
                 dict(name='tope', label='Tope', type='number', default='0', col=4,
                      help='Caja chica: saldo máximo permitido (0 = sin tope).'),
                 dict(name='activo', label='Activa', type='bool', col=4),
                 dict(name='responsable', label='Responsable', type='text'),
                 dict(name='saldo_inicial', label='Saldo inicial', type='number', default='0')]),
    dict(base, key='movimiento', model='MovimientoTesoreria', title='Movimientos de Tesorería',
         singular='Movimiento', create_title='Registrar movimiento manual', create_label='Movimiento manual',
         c_a='create_movimiento', editable=False, acc='',
         delete_label='Anular', delete_mname='anular_movimientos',
         delete_msg='¿Anular ${ids.length} movimiento(s)?',
         search=['concepto', 'referencia'], order_col=1, order_dir='desc',
         after_save_js="bootstrap.Offcanvas.getInstance('#offcanvasGlobalUi')?.hide();",
         cols=[col('fecha', 'Fecha', 'date'), col('get_destino', 'Cuenta / Caja', btyp='mdb'),
               col('tipo', 'Tipo', render="return data === 'ingreso' ? '<span class=\"badge bg-success\">Ingreso</span>' : '<span class=\"badge bg-danger\">Egreso</span>';"),
               col('monto', 'Monto', 'float', 'align-right', MONEY), col('moneda', 'Moneda'),
               col('concepto', 'Concepto'), col('referencia', 'Referencia'),
               col('origen_model', 'Origen'),
               col('anulado', 'Anulado', 'bool', 'align-center', BOOL),
               col('cargado_usuario', 'Usuario')],
         fields=[dict(name='fecha', label='Fecha', type='date', required=True, today=True, col=4),
                 dict(name='tipo', label='Tipo', type='select', col=4,
                      options=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')]),
                 dict(name='monto', label='Monto', type='number', required=True, col=4),
                 dict(name='cuentaobj_id', label='Cuenta bancaria', type='fk', fk_model='CuentaBancaria',
                      display=['get_descripcion'], methods=['get_descripcion']),
                 dict(name='cajaobj_id', label='Caja', type='fk', fk_model='Caja'),
                 dict(name='concepto', label='Concepto', type='text', required=True, col=8),
                 dict(name='referencia', label='Referencia', type='text', col=4)]),
    dict(base, key='cheque', model='Cheque', title='Cheques Emitidos', create=False, delete=False,
         acc='<i title="Anular cheque" class="tr-cheque-anular text fs-5 mdi mdi-cancel text-danger cursor-pointer"></i>',
         search=['beneficiario', 'numero', 'concepto'], order_col=2, order_dir='desc',
         cols=[col('chequeraobj__cuentaobj__bancoobj__nombre', 'Banco'), col('numero', 'Número', 'int'),
               col('fecha_emision', 'Emisión', 'date'), col('fecha_pago', 'Pago', 'date'),
               col('beneficiario', 'Beneficiario'), col('monto', 'Monto', 'float', 'align-right', MONEY),
               col('estado', 'Estado'), col('concepto', 'Concepto')],
         extra_js="""
    $(`#${t_cheque} tbody`).on('click', '.tr-cheque-anular', function() {
        let rowobj = $(`#${t_cheque}`).DataTable().row($(this).closest('tr')).data();
        Swal.fire({
            title: `Anular cheque ${rowobj.numero}`,
            input: 'text',
            inputLabel: 'Motivo',
            showCancelButton: true,
            confirmButtonText: 'Anular',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (!result.isConfirmed) return;
            let gbe = new FormData();
            gbe.append('module', 'Tesoreria');
            gbe.append('package', 'mng_tesoreria');
            gbe.append('attr', 'MTesoreria');
            gbe.append('mname', 'anular_cheque');
            gbe.append('dbcon', 'default');
            gbe.append('id', rowobj.id);
            gbe.append('motivo', result.value || '');
            axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
                if (rsp.data.error) UiB.MsgError(rsp.data.error);
                else UiB.MsgSuccess(rsp.data.success || rsp.data.info);
                $(`#${t_cheque}`).DataTable().ajax.reload();
            });
        });
    })
"""),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Tesoreria', specs, os.path.join(BASE, 'Tesoreria', 'templates', 'Tesoreria'))
