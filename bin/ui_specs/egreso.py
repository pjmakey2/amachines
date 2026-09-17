import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

MON = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]
base = dict(pkg='mng_egreso', attr='MEgreso')
CUENTA = dict(type='fk', app='Tesoreria', fk_model='CuentaBancaria', display=['get_descripcion'], methods=['get_descripcion'])
CAJA = dict(type='fk', app='Tesoreria', fk_model='Caja')
PROV = dict(type='fk', fk_model='Proveedor', display=['get_descripcion'], methods=['get_descripcion'])
CAT = dict(type='fk', fk_model='CategoriaGasto')

RECURRENTE_FIELDS = [
    dict(PROV, name='proveedorobj_id', label='Proveedor', required=True, col=12),
    dict(CAT, name='categoriaobj_id', label='Categoría', required=True),
    dict(name='concepto', label='Concepto', type='text', required=True),
    dict(name='monto', label='Monto (IVA incluido)', type='number', required=True, col=4),
    dict(name='moneda', label='Moneda', type='select', options=MON, col=4),
    dict(name='activo', label='Activo', type='bool', col=4),
    dict(name='frecuencia', label='Frecuencia', type='select', col=4,
         options=[('mensual', 'Mensual'), ('bimestral', 'Bimestral'), ('trimestral', 'Trimestral'),
                  ('semestral', 'Semestral'), ('anual', 'Anual')]),
    dict(name='dia_aplicacion', label='Día de aplicación', type='number', integer=True, required=True, default='1', col=4,
         help='Día del mes en que se genera el gasto.'),
    dict(name='fecha_inicio', label='Desde', type='date', required=True, today=True, col=4),
    dict(name='fecha_fin', label='Hasta (opcional)', type='date', col=4),
]

# Seccion de gastos recurrentes dentro de la ficha del proveedor (solo al editar)
PROVEEDOR_RECURRENTES_HTML = """
        {% if mobj %}
        <div class="card shadow-sm mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0"><i class="mdi mdi-calendar-sync"></i> Gastos recurrentes del proveedor</h6>
                    <button type="button" class="btn btn-sm btn-outline-primary" name="btn_nuevo_recurrente"><i class="mdi mdi-plus"></i> Agregar</button>
                </div>
                <table class="table table-sm mb-0">
                    <thead><tr><th>Concepto</th><th>Categoría</th><th class="text-end">Monto</th><th>Frecuencia</th><th>Día</th><th>Próxima</th><th>Activo</th><th></th></tr></thead>
                    <tbody name="tbody_recurrentes"><tr><td colspan="8" class="text-muted text-center">Cargando...</td></tr></tbody>
                </table>
            </div>
        </div>
        {% endif %}
"""
PROVEEDOR_RECURRENTES_JS = """
    {% if mobj %}
    proveedor_recurrentes_load = () => {
        let ffdata = new FormData();
        ffdata.append('module', 'OptsIO');
        ffdata.append('package', 'io_serial');
        ffdata.append('attr', 'IoS');
        ffdata.append('mname', 'seModel');
        ffdata.append('model_app_name', 'Egreso');
        ffdata.append('model_name', 'GastoRecurrente');
        ffdata.append('dbcon', 'default');
        ffdata.append('fields', jfy(['id', 'concepto', 'categoriaobj__nombre', 'monto', 'moneda', 'frecuencia', 'dia_aplicacion', 'proxima_fecha', 'activo']));
        ffdata.append('mquery', jfy([{field: 'proveedorobj_id', value: {{ mobj.pk }}}]));
        axios.post('{% url "iom" %}', ffdata, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
            let esc = (v) => $('<span>').text(v == null ? '' : v).html();
            let filas = (rsp.data.qs || []).map((r) => `<tr>
                <td>${esc(r.concepto)}</td><td>${esc(r.categoriaobj__nombre)}</td>
                <td class="text-end">${r.moneda} ${UiN.formatNumberU(parseFloat(r.monto).toFixed(0))}</td>
                <td>${r.frecuencia}</td><td>${r.dia_aplicacion}</td><td>${moment(r.proxima_fecha).format('DD/MM/YYYY')}</td>
                <td>${r.activo ? 'Sí' : 'No'}</td>
                <td><i title="Editar" data-id="${r.id}" class="tr-recurrente-edit mdi mdi-pencil cursor-pointer"></i></td></tr>`);
            qelem('#form_proveedor_{{ rr }} tbody[name=tbody_recurrentes]').innerHTML = filas.join('') ||
                '<tr><td colspan="8" class="text-muted text-center">Sin gastos recurrentes</td></tr>';
        });
    }
    // El recurrente se edita en un modal para no perder la ficha abierta en el offcanvas
    proveedor_recurrente_form = (pk) => {
        let tps = {
            url: '{% url "dtmpl" %}', template: 'Egreso/GastoRecurrenteCreateUi.html', raw: true, dbcon: 'default',
            dattrs: { t_guid: 'none', from_ProveedorCreateUi: true, en_modal: true, proveedor_id: {{ mobj.pk }} },
        }
        if (pk) { tps['model_app_name'] = 'Egreso'; tps['model_name'] = 'GastoRecurrente'; tps['pk'] = pk; }
        OptsIO.getTmpl(tps).then((rsp) => {
            Swal.fire({ title: 'Gasto recurrente', html: `<div class="text-start">${rsp.data}</div>`, width: 800,
                        showConfirmButton: false, showCloseButton: true,
                        didOpen: () => { $(Swal.getHtmlContainer()).find('script').each(function() { $.globalEval(this.text || this.textContent || ''); }); },
                        willClose: () => proveedor_recurrentes_load() });
            UiB.kILLLoaderAjax();
        });
    }
    qelem('#form_proveedor_{{ rr }} button[name=btn_nuevo_recurrente]').addEventListener('click', () => proveedor_recurrente_form());
    $('#form_proveedor_{{ rr }}').on('click', '.tr-recurrente-edit', function() { proveedor_recurrente_form($(this).data('id')); });
    proveedor_recurrentes_load();
    {% endif %}
"""

