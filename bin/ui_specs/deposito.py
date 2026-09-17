import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

MON = [('PYG', 'Guaraníes'), ('USD', 'Dólares'), ('EUR', 'Euros'), ('BRL', 'Reales')]

CHEQUES_HTML = """
        <div class="card shadow-sm mb-3" data-field="sec_cheques">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0"><i class="mdi mdi-checkbook"></i> Cheques depositados</h6>
                    <button type="button" class="btn btn-sm btn-outline-primary" name="btn_add_cheque"><i class="mdi mdi-plus"></i> Agregar cheque</button>
                </div>
                <table class="table table-sm mb-0">
                    <thead><tr><th>Banco</th><th>Número</th><th>Librador</th><th>Fecha</th><th class="text-end">Monto</th><th></th></tr></thead>
                    <tbody name="tbody_cheques"></tbody>
                </table>
            </div>
        </div>
"""
DEPOSITO_JS = """
    deposito_sel = (name) => `#form_deposito_{{ rr }} [name=${name}]`;
    deposito_add_cheque = (c) => {
        c = c || {};
        let tr = document.createElement('tr');
        tr.innerHTML = `<td><input type="text" name="chq_banco" class="form-control form-control-sm"></td>
            <td><input type="text" name="chq_numero" class="form-control form-control-sm"></td>
            <td><input type="text" name="chq_librador" class="form-control form-control-sm"></td>
            <td><input type="date" name="chq_fecha" class="form-control form-control-sm"></td>
            <td><input type="text" name="chq_monto" class="form-control form-control-sm text-end"></td>
            <td><i title="Quitar" class="mdi mdi-close text-danger cursor-pointer" name="chq_quitar"></i></td>`;
        tr.querySelector('[name=chq_banco]').value = c.banco || '';
        tr.querySelector('[name=chq_numero]').value = c.numero || '';
        tr.querySelector('[name=chq_librador]').value = c.librador || '';
        tr.querySelector('[name=chq_fecha]').value = c.fecha || '';
        tr.querySelector('[name=chq_monto]').value = c.monto || 0;
        Inputmask({ alias: 'numeric', groupSeparator: ',', radixPoint: '.', autoGroup: true, digits: 2, digitsOptional: false,
                    rightAlign: true, allowMinus: false, removeMaskOnSubmit: true, autoUnmask: true }).mask(tr.querySelector('[name=chq_monto]'));
        tr.querySelector('[name=chq_quitar]').addEventListener('click', () => tr.remove());
        qelem(deposito_sel('tbody_cheques')).appendChild(tr);
    }
    qelem(deposito_sel('btn_add_cheque')).addEventListener('click', () => deposito_add_cheque());
    deposito_toggle_tipo = () => {
        qelem('#form_deposito_{{ rr }} [data-field=sec_cheques]').hidden = qelem(deposito_sel('tipo')).value !== 'cheque';
    }
    qelem(deposito_sel('tipo')).addEventListener('change', deposito_toggle_tipo);
    deposito_toggle_tipo();
    {% if mobj %}
        {% if mobj.automatico %}
            // Generado por un cobro: tipo, monto y moneda vienen del recibo
            ['tipo', 'monto', 'moneda'].forEach((n) => { qelem(deposito_sel(n)).disabled = true; });
            $('#form_deposito_{{ rr }}').prepend(`<div class="alert alert-secondary py-2"><i class="mdi mdi-robot-outline"></i> Generado por el cobro: <b>{{ mobj.origen_desc }}</b>. Complete la cuenta y la boleta.</div>`);
        {% endif %}
        (() => {
            let gbe = new FormData();
            gbe.append('module', 'Deposito');
            gbe.append('package', 'mng_deposito');
            gbe.append('attr', 'MDeposito');
            gbe.append('mname', 'get_cheques');
            gbe.append('dbcon', 'default');
            gbe.append('id', '{{ mobj.pk }}');
            axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
                (rsp.data.cheques || []).forEach((c) => deposito_add_cheque(c));
                {% if mobj.estado != 'cargado' or mobj.anulado %}
                    $('#form_deposito_{{ rr }} :input').prop('disabled', true);
                    $('#form_deposito_{{ rr }} button[type=submit]').replaceWith('<div class="alert alert-info mb-0">Depósito {{ mobj.estado }}: solo lectura.</div>');
                {% endif %}
            });
        })();
    {% endif %}
"""
BEFORE_SAVE = """
        ['chq_banco', 'chq_numero', 'chq_librador', 'chq_fecha', 'chq_monto'].forEach((n) => delete edata[n]);
        edata['cheques'] = [];
        document.querySelectorAll('#form_deposito_{{ rr }} tbody[name=tbody_cheques] tr').forEach((tr) => {
            edata['cheques'].push({
                banco: tr.querySelector('[name=chq_banco]').value, numero: tr.querySelector('[name=chq_numero]').value,
                librador: tr.querySelector('[name=chq_librador]').value, fecha: tr.querySelector('[name=chq_fecha]').value,
                monto: tr.querySelector('[name=chq_monto]').inputmask.unmaskedvalue().replace(',', '.')
            });
        });
"""

