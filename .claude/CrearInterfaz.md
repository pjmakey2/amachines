# Crear Interfaces en Amachine

Guía paso a paso para crear interfaces en el sistema, basada en el patrón de `DocumentHeaderUi.html` (listado) y `DocumentHeaderCreateUi.html` (formulario).

Hay dos tipos básicos de interfaz:

- **Listado/Home UI** — tabla con datos + toolbar. Se registra como `App` en el menú.
- **Create/Edit UI** — formulario que se abre desde el listado en un offcanvas, para crear o editar un registro.

---

## 1. Listado (Home UI)

### Estructura mínima del template

```html
<div class="mimodel_ui_container container-fluid">
    <div class="mimodel_ui_msgs"></div>

    <!-- Toolbar -->
    <div class="toolbar mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
        <div class="toolbar-buttons d-flex align-items-center gap-2">
            <button id="btn_crear_mimodel" class="btn btn-primary">
                <i class="mdi mdi-plus"></i> Crear
            </button>
            <button id="btn_borrar_mimodel" class="btn btn-danger">
                <i class="mdi mdi-delete"></i> Borrar
            </button>
        </div>
        <div class="toolbar-search">
            <input type="text" id="input_buscar_mimodel" class="form-control am_input" placeholder="Buscar...">
        </div>
    </div>

    <div id="table_mimodel_ui"></div>
</div>

<script type="text/javascript">
    var gmquery = [];

    // Builder: modifica los params de cada request (filtros, mquery)
    mimodel_home_be = function(data, settings) {
        let tt = qelem(`#table_mimodel_ui`);
        tt.classList.add('overlay-container', 'overlay');
        let crdata = Object.assign({}, settings.ajax.initquery);
        let mquery = [];
        if (gmquery.length > 0) {
            mquery = [...mquery, ...gmquery];
        }
        if (mquery.length > 0) crdata.mquery = jfy(mquery);
        return Object.assign(data, crdata);
    }

    // Crea el DataTable con id único
    let t_mimodel = `dtable_${OptsIO.s4generate()}`;
    Grid.datatables_wrapper({
        t_guid: t_mimodel,
        url_exec: '{% url "iom" %}',
        title: 'Mi Listado',
        tselector: 'table_mimodel_ui',
        app_name: 'MiApp',
        model_name: 'MiModel',
        cls_table: 'cell-border row-border table table-sm',
        mquery: [],
        plength: 100,
        builder_be: mimodel_home_be,
        t_opts: {
            select: true,
            fixedHeader: true,
            scrollX: true,
            scrollY: 600,
            paging: true,
            order: [[1, 'desc']],
            rowId: row => `tr_mimodel_${row.id}`
        },
        columns: [
            // Columna de acciones
            { fdis: true, gre: false, btyp: 'loc', idx: null, tit: 'ACC', dtyp: 'str', dfl: '', nord: false,
              render: (data, type, rowobj) => {
                  let icons = `<i title="Ver/Editar" class="tr-mimodel-query fs-5 mdi mdi-archive-eye-outline me-2"></i>`;
                  return icons;
              }
            },
            // Columnas de datos
            { fdis: true, gre: true, btyp: 'fdb', idx: 'nombre', tit: 'Nombre', cls: 'align-left', dtyp: 'str' },
            { fdis: true, gre: true, btyp: 'fdb', idx: 'fecha', tit: 'Fecha', cls: 'align-left', dtyp: 'date',
              render: (data) => moment(data).format('DD/MM/YY')
            },
            { fdis: true, gre: true, btyp: 'fdb', idx: 'total', tit: 'Total', cls: 'align-right', dtyp: 'float',
              render: (data) => UiN.formatNumberU(parseFloat(data || 0).toFixed(0))
            },
            // Columnas ocultas (necesarias si el render las referencia)
            { fdis: true, gre: true, btyp: 'fdb', idx: 'estado', tit: 'estado', dtyp: 'str', hide: true },
        ]
    });

    // Click handlers
    $(`#${t_mimodel} tbody`).on('click', '.tr-mimodel-query', function() {
        let rowobj = $(`#${t_mimodel}`).DataTable().row($(this).closest('tr')).data();
        mimodel_form(rowobj.id);
    });

    qelem('#btn_crear_mimodel').addEventListener('click', () => mimodel_form());
    qelem('#btn_borrar_mimodel').addEventListener('click', () => { /* ver abajo */ });

    // Abre el form de crear/editar en un offcanvas
    mimodel_form = (pk) => {
        let dattrs = { title: 'Crear', t_guid: t_mimodel, sui_rr: '{{ rr }}', offcanvasglobal: true };
        let tps = {
            model_app_name: 'MiApp',
            model_name: 'MiModel',
            dbcon: 'default',
            url: '{% url "dtmpl" %}',
            dattrs: dattrs,
            template: 'MiApp/MiModelCreateUi.html',
            raw: true
        };
        if (pk) { tps.pk = pk; dattrs.title = 'Editar'; }
        OptsIO.getTmpl(tps).then((rsp) => {
            $('#offcanvasGlobalUiBody').html(rsp.data);
            new bootstrap.Offcanvas('#offcanvasGlobalUi').show();
            document.getElementById('offcanvasGlobalUi').addEventListener('hidden.bs.offcanvas', () =>
                $('#offcanvasGlobalUiBody').html('')
            );
            UiB.kILLLoaderAjax();
        });
    }

    // Búsqueda
    qelem('#input_buscar_mimodel').onkeydown = (evt) => {
        if (evt.key === 'Enter') {
            gmquery = [];
            let val = qelem('#input_buscar_mimodel').value.trim();
            if (val) gmquery.push({field: 'or_nombre__icontains', value: val});
            $(`#${t_mimodel}`).DataTable().ajax.reload();
        }
    }

    // Limpia overlay tras cada redraw
    $(`#${t_mimodel}`).on('draw.dt', function() {
        qelem(`#table_mimodel_ui`).classList.remove('overlay-container', 'overlay');
    });
