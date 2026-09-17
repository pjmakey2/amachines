"""Genera templates lista+formulario con el patron de ProductoUi/MarcaCreateUi."""
import json, os, sys

def col(idx, tit, dtyp='str', cls='align-left', render=None, btyp='fdb', hide=False):
    r = f",\n                 render: (data, type, rowobj) => {{ {render} }}" if render else ''
    return f"""              {{ fdis: true, gre: true, btyp: '{btyp}', idx: '{idx}', tit: '{tit}', cls: '{cls}', dtyp: '{dtyp}', hide: {str(hide).lower()}{r} }},"""

MONEY = "return UiN.formatNumberU(parseFloat(data || 0).toFixed(0));"
ESTADO_BADGE = ("if (rowobj.anulado) return '<span class=\"badge bg-dark\">Anulado</span>';"
                " let c = {cargado: 'bg-secondary', verificado: 'bg-info', aprobado: 'bg-success'}[data] || 'bg-primary';"
                " return `<span class=\"badge ${c}\">${data}</span>`;")
WORKFLOW_ACC = ('<i title="Avanzar al siguiente estado" class="tr-{k}-avanzar text fs-5 mdi mdi-check-decagram text-success cursor-pointer me-1"></i>'
                '<i title="Anular" class="tr-{k}-anular text fs-5 mdi mdi-cancel text-danger cursor-pointer me-1"></i>'
                '<i title="Historial" class="tr-{k}-log text fs-5 mdi mdi-history text-muted cursor-pointer me-1"></i>')


def workflow_js(app, k, M, estados=('cargado', 'verificado', 'aprobado')):
    siguiente_map = json.dumps({a: b for a, b in zip(estados, estados[1:])})
    return """
    {k}_workflow = (mname, rowobj, extra) => {{
        let gbe = new FormData();
        gbe.append('module', 'OptsIO');
        gbe.append('package', 'mng_workflow');
        gbe.append('attr', 'MWorkflow');
        gbe.append('mname', mname);
        gbe.append('dbcon', 'default');
        gbe.append('model_app_name', '{app}');
        gbe.append('model_name', '{M}');
        gbe.append('id', rowobj.id);
        Object.keys(extra || {{}}).forEach((key) => gbe.append(key, extra[key]));
        return axios.post('{{% url "iom" %}}', gbe, {{ headers: {{'X-CSRFToken': OptsIO.getCookie('csrftoken')}} }}).then((rsp) => {{
            if (rsp.data.error) UiB.MsgError(rsp.data.error);
            else if (rsp.data.success && mname !== 'get_log') UiB.MsgSuccess(rsp.data.success);
            if (mname !== 'get_log') $(`#${{t_{k}}}`).DataTable().ajax.reload(null, false);
            return rsp.data;
        }});
    }}

    $(`#${{t_{k}}} tbody`).on('click', '.tr-{k}-avanzar', function() {{
        let rowobj = $(`#${{t_{k}}}`).DataTable().row($(this).closest('tr')).data();
        let siguiente = {siguiente_map}[rowobj.estado];
        if (rowobj.anulado || !siguiente) {{
            UiB.MsgInfo('La operación ya está cerrada.');
            return;
        }}
        UiB.MsgSwall({{ msg: `¿Pasar la operación ${{rowobj.numero}} a "${{siguiente}}"?`, ttype: 'info' }}).then((result) => {{
            if (result.isConfirmed) {k}_workflow('avanzar', rowobj, {{estado: siguiente}});
        }});
    }})

    $(`#${{t_{k}}} tbody`).on('click', '.tr-{k}-anular', function() {{
        let rowobj = $(`#${{t_{k}}}`).DataTable().row($(this).closest('tr')).data();
        Swal.fire({{
            title: `Anular operación ${{rowobj.numero}}`, input: 'text', inputLabel: 'Motivo',
            showCancelButton: true, confirmButtonText: 'Anular', cancelButtonText: 'Cancelar'
        }}).then((result) => {{
            if (result.isConfirmed) {k}_workflow('anular', rowobj, {{motivo: result.value || ''}});
        }});
    }})

    $(`#${{t_{k}}} tbody`).on('click', '.tr-{k}-log', function() {{
        let rowobj = $(`#${{t_{k}}}`).DataTable().row($(this).closest('tr')).data();
        {k}_workflow('get_log', rowobj).then((data) => {{
            if (!data.log) return;
            let filas = data.log.map((l) => `<tr><td>${{l.fecha}}</td><td>${{l.estado}}</td><td>${{$('<span>').text(l.usuario || l.username).html()}}</td><td>${{$('<span>').text(l.nota || '').html()}}</td></tr>`);
            Swal.fire({{
                title: `Historial operación ${{rowobj.numero}}`, width: 700,
                html: `<table class="table table-sm text-start"><thead><tr><th>Fecha</th><th>Estado</th><th>Usuario</th><th>Nota</th></tr></thead><tbody>${{filas.join('')}}</tbody></table>`
            }});
        }});
    }})
""".format(k=k, app=app, M=M, siguiente_map=siguiente_map)
BOOL = "return data ? 'Sí' : 'No';"