GASTO_TIPO_JS = """
    // Secciones visibles segun el tipo de gasto
    gasto_toggle_tipo = () => {
        let tipo = qelem('#form_gasto_{{ rr }} select[name=tipo]').value;
        let visibles = {
            comun: ['sec_comprobante', 'factura_numero', 'factura_timbrado', 'factura_fecha', 'factura_condicion', 'vencimiento', 'exenta', 'gravada_5', 'gravada_10', 'moneda', 'archivo', 'proveedorobj_id'],
            a_rendir: ['sec_rendir', 'presupuesto_monto', 'presupuesto_ref', 'responsable', 'moneda', 'archivo', 'proveedorobj_id', 'beneficiario'],
            caja_chica: ['sec_caja', 'cajaobj_id', 'sec_comprobante', 'factura_numero', 'factura_timbrado', 'factura_fecha', 'exenta', 'gravada_5', 'gravada_10', 'archivo', 'proveedorobj_id', 'beneficiario'],
        }[tipo];
        ['sec_comprobante', 'factura_numero', 'factura_timbrado', 'factura_fecha', 'factura_condicion', 'vencimiento', 'exenta', 'gravada_5', 'gravada_10',
         'sec_rendir', 'presupuesto_monto', 'presupuesto_ref', 'responsable', 'sec_caja', 'cajaobj_id', 'moneda', 'archivo', 'beneficiario', 'proveedorobj_id'].forEach((n) => {
            let el = qelem(`#form_gasto_{{ rr }} [data-field=${n}]`);
            if (el) el.hidden = !visibles.includes(n);
        });
    }
    qelem('#form_gasto_{{ rr }} select[name=tipo]').addEventListener('change', gasto_toggle_tipo);
    gasto_toggle_tipo();
    {% if mobj and mobj.estado != 'cargado' %}
        $('#form_gasto_{{ rr }} :input').prop('disabled', true);
        $('#form_gasto_{{ rr }} button[type=submit]').replaceWith('<div class="alert alert-info mb-0">Gasto {{ mobj.estado }}: solo lectura.</div>');
    {% endif %}
"""