</script>
```

### Claves de las columnas del Grid

| Prop | Descripción |
|------|-------------|
| `fdis` | Si `true`, el campo se muestra en el form de búsqueda avanzada |
| `gre` | Si `true`, se incluye en el SELECT |
| `btyp` | `fdb` (field de DB), `mdb` (multi-field), `loc` (columna virtual/local) |
| `idx` | Nombre del campo en el modelo Django (o null si es virtual) |
| `tit` | Título visible en el header |
| `cls` | Clase CSS alineación: `align-left`, `align-right`, `align-center` |
| `dtyp` | Tipo: `str`, `int`, `float`, `date`, `bool` |
| `hide` | `true` oculta la columna pero trae el dato (útil para render) |
| `nord` | `true` desactiva ordenamiento |
| `render` | Función para customizar el HTML de la celda |
| `dfcon` | HTML default cuando la celda no tiene data |

### Filtros programáticos (`mquery`)

`mquery` es un array que se serializa y va como filtro al backend. Formatos:

```javascript
mquery.push({field: 'estado', value: 'Aprobado'});            // igualdad
mquery.push({field: 'estado__isnull', value: true});          // is null
mquery.push({field: 'or_nombre__icontains', value: 'juan'});  // OR + LIKE (prefijo or_)
mquery.push({field: 'fecha__gte', value: '2026-01-01'});      // rangos
```

---

## 2. Formulario (Create/Edit UI)

### Convenciones

- **Id único `{{ rr }}`**: cada template renderizado recibe un hash aleatorio para evitar colisiones cuando se abren múltiples forms. Usar `id="form_mimodel_{{ rr }}"`.
- **`mobj`**: si se abre el form con `pk`, Django inyecta `mobj = Model.objects.get(pk=pk)` al contexto.
- **Hidden inputs**: usar `type="hidden"` para valores fijos (`source`, `doc_tipo`, etc) y el `id` en modo edición.

### Estructura mínima

```html
<div class="ui_mimodel">
    <form id="form_mimodel_{{ rr }}" class="form_mimodel">
        {% if mobj %}
            <input type="hidden" name="id" value="{{ mobj.pk }}">
        {% endif %}
        <input type="hidden" name="source" value="MANUAL">

        <div class="row mt-2">
            <div class="col-md-4">
                <div class="form-floating form-floating-sm">
                    <input required type="text" name="nombre" class="form-control"
                           placeholder="Nombre"
                           {% if mobj %} value="{{ mobj.nombre }}" {% endif %}>
                    <label>Nombre</label>
                </div>
            </div>
            <div class="col-md-3">
                <div class="form-floating form-floating-sm">
                    <select required name="estado" class="form-select">
                        <option value="A" {% if mobj.estado == 'A' %}selected{% endif %}>Activo</option>
                        <option value="I" {% if mobj.estado == 'I' %}selected{% endif %}>Inactivo</option>
                    </select>
                    <label>Estado</label>
                </div>
            </div>
        </div>

        <div class="d-flex gap-2 mt-3">
            <button type="submit" id="btn_guardar" class="btn btn-primary">Guardar</button>
            <button type="submit" id="btn_enviar" class="btn btn-success">Guardar y Enviar</button>
        </div>
    </form>
