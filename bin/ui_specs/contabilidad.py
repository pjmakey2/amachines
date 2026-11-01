import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

base = dict(pkg='mng_contabilidad', attr='MContabilidad')
TIPOS = [('activo', 'Activo'), ('pasivo', 'Pasivo'), ('patrimonio', 'Patrimonio Neto'), ('ingreso', 'Ingreso'), ('costo', 'Costo'), ('gasto', 'Gasto')]

specs = [
    dict(base, key='plancuenta', model='PlanCuenta', title='Plan de Cuentas', singular='Cuenta', c_a='create_cuenta',
         create_label='Nueva cuenta', delete_mname='delete_cuentas', search=['codigo', 'nombre'], order_col=1,
         cols=[col('codigo', 'Código', render="return `<span class=\"font-monospace\">${data}</span>`;"),
               col('get_codigo_corto', 'Corto', btyp='mdb'),
               col('nombre', 'Cuenta', render="let pad = (rowobj.nivel - 1) * 18; return `<span style=\"padding-left:${pad}px; ${rowobj.imputable ? '' : 'font-weight:600;'}\">${$('<span>').text(data).html()}</span>`;"),
               col('tipo', 'Tipo'), col('nivel', 'Nivel', 'int', 'align-center'),
               col('imputable', 'Imputable', 'bool', 'align-center', BOOL), col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='codigo', label='Código', type='text', required=True, col=5, ph='3.1.3.2', readonly_on_edit=True,
                      help='Cargue solo los niveles con valor (3.1.3.2). Se completa al formato del negocio y hereda el tipo del padre.'),
                 dict(name='nombre', label='Nombre', type='text', required=True, col=7),
                 dict(name='tipo', label='Tipo (solo cuentas de primer nivel)', type='select', options=TIPOS, col=6),
                 dict(name='activo', label='Activa', type='bool', col=6)],
         form_extra_html="""
        <div class="alert alert-secondary py-2" name="codigo_preview">
            {% if mobj %}<b>{{ mobj.codigo }}</b> · nivel {{ mobj.nivel }}<br><span class="small">{{ mobj.get_ruta }}</span>{% else %}Escriba el código para ver cómo queda.{% endif %}
        </div>
""",
         form_extra_js="""
    {% if not mobj %}
    plancuenta_preview_timer = null;
    plancuenta_preview = () => {
        let gbe = new FormData();
        gbe.append('module', 'Contabilidad');
        gbe.append('package', 'mng_contabilidad');
        gbe.append('attr', 'MContabilidad');
        gbe.append('mname', 'preview_codigo');
        gbe.append('dbcon', 'default');
        gbe.append('codigo', qelem('#form_plancuenta_{{ rr }} input[name=codigo]').value);
        axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
            let box = qelem('#form_plancuenta_{{ rr }} [name=codigo_preview]');
            let d = rsp.data, esc = (v) => $('<span>').text(v == null ? '' : v).html();
            let tipoSel = qelem('#form_plancuenta_{{ rr }} select[name=tipo]');
            if (d.error) { box.className = 'alert alert-danger py-2'; box.innerHTML = esc(d.error) + ` <span class="small">(formato ${esc(d.formato)})</span>`; return; }
            if (!d.codigo) { box.className = 'alert alert-secondary py-2'; box.textContent = 'Escriba el código para ver cómo queda.'; return; }
            let padre = d.padre === null ? '<span class="text-danger">La cuenta padre no existe: créela primero.</span>' :
                        (d.padre ? `Cuelga de: <b>${esc(d.padre)}</b>` : 'Cuenta de primer nivel: elija el tipo.');
            box.className = 'alert py-2 ' + (d.existente ? 'alert-warning' : (d.padre === null ? 'alert-danger' : 'alert-info'));
            box.innerHTML = `<b class="font-monospace">${d.codigo}</b> · nivel ${d.nivel}<br><span class="small">${padre}${d.existente ? ' · <b>Ya existe:</b> ' + esc(d.existente) : ''}</span>`;
            tipoSel.disabled = !!d.padre;
            if (d.tipo) tipoSel.value = d.tipo;
        });
    }
    qelem('#form_plancuenta_{{ rr }} input[name=codigo]').addEventListener('input', () => {
        clearTimeout(plancuenta_preview_timer);
        plancuenta_preview_timer = setTimeout(plancuenta_preview, 300);
    });
    {% else %}
    qelem('#form_plancuenta_{{ rr }} select[name=tipo]').disabled = true;
    {% endif %}
"""),

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