specs = [
    dict(base, key='proveedor', model='Proveedor', title='Proveedores', singular='Proveedor',
         delete_extra={'model_name': 'Proveedor'}, search=['nombre', 'ruc', 'nombre_fantasia'],
         cols=[col('ruc', 'RUC'), col('ruc_dv', 'DV', 'int'), col('nombre', 'Razón social'), col('nombre_fantasia', 'Fantasía'),
               col('telefono', 'Teléfono'), col('email', 'Email'), col('plazo_dias', 'Plazo (días)', 'int', 'align-right'),
               col('get_saldo_pendiente', 'Saldo pendiente', 'float', 'align-right', MONEY, btyp='mdb'),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)],
         fields=[dict(name='ruc', label='RUC', type='text', required=True, col=4),
                 dict(name='ruc_dv', label='DV', type='number', integer=True, default='0', col=2),
                 dict(name='nombre', label='Razón social', type='text', required=True, col=6),
                 dict(name='nombre_fantasia', label='Nombre de fantasía', type='text'),
                 dict(name='contacto', label='Contacto', type='text'),
                 dict(name='telefono', label='Teléfono', type='text', col=4),
                 dict(name='email', label='Email', type='text', col=4),
                 dict(name='plazo_dias', label='Plazo de pago (días)', type='number', integer=True, default='0', col=4),
                 dict(name='direccion', label='Dirección', type='text', col=12),
                 dict(name='banco_nombre', label='Banco (para transferirle)', type='text'),
                 dict(name='banco_cuenta', label='Nro. de cuenta', type='text'),
                 dict(name='activo', label='Activo', type='bool', col=4)],
         form_extra_html=PROVEEDOR_RECURRENTES_HTML, form_extra_js=PROVEEDOR_RECURRENTES_JS),

    dict(base, key='categoriagasto', model='CategoriaGasto', title='Categorías de Gasto', singular='Categoría de Gasto',
         delete_extra={'model_name': 'CategoriaGasto'}, search=['nombre'],
         cols=[col('nombre', 'Nombre'), col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True, col=8),
                 dict(name='activo', label='Activa', type='bool', col=4)]),

    dict(base, key='gastorecurrente', model='GastoRecurrente', title='Gastos Recurrentes', singular='Gasto Recurrente',
         c_a='create_recurrente', delete_extra={'model_name': 'GastoRecurrente'},
         search=['concepto', 'proveedorobj__nombre'], order_col=7,
         toolbar_extra="""            <button id="btn_generar_recurrentes" class="btn btn-outline-success"><i class="mdi mdi-play"></i> Generar vencidos ahora</button>\n""",
         cols=[col('proveedorobj__nombre', 'Proveedor'), col('concepto', 'Concepto'), col('categoriaobj__nombre', 'Categoría'),
               col('monto', 'Monto', 'float', 'align-right', MONEY), col('moneda', 'Moneda'), col('frecuencia', 'Frecuencia'),
               col('proxima_fecha', 'Próxima generación', 'date'), col('fecha_fin', 'Hasta', 'date'),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)],
         fields=RECURRENTE_FIELDS,
         after_save_js="if (typeof Swal !== 'undefined' && Swal.isVisible()) Swal.close();",
         form_extra_js="""
    {% if proveedor_id %}
        // Abierto desde la ficha del proveedor: el proveedor queda fijo
        setTimeout(() => { $('#form_gastorecurrente_{{ rr }} select[name=proveedorobj_id]').val('{{ proveedor_id }}').trigger('change'); }, 600);
    {% endif %}
""",
         extra_js="""
    qelem('#btn_generar_recurrentes').addEventListener('click', () => {
        let gbe = new FormData();
        gbe.append('module', 'Egreso');
        gbe.append('package', 'mng_egreso');
        gbe.append('attr', 'MEgreso');
        gbe.append('mname', 'generar_recurrentes_ui');
        gbe.append('dbcon', 'default');
        axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
            UiB.MsgSuccess(rsp.data.success);
            $(`#${t_gastorecurrente}`).DataTable().ajax.reload();
        });
    });
"""),

    dict(base, key='gasto', model='Gasto', title='Gastos', singular='Gasto', workflow=True, c_a='create_gasto',
         create_label='Cargar gasto', search=['concepto', 'factura_numero', 'proveedorobj__nombre', 'beneficiario'],
         order_col=1, order_dir='desc',
         acc='<i title="Ver/Editar" class="tr-gasto-query text fs-5 mdi mdi-archive-eye-outline me-1"></i>'
             '<i title="Rendir gasto" class="tr-gasto-rendir text fs-5 mdi mdi-clipboard-check-outline text-primary cursor-pointer me-1"></i>',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('tipo', 'Tipo'),
               col('get_beneficiario', 'Proveedor / Beneficiario', btyp='mdb'), col('categoriaobj__nombre', 'Categoría'),
               col('concepto', 'Concepto'), col('factura_numero', 'Factura'), col('moneda', 'Mon.'),
               col('total', 'Total', 'float', 'align-right', MONEY), col('presupuesto_monto', 'Presupuesto', 'float', 'align-right', MONEY),
               col('saldo', 'Saldo', 'float', 'align-right', MONEY), col('estado_pago', 'Pago'),
               col('estado', 'Estado', render=ESTADO_BADGE), col('rendido', 'Rendido', 'bool', 'align-center', BOOL)],
         fields=[dict(name='tipo', label='Tipo de gasto', type='select', col=4,
                      options=[('comun', 'Gasto común (con factura)'), ('a_rendir', 'Gasto a rendir (presupuesto)'), ('caja_chica', 'Caja chica')]),
                 dict(name='fecha', label='Fecha', type='date', required=True, today=True, col=4),
                 dict(name='moneda', label='Moneda', type='select', options=MON, col=4),
                 dict(PROV, name='proveedorobj_id', label='Proveedor'),
                 dict(name='beneficiario', label='Beneficiario (si no es proveedor)', type='text'),
                 dict(CAT, name='categoriaobj_id', label='Categoría', required=True),
                 dict(name='concepto', label='Concepto', type='text', required=True),
                 dict(name='sec_caja', label='Caja chica', type='section'),
                 dict(CAJA, name='cajaobj_id', label='Caja chica que paga', qs=[{'field': 'activo', 'value': True}, {'field': 'tipo', 'value': 'chica'}],
                      help='El gasto se descuenta de la caja al aprobarse.'),
                 dict(name='sec_rendir', label='Presupuesto (a rendir)', type='section'),
                 dict(name='presupuesto_monto', label='Monto del presupuesto', type='number', col=4),
                 dict(name='presupuesto_ref', label='Referencia del presupuesto', type='text', col=4),
                 dict(name='responsable', label='Responsable de rendir', type='text', col=4),
                 dict(name='sec_comprobante', label='Comprobante', type='section'),
                 dict(name='factura_numero', label='Factura Nro.', type='text', ph='001-001-0000001', col=4),
                 dict(name='factura_timbrado', label='Timbrado', type='text', col=4),
                 dict(name='factura_fecha', label='Fecha factura', type='date', col=4),
                 dict(name='factura_condicion', label='Condición', type='select', col=4, options=[('contado', 'Contado'), ('credito', 'Crédito')]),
                 dict(name='vencimiento', label='Vencimiento', type='date', col=4),
                 dict(name='exenta', label='Exenta', type='number', default='0', col=4),
                 dict(name='gravada_5', label='Gravada 5% (IVA incl.)', type='number', default='0', col=4),
                 dict(name='gravada_10', label='Gravada 10% (IVA incl.)', type='number', default='0', col=4),
                 dict(name='archivo', label='Comprobante / presupuesto escaneado', type='file', col=12)],
         form_extra_js=GASTO_TIPO_JS,
         extra_js="""
    $(`#${t_gasto} tbody`).on('click', '.tr-gasto-rendir', function() {
        let rowobj = $(`#${t_gasto}`).DataTable().row($(this).closest('tr')).data();
        if (rowobj.tipo !== 'a_rendir' || rowobj.estado !== 'aprobado' || rowobj.rendido || rowobj.anulado) {
            UiB.MsgInfo('Solo se rinde un gasto "a rendir" aprobado y todavía no rendido.');
            return;
        }
        OptsIO.getTmpl({ url: '{% url "dtmpl" %}', template: 'Egreso/GastoRendirUi.html', raw: true, dbcon: 'default',
                         model_app_name: 'Egreso', model_name: 'Gasto', pk: rowobj.id,
                         dattrs: { t_guid: t_gasto, offcanvasglobal: true } }).then((rsp) => {
            $('#offcanvasGlobalUiBody').html(rsp.data);
            new bootstrap.Offcanvas('#offcanvasGlobalUi').show();
            UiB.kILLLoaderAjax();
        });
    })
"""),

    dict(base, key='pagoproveedor', model='PagoProveedor', title='Pagos a Proveedores', singular='Pago', workflow=True,
         create_label='Nuevo pago', search=['beneficiario', 'referencia'], order_col=1, order_dir='desc',
         acc='<i title="Ver/Editar" class="tr-pagoproveedor-query text fs-5 mdi mdi-archive-eye-outline me-1"></i>'
             '<i title="Imprimir cheque" class="tr-pagoproveedor-cheque text fs-5 mdi mdi-printer-outline text-primary cursor-pointer me-1"></i>',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('beneficiario', 'Beneficiario'),
               col('medio', 'Medio'), col('get_origen_fondos', 'Origen de fondos', btyp='mdb'),
               col('get_cheque_numero', 'Cheque', btyp='mdb'), col('referencia', 'Referencia'), col('moneda', 'Mon.'),
               col('total', 'Total', 'float', 'align-right', MONEY), col('estado', 'Estado', render=ESTADO_BADGE)],
         extra_js="""
    $(`#${t_pagoproveedor} tbody`).on('click', '.tr-pagoproveedor-cheque', function() {
        let rowobj = $(`#${t_pagoproveedor}`).DataTable().row($(this).closest('tr')).data();
        let gbe = new FormData();
        gbe.append('module', 'Egreso');
        gbe.append('package', 'mng_egreso');
        gbe.append('attr', 'MEgreso');
        gbe.append('mname', 'imprimir_cheque');
        gbe.append('dbcon', 'default');
        gbe.append('id', rowobj.id);
        axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
            if (rsp.data.error) { UiB.MsgError(rsp.data.error); return; }
            let link = document.createElement('a');
            link.href = rsp.data.pdf_file;
            link.target = '_blank';
            link.click();
        });
    })
"""),

    dict(base, key='transferenciainterna', model='TransferenciaInterna', title='Transferencias Internas',
         singular='Transferencia', workflow=True, c_a='create_transferencia', create_label='Nueva transferencia',
         search=['concepto', 'referencia'], order_col=1, order_dir='desc',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('get_origen', 'Origen', btyp='mdb'),
               col('get_destino', 'Destino', btyp='mdb'), col('monto', 'Monto', 'float', 'align-right', MONEY),
               col('concepto', 'Concepto'), col('referencia', 'Referencia'), col('estado', 'Estado', render=ESTADO_BADGE)],
         fields=[dict(name='fecha', label='Fecha', type='date', required=True, today=True, col=4),
                 dict(name='monto', label='Monto que sale', type='number', required=True, col=4),
                 dict(name='monto_destino', label='Monto que ingresa (si cambia la moneda)', type='number', default='0', col=4),
                 dict(name='sec_origen', label='Origen (elegir uno)', type='section'),
                 dict(CUENTA, name='origen_cuentaobj_id', label='Cuenta bancaria origen'),
                 dict(CAJA, name='origen_cajaobj_id', label='Caja origen'),
                 dict(name='sec_destino', label='Destino (elegir uno) — para reponer caja chica, elegir la caja', type='section'),
                 dict(CUENTA, name='destino_cuentaobj_id', label='Cuenta bancaria destino'),
                 dict(CAJA, name='destino_cajaobj_id', label='Caja destino'),
                 dict(name='concepto', label='Concepto', type='text', col=8),
                 dict(name='referencia', label='Referencia', type='text', col=4)],
         form_extra_js="""
    {% if mobj and mobj.estado != 'cargado' %}
        $('#form_transferenciainterna_{{ rr }} :input').prop('disabled', true);
        $('#form_transferenciainterna_{{ rr }} button[type=submit]').replaceWith('<div class="alert alert-info mb-0">Transferencia {{ mobj.estado }}: solo lectura.</div>');
    {% endif %}
"""),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Egreso', specs, os.path.join(BASE, 'Egreso', 'templates', 'Egreso'))