</div>

<script type="text/javascript">
    save_mimodel = (target, btn_submitter_id) => {
        let fdata = new FormData();
        fdata.append('module', 'OptsIO');
        fdata.append('package', 'io_maction');
        fdata.append('attr', 'IOMaction');
        fdata.append('mname', 'process_record');
        fdata.append('model_app_name', 'MiApp');
        fdata.append('model_name', 'MiModel');
        fdata.append('dbcon', 'default');

        // Serializar el form a dict JSON
        let formData = new FormData(target);
        let edata = form_serials.form_to_json(formData);

        // Distinguir botón submitter (opcional)
        if (btn_submitter_id === 'btn_enviar') {
            edata['send_save'] = true;
        }

        fdata.append('uc_fields', jfy(edata));
        fdata.append('b_vals', jfy([]));
        // c_a: chain_action — métodos Python a ejecutar en cadena con los datos
        fdata.append('c_a', jfy([{
            module: 'MiApp',
            package: 'mng_mimodel',
            attr: 'MMimodel',
            mname: 'create_mimodel',
            cont: false,
            show_success: true
        }]));
        fdata.append('a_vals', jfy([]));

        // Overlay
        let ft = document.querySelector('#form_mimodel_{{ rr }}');
        ft.classList.add('overlay-container', 'overlay');

        return axios.post('{% url "iom" %}', fdata, {
            headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')}
        }).then((rsp) => {
            let msgs = rsp.data.msgs || [rsp.data];
            let got_error = msgs.some(m => m.error);
            UiB.BeMsgHandle({rsps: msgs, timer: 2000, offcanvasglobal: true});
            if (!got_error) {
                $('#{{ t_guid }}').DataTable().ajax.reload();
            }
        }).catch((err) => UiB.MsgError(err))
          .finally(() => ft.classList.remove('overlay-container', 'overlay'));
    }

    qelem('#form_mimodel_{{ rr }}').addEventListener('submit', (evt) => {
        evt.preventDefault();
        let btn_id = evt.submitter.attributes['id'].value;
        save_mimodel(event.target, btn_id);
    });
</script>
```

### Patrón `process_record` + `c_a` (chain actions)

El patrón estándar usa `OptsIO.io_maction.IOMaction.process_record` como orquestador:

1. `uc_fields` → JSON con los datos del form (lo que el usuario editó)
2. `c_a` → lista de métodos Python a ejecutar con `uc_fields` como input
3. Cada método recibe `kwargs['qdict']` con los datos y retorna `dict` con `success` o `error`

Ejemplo de método en el backend (`mng_mimodel.py`):
```python
class MMimodel:
    def create_mimodel(self, *args, **kwargs) -> tuple:
        q = kwargs.get('qdict', {})
        uc_fields = from_json(q.get('uc_fields', {}))
        pk = uc_fields.get('id')
        if pk:
            MiModel.objects.filter(pk=pk).update(**uc_fields)
            return {'success': 'Actualizado'}, args, kwargs
        obj = MiModel.objects.create(**uc_fields)
        return {'success': f'Creado pk={obj.pk}'}, args, kwargs