def list_tmpl(app, s):
    k, M = s['key'], s['model']
    cols = '\n'.join(s['cols'])
    searches = '\n'.join(
        f"                gmquery_{k}.push({{'field': 'or_{f}__icontains', 'value': v}});" for f in s['search'])
    mquery = json.dumps(s.get('mquery', []))
    can_create = s.get('create', True)
    can_delete = s.get('delete', True)
    if s.get('workflow'):
        can_delete = False
        s = dict(s, acc=s.get('acc', f'<i title="Ver/Editar" class="tr-{k}-query text fs-5 mdi mdi-archive-eye-outline me-1"></i>') + WORKFLOW_ACC.format(k=k),
                 extra_js=workflow_js(app, k, M, s.get('workflow_states', ('cargado', 'verificado', 'aprobado'))) + s.get('extra_js', ''))
        cols = cols + "\n" + col('anulado', 'Anulado', 'bool', hide=True)
    btns = ''
    if can_create:
        btns += f"""            <button id="btn_crear_{k}" class="btn btn-primary me-2"><i class="mdi mdi-plus"></i> {s.get('create_label', 'Crear')}</button>\n"""
    if can_delete:
        btns += f"""            <button id="btn_borrar_{k}" class="btn btn-danger"><i class="mdi mdi-delete"></i> {s.get('delete_label', 'Borrar')}</button>\n"""
    acc = f"""               {{ fdis: true, gre: false, btyp: 'loc', idx: null, tit: 'ACC', dtyp: 'str', dfl: '', nord: false,
                dfcon: `{s.get('acc', f'<i title="Ver/Editar" class="tr-{k}-query text fs-5 mdi mdi-archive-eye-outline"></i>')}` }},"""
    out = f"""<div class="{k}_ui_container container-fluid">
    <div class="toolbar mb-3 d-flex justify-content-between align-items-center">
        <div class="toolbar-buttons">
{btns}{s.get('toolbar_extra', '')}        </div>
        <div class="toolbar-search">
            <input type="text" id="input_buscar_{k}" class="form-control" placeholder="Buscar...">
        </div>
    </div>
    <div id="table_{k}_ui"></div>
</div>
<script type="text/javascript">
    var gmquery_{k} = [];
    {k}_home_be = function (data, settings) {{
        let tt = qelem(`#table_{k}_ui`);
        tt.classList.add('overlay-container');
        tt.classList.add('overlay');
        let crdata = Object.assign({{}}, settings.ajax.initquery);
        let mquery = {mquery};
        if (gmquery_{k}.length > 0) mquery = [...mquery, ...gmquery_{k}];
        if (mquery.length > 0) crdata.mquery = jfy(mquery);
        return Object.assign(data, crdata);
    }}
    t_{k} = `dtable_${{OptsIO.s4generate()}}`;
    Grid.datatables_wrapper({{
          t_guid: t_{k},
          url_exec: '{{% url "iom" %}}',
          title: '{s['title']}',
          tselector: 'table_{k}_ui',
          app_name: '{app}',
          model_name: '{M}',
          cls_table: 'cell-border row-border table table-sm',
          cls_thead: 'border-gray-900',
          mquery: [],
          plength: 100,
          builder_be: {k}_home_be,
          t_opts: {{
              select: true,
              fixedHeader: true,
              responsive: null,
              scrollCollapse: true,
              scrollX: true,
              scrollY: 600,
              paging: true,
              order: [[{s.get('order_col', 1)}, '{s.get('order_dir', 'asc')}']],
              rowId: function(row, se) {{ return `tr_{k}_${{row.id}}` }}
          }},
          columns: [
{acc}
{cols}
          ]
      }})
"""
    if can_create or s.get('edit'):
        out += f"""
    {k}_form_crud = (pk) => {{
        let dattrs = {{ title: '{s['title']}', t_guid: t_{k}, sui_rr: '{{{{ rr }}}}', offcanvasglobal: true }};
        let tps = {{
            model_app_name: '{app}',
            model_name: '{M}',
            dbcon: 'default',
            url: '{{% url "dtmpl" %}}',
            dattrs: dattrs,
            template: '{app}/{M}CreateUi.html',
            raw: true,
        }}
        if (pk) tps['pk'] = pk;
        OptsIO.getTmpl(tps).then((rsp) => {{
            $('#offcanvasGlobalUiBody').html(rsp.data);
            new bootstrap.Offcanvas('#offcanvasGlobalUi').show();
            document.getElementById('offcanvasGlobalUi').addEventListener('hidden.bs.offcanvas', () => {{
                $('#offcanvasGlobalUiBody').html('');
            }}, {{ once: true }})
            UiB.kILLLoaderAjax();
        }})
    }}

"""
        if can_create:
            out += f"""
    qelem('#btn_crear_{k}').addEventListener('click', () => {k}_form_crud());
"""
        if s.get('editable', True):
            out += f"""
    $(`#${{t_{k}}} tbody`).on('click', '.tr-{k}-query', function() {{
        let rowobj = $(`#${{t_{k}}}`).DataTable().row($(this).closest('tr')).data();
        {k}_form_crud(rowobj.id);
    }})
"""
    if can_delete:
        extra = ''.join(f"\n            gbe.append('{a}', '{b}');" for a, b in s.get('delete_extra', {}).items())
        out += f"""
    qelem('#btn_borrar_{k}').addEventListener('click', function() {{
        let ids = $(`#${{t_{k}}}`).DataTable().rows({{ selected: true }}).data().toArray().map(row => row.id);
        if (ids.length === 0) {{
            UiB.MsgError('Por favor, selecciona al menos un registro.');
            return;
        }}
        UiB.MsgSwall({{
            msg: `{s.get('delete_msg', '¿Borrar ${ids.length} registro(s)? Esta acción no se puede deshacer.')}`,
            ttype: 'info'
        }}).then((result) => {{
            if (!result.isConfirmed) return;
            let gbe = new FormData();
            gbe.append('module', '{app}');
            gbe.append('package', '{s['pkg']}');
            gbe.append('attr', '{s['attr']}');
            gbe.append('mname', '{s.get('delete_mname', 'delete_catalogo')}');
            gbe.append('dbcon', 'default');
            gbe.append('ids', jfy(ids));{extra}
            axios.post('{{% url "iom" %}}', gbe, {{ headers: {{'X-CSRFToken': OptsIO.getCookie('csrftoken')}} }}).then((rsp) => {{
                UiB.BeMsgHandle({{ rsps: rsp.data.msgs, timer: 2000, offcanvasglobal: true }});
                $(`#${{t_{k}}}`).DataTable().ajax.reload();
            }}).catch((err) => {{
                log.error(`Error: ${{jfy(err)}}`);
                UiB.MsgError('Ocurrió un error. Por favor, intenta de nuevo.');
            }});
        }});
    }});
"""
    out += s.get('extra_js', '')
    out += f"""
    qelem('#input_buscar_{k}').onkeydown = (evt) => {{
        if (evt.key === 'Enter') {{
            gmquery_{k} = [];
            let v = qelem('#input_buscar_{k}').value.trim();
            if (v !== '') {{
{searches}
            }}
            $(`#${{t_{k}}}`).DataTable().ajax.reload();
        }}
    }}

    $(`#${{t_{k}}}`).on('draw.dt', function() {{
        let tt = qelem(`#table_{k}_ui`);
        tt.classList.remove('overlay-container');
        tt.classList.remove('overlay');
    }})
</script>
"""
    return out