specs = [
    dict(pkg='mng_deposito', attr='MDeposito', key='deposito', model='Deposito', title='Depósitos', singular='Depósito',
         workflow=True, c_a='create_deposito', create_label='Nuevo depósito',
         search=['boleta_numero', 'origen_desc', 'observacion'], order_col=1, order_dir='desc',
         toolbar_extra="""            <select id="filtro_deposito_estado" class="form-select" style="width: 220px;">
                <option value="pendientes">Pendientes de acreditar</option>
                <option value="">Todos</option>
                <option value="aprobado">Acreditados</option>
            </select>\n""",
         mquery=[],
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('tipo', 'Tipo'),
               col('get_cuenta', 'Cuenta', btyp='mdb'), col('boleta_numero', 'Boleta'), col('moneda', 'Mon.'),
               col('monto', 'Monto', 'float', 'align-right', MONEY), col('origen_desc', 'Origen'),
               col('automatico', 'Auto', 'bool', 'align-center', BOOL), col('estado', 'Estado', render=ESTADO_BADGE)],
         fields=[dict(name='fecha', label='Fecha del depósito', type='date', required=True, today=True, col=4),
                 dict(name='tipo', label='Tipo de valor', type='select', col=4,
                      options=[('efectivo', 'Efectivo'), ('cheque', 'Cheques'), ('transferencia', 'Transferencia recibida'), ('tarjeta', 'Acreditación de tarjetas')]),
                 dict(name='monto', label='Monto', type='number', required=True, col=4),
                 dict(name='cuentaobj_id', label='Cuenta bancaria donde se depositó', type='fk', app='Tesoreria', fk_model='CuentaBancaria',
                      display=['get_descripcion'], methods=['get_descripcion'], col=8),
                 dict(name='moneda', label='Moneda', type='select', options=MON, col=4),
                 dict(name='boleta_numero', label='Nro. de boleta / comprobante', type='text', col=4),
                 dict(name='observacion', label='Observación', type='text', col=8)],
         form_extra_html=CHEQUES_HTML, form_extra_js=DEPOSITO_JS, before_save_js=BEFORE_SAVE,
         extra_js="""
    // Filtro rapido: por defecto lo que falta acreditar
    deposito_aplicar_filtro = () => {
        let v = qelem('#filtro_deposito_estado').value;
        gmquery_deposito = gmquery_deposito.filter((q) => !['estado', 'anulado'].includes(q.field));
        if (v === 'pendientes') { gmquery_deposito.push({field: 'estado', value: 'cargado|verificado'}, {field: 'anulado', value: false}); }
        else if (v) { gmquery_deposito.push({field: 'estado', value: v}); }
    }
    qelem('#filtro_deposito_estado').addEventListener('change', () => { deposito_aplicar_filtro(); $(`#${t_deposito}`).DataTable().ajax.reload(); });
    deposito_aplicar_filtro();
    $(`#${t_deposito}`).DataTable().ajax.reload();
"""),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Deposito', specs, os.path.join(BASE, 'Deposito', 'templates', 'Deposito'))