```

Ver `.claude/axios_backend_calls.md` para detalles del endpoint `iom`.

---

## 3. Registrar la app en el menú

Agregar entrada en `Apps` (tabla de aplicaciones del menú) — usar management command o admin:

```python
Apps.objects.create(
    prioridad=1,
    menu='MiMenu',
    menu_icon='mdi mdi-folder',
    app_name='mimodel_home',
    friendly_name='Mi Modelo',
    icon='mdi mdi-list',
    url='MiApp/MiModelUi.html',   # path del template
    version='1.0',
    background='#4f46e5',
    active=True
)
```

El `url` es el path relativo al folder `templates/`. El sistema lo renderiza vía `dtmpl` al hacer click en el menú.

---

## 4. Flujo completo — checklist

Para agregar una pantalla nueva para un modelo `MiModel`:

1. **Template listado**: `templates/MiApp/MiModelUi.html`
2. **Template form**: `templates/MiApp/MiModelCreateUi.html`
3. **Backend logic**: `MiApp/mng_mimodel.py` con clase `MMimodel` y métodos `create_mimodel`, `delete_*`, validaciones, etc.
4. **Registrar en `Apps`**: crear entrada en la tabla del menú
5. **Probar**: navegar al menú → listado → crear/editar abre el offcanvas → save recarga el listado

---

## 5. Componentes reutilizables

| Componente | Uso |
|-----------|-----|
| `Grid.datatables_wrapper({...})` | Wrapper de DataTables configurado con backend Django |
| `OptsIO.getTmpl({...})` | Carga templates dinámicamente vía `dtmpl` |
| `OptsIO.s4generate()` | Genera string aleatorio 4 chars (para IDs únicos) |
| `OptsIO.getCookie('csrftoken')` | Lee CSRF token |
| `form_serials.form_to_json(formData)` | Serializa un FormData a objeto JS |
| `form_validation.just_number(event)` | Fuerza solo números en un input |
| `form_input.calculate_dv(sel1, sel2)` | Calcula dígito verificador de RUC |
| `UiB.MsgSuccess/Error/Info(msg)` | Toasts |
| `UiB.MsgSwall({msg, ttype})` | SweetAlert2 de confirmación |
| `UiB.BeMsgHandle({rsps, ...})` | Muestra mensajes de respuesta del backend |
| `UiN.formatNumberU(num)` | Formato numérico (separador de miles) |
| `Inputmask({...}).mask(el)` | Máscaras de input (decimales, moneda) |
| `moment(date).format(fmt)` | Formato de fechas |

---

## 6. Offcanvas global

El sistema tiene un offcanvas reutilizable en `BaseUi.html`:

```html
<div id="offcanvasGlobalUi" class="offcanvas offcanvas-end">
    <div id="offcanvasGlobalUiBody"></div>
</div>
```

Cualquier form se inyecta en `#offcanvasGlobalUiBody`. Al cerrar (`hidden.bs.offcanvas`) se limpia el contenido automáticamente. No hay que crear un offcanvas por pantalla.

---

## 7. Tips

- Siempre usar `{{ rr }}` en IDs de elementos para evitar colisiones
- Las columnas que el `render` necesita para lógica condicional deben estar en `columns` aunque se escondan con `hide: true`
- Los filtros permanentes van en el campo `mquery: [...]` del wrapper; los filtros dinámicos en `gmquery` y se rearmman en `builder_be`
- Para operaciones simples (sin form), invocar el método directamente con `axios.post('{% url "iom" %}', fdata, ...)` en vez de abrir un form
- Recargar DataTable tras mutaciones: `$(`#${t_mimodel}`).DataTable().ajax.reload(null, false)` (el segundo arg mantiene la página actual)