def field_html(k, f):
    n, label, typ = f['name'], f['label'], f['type']
    req = ' required' if f.get('required') else ''
    star = ' <span class="text-danger">*</span>' if f.get('required') else ''
    w = f.get('col', 6)
    ro = ' {% if mobj %}readonly{% endif %}' if f.get('readonly_on_edit') else ''
    if typ == 'color':
        inner = f"""<input type="color" name="{n}" class="form-control form-control-color" value='{{% if mobj %}}{{{{ mobj.{n} }}}}{{% else %}}{f.get('default', '#000000')}{{% endif %}}' />"""
    elif typ == 'textarea':
        inner = f"""<textarea name="{n}" class="form-control" rows="{f.get('rows', 4)}" placeholder="{f.get('ph', '')}">{{% if mobj %}}{{{{ mobj.{n} }}}}{{% endif %}}</textarea>"""
    elif typ in ('text', 'number', 'date'):
        default = f.get('default', '')
        if typ == 'date':
            val = f"""{{% if mobj %}}{{{{ mobj.{n}|date:"Y-m-d" }}}}{{% else %}}{{% now "Y-m-d" %}}{{% endif %}}""" if f.get('today') else f"""{{% if mobj %}}{{{{ mobj.{n}|date:"Y-m-d" }}}}{{% endif %}}"""
        elif typ == 'number':
            val = f"""{{% if mobj %}}{{{{ mobj.{n}|floatformat:"-2"|cut:"." |cut:" " }}}}{{% else %}}{default}{{% endif %}}""" if False else f"""{{% if mobj %}}{{{{ mobj.{n}|stringformat:"s" }}}}{{% else %}}{default}{{% endif %}}"""
        else:
            val = f"""{{% if mobj %}}{{{{ mobj.{n} }}}}{{% else %}}{default}{{% endif %}}"""
        # Directriz crud_patterm: numericos siempre type=text + Inputmask
        itype = 'text' if typ == 'number' else typ
        extra_cls = ' text-end' if typ == 'number' else ''
        inner = f"""<input type="{itype}" name="{n}" class="form-control{extra_cls}" placeholder="{f.get('ph', '')}" value='{val}'{req}{ro} />"""
    elif typ == 'select':
        opts = '\n'.join(
            f"""                        <option value="{v}" {{% if mobj and mobj.{n} == "{v}" %}}selected{{% endif %}}>{t}</option>"""
            for v, t in f['options'])
        inner = f"""<select name="{n}" class="form-control"{req}>\n{opts}\n                    </select>"""
    elif typ == 'bool':
        inner = f"""<select name="{n}" class="form-control">
                        <option value="true" {{% if not mobj or mobj.{n} %}}selected{{% endif %}}>Sí</option>
                        <option value="false" {{% if mobj and not mobj.{n} %}}selected{{% endif %}}>No</option>
                    </select>"""
    elif typ == 'file':
        inner = f"""<input type="file" name="{n}" class="form-control" />"""
        if f.get('link', True):
            help_link = f"""{{% if mobj and mobj.{n} %}}<a href="{{{{ mobj.{n}.url }}}}" target="_blank">Ver archivo actual</a>{{% endif %}}"""
            f = dict(f, help=(f.get('help', '') + ' ' + help_link).strip())
    elif typ == 'section':
        return f"""            <div class="col-md-12" data-field="{n}"><h6 class="border-bottom pb-1 mt-2">{label}</h6></div>"""
    elif typ == 'fk':
        inner = f"""<select name="{n}" class="form-control"{req}>
                        <option value="">Seleccione...</option>
                    </select>"""
    help_ = f"""\n                <small class="text-muted">{f['help']}</small>""" if f.get('help') else ''
    return f"""            <div class="col-md-{w} mb-3" data-field="{n}">
                <label>{label}{star}</label>
                <div class="input-group flex-nowrap am_focus_highlight">
                    {inner}
                </div>{help_}
            </div>"""


def form_tmpl(app, s):
    k, M = s['key'], s['model']
    fields = '\n'.join(field_html(k, f) for f in s['fields'])
    s = dict(s, fields=[f for f in s['fields'] if f['type'] != 'section'])
    fks = [f for f in s['fields'] if f['type'] == 'fk']
    pop = ''
    for f in fks:
        if f.get('no_populate'):
            continue  # el spec lo resuelve con busqueda ajax (se_select) en form_extra_js
        attr = f['name'][:-3]
        disp = f.get('display', ['nombre'])
        methods = f.get('methods', [])
        pop += f"""
    form_search.se_populate({{
        surl: '{{% url "iom" %}}',
        dele: '#form_{k}_{{{{ rr }}}} select[name={f['name']}]',
        app_name: '{f.get('app', app)}',
        model_name: '{f['fk_model']}',
        field_display: {json.dumps(disp)},
        field_id: ['id'],
        db_fields: {json.dumps(f.get('db_fields', ['id'] + [d for d in disp if d not in methods]))},
        db_methods: {json.dumps(methods)},
        qs_be: {json.dumps(f.get('qs', [{'field': 'activo', 'value': True}]))},
        dbcon: 'default',
        headers: {{'X-CSRFToken': OptsIO.getCookie('csrftoken')}},
        first_selected: false,
        allowClear: {str(not f.get('required', False)).lower()},
        width: '100%',
        dropdownParent: {{% if en_modal %}}$('.swal2-container'){{% else %}}$('#offcanvasGlobalUi'){{% endif %}},
        theme: 'bootstrap-5'
    }}).then(() => {{
        {{% if mobj and mobj.{attr} %}}
            $('#form_{k}_{{{{ rr }}}} select[name={f['name']}]').val('{{{{ mobj.{attr}.id }}}}').trigger('change');
        {{% endif %}}
    }});
"""
    nums = [f for f in s['fields'] if f['type'] == 'number']
    if nums:
        pop += """
    initializeInputMasks_%s = () => {
        let maskDecimal = {
            alias: 'numeric', groupSeparator: ',', radixPoint: '.', autoGroup: true, digits: 2,
            digitsOptional: false, rightAlign: true, allowMinus: false,
            removeMaskOnSubmit: true, autoUnmask: true
        };
        let maskEntero = Object.assign({}, maskDecimal, { digits: 0, groupSeparator: '', autoGroup: false });
""" % k
        for f in nums:
            m = 'maskEntero' if f.get('integer') else 'maskDecimal'
            pop += f"""        Inputmask({m}).mask(qelem('#form_{k}_{{{{ rr }}}} input[name={f['name']}]'));\n"""
        pop += f"""    }}
    initializeInputMasks_{k}();
"""
    c_a = '[]'
    if s.get('c_a'):
        c_a = f"""[{{ 'module': '{app}', 'package': '{s['pkg']}', 'attr': '{s['attr']}', 'mname': '{s['c_a']}', 'cont': false, 'show_success': true }}]"""
    seldis = json.dumps([f['name'] for f in fks])
    filenames = json.dumps([f['name'] for f in s['fields'] if f['type'] == 'file'])
    numnames = json.dumps([f['name'] for f in s['fields'] if f['type'] == 'number'])
    return f"""<div class="ui_{k}">
    <form id="form_{k}_{{{{ rr }}}}" class="form_{k}">
        <input type="hidden" name="id" {{% if mobj %}} value="{{{{ mobj.pk }}}}" {{% endif %}}>
        <div class="row">
{fields}
        </div>
{s.get('form_extra_html', '')}
        <div class="row mt-2">
            <div class="col-md-12 text-start">
                <button class="btn btn-primary" type="submit">Guardar</button>
            </div>
        </div>
    </form>
</div>
<script type="text/javascript">
    {{% if not en_modal %}}qelem('#offcanvasGlobalUiLabel').innerHTML = `{{% if mobj %}}Modificar {s['singular']} {{{{ mobj.pk }}}}{{% else %}}{s.get('create_title', 'Crear ' + s['singular'])}{{% endif %}}`;{{% endif %}}
{pop}
    save_{k} = (target) => {{
        let fdata = new FormData();
        fdata.append('module', 'OptsIO');
        fdata.append('package', 'io_maction');
        fdata.append('attr', 'IOMaction');
        fdata.append('mname', 'process_record');
        fdata.append('model_app_name', '{app}');
        fdata.append('model_name', '{M}');
        fdata.append('dbcon', 'default');
        let edata = form_serials.form_to_json(new FormData(target));
        {seldis}.forEach((idx) => {{
            let vv = $(`#form_{k}_{{{{ rr }}}} select[name=${{idx}}]`).val();
            if (vv !== undefined) edata[idx] = vv;
        }});
        // Leer valores sin mascara directamente del inputmask (el backend recibe punto decimal)
        {numnames}.forEach((f) => {{
            let el = qelem(`#form_{k}_{{{{ rr }}}} input[name=${{f}}]`);
            if (el && el.inputmask) edata[f] = el.inputmask.unmaskedvalue().replace(',', '.');
        }});
        {filenames}.forEach((f) => {{
            let el = qelem(`#form_{k}_{{{{ rr }}}} input[name=${{f}}]`);
            delete edata[f];
            if (el && el.files.length > 0) fdata.append(f, el.files[0]);
        }});
        {s.get('before_save_js', '')}
        fdata.append('uc_fields', jfy(edata));
        fdata.append('b_vals', jfy([]));
        fdata.append('c_a', jfy({c_a}));
        fdata.append('a_vals', jfy([]));
        let fele = document.querySelector('#form_{k}_{{{{ rr }}}}');
        fele.classList.add('overlay-container');
        fele.classList.add('overlay');
        return axios.post('{{% url "iom" %}}', fdata, {{ headers: {{ 'X-CSRFToken': OptsIO.getCookie('csrftoken') }} }})
        .then((rsp) => {{
            let msgs = rsp.data.hasOwnProperty('msgs') ? rsp.data.msgs : [rsp.data];
            let got_error = msgs.some((ee) => ee.error);
            UiB.BeMsgHandle({{ rsps: msgs, timer: 2000, offcanvasglobal: {{% if en_modal %}}false{{% else %}}true{{% endif %}} }});
            if (!got_error) {{
                $('#{{{{ t_guid }}}}').DataTable().ajax.reload();
                {s.get('after_save_js', '')}
            }}
        }}).catch((err) => {{
            log.error(`#form_{k} Error in save record: ` + JSON.stringify(err, null, 2));
            UiB.MsgError(err);
        }}).finally(() => {{
            let ft = document.querySelector('#form_{k}_{{{{ rr }}}}');
            if (ft) {{
                ft.classList.remove('overlay-container');
                ft.classList.remove('overlay');
            }}
        }});
    }}

    qelem('#form_{k}_{{{{ rr }}}}').addEventListener('submit', (evt) => {{
        evt.preventDefault();
        save_{k}(evt.target);
    }})
{s.get('form_extra_js', '')}</script>
"""


def generate(app, specs, outdir):
    os.makedirs(outdir, exist_ok=True)
    for s in specs:
        open(os.path.join(outdir, f"{s['model']}Ui.html"), 'w').write(list_tmpl(app, s))
        if s.get('fields'):
            open(os.path.join(outdir, f"{s['model']}CreateUi.html"), 'w').write(form_tmpl(app, s))
        print('generated', s['model'])
