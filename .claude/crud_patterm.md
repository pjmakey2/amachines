# Contextos de Claude para AM
# Creación de CRUD para la Empresa AltaMachines


## Información

 Te proporcionaré:

 * Los modelos para los que crearemos las interfaces.
   * Así que necesitas leerlos para contexto.
 * Dónde crear los templates
   * Así que necesitas crear estos archivos si no existen
 * Qué módulos usar
   * Así que necesitas crearlos si no existen


## Directrices
  * No uses const o let en los templates que se llaman por ajax, porque esto generaría un error de que la variable ya está declarada.
  * Lee todos los archivos involucrados en la solicitud del usuario.
      Si un usuario quiere que construyas la interfaz para algunos modelos y este modelo tiene una o múltiples relaciones, debes leer la estructura de estas relaciones para saber qué y cómo usarlo.
  * Los elementos de formulario deben tener atributo name y en el código javascript la referencia al elemento debe ser por el atributo name, no por id
  * **SIEMPRE usa Inputmask para inputs numéricos** (precios, costos, cantidades, porcentajes, etc.) para mostrar números en formato humanizado:
    - Cambia `type="number"` a `type="text"` para inputs que usarán inputmask
    - La librería Inputmask ya está cargada en templates/AMJS.html
    - **CRÍTICO**: El Backend DEBE recibir punto (.) como separador decimal (60.58 NO 60,58)
    - Las propiedades `removeMaskOnSubmit: true` y `autoUnmask: true` aseguran que el backend reciba el formato correcto con punto como separador decimal

    - **Configuración estándar para campos decimales** (precios, costos, cantidades, etc.):
      ```javascript
      {
          alias: 'numeric',
          groupSeparator: ',',      // Mostrar: separador de miles (1,234.56)
          radixPoint: '.',          // Mostrar: separador decimal (1,234.56)
          autoGroup: true,
          digits: 2,                // Número de decimales
          digitsOptional: false,
          rightAlign: true,
          allowMinus: false,
          removeMaskOnSubmit: true, // CRÍTICO: Remueve formato de máscara al enviar
          autoUnmask: true          // CRÍTICO: Retorna valor sin máscara (60.58 con punto)
      }
      ```

    - Ejemplo de implementación:
      ```javascript
      function initializeInputMasks() {
          let maskOptions = {
              alias: 'numeric',
              groupSeparator: ',',
              radixPoint: '.',
              autoGroup: true,
              digits: 2,
              digitsOptional: false,
              rightAlign: true,
              allowMinus: false,
              removeMaskOnSubmit: true,
              autoUnmask: true
          };
          Inputmask(maskOptions).mask(qelem('#form_xxx_{{ rr }} input[name=precio]'));
          Inputmask(maskOptions).mask(qelem('#form_xxx_{{ rr }} input[name=costo]'));
      }

      // Inicializar máscaras al cargar
      initializeInputMasks();
      ```

    - Para campos de porcentaje, agrega `min: 0, max: 100` a las opciones de máscara
    - **IMPORTANTE**: Con `removeMaskOnSubmit: true` y `autoUnmask: true`, cuando accedes al valor del input vía `.value` o FormData, obtienes el formato numérico limpio con punto como separador decimal (ej., "60.58"), listo para procesamiento del backend
    - La máscara solo afecta la VISUALIZACIÓN, el valor real siempre está en formato estándar (punto como separador decimal)
  * no uses {{ rr }} en.
     * Funciones Javascript
     * cualquier elemento de formulario o atributo de elemento de formulario
     * Esto es principalmente para el valor del id del formulario porque es lo que usamos para referenciar algo en el formulario, ejemplo.
        $('#form_test_{{ rr }} input[name=blalba]')
  * Un endpoint para obtener los datos, también para llamar al método en los módulos del backend.
  * La obtención y renderizado de datos de un modelo se hace con table_ui.js.
     * Leer table_ui.md para documentación.
  * Las referencias para tags html select para obtener claves foráneas se hacen con form_ui.js
     * Leer form_ui.md para documentación.
     * Cuando crees el formulario si el modelo tiene foreignkey debes usar se_populate o se_select automáticamente, pero debes preguntar qué método usar antes.
     * Cada select2 debe tener el parámetro dropdownParent: $('#offcanvasGlobalUi') si está dentro del offcanvasGlobalUi, también por defecto el theme: 'bootstrap-5'

     En el atributo dele de se_select o se_populate nunca uses referencias #id

     siempre usa el name del elemento html.

      dele: '#form_anime_{{ rr }} select[name=menu]'

     * Cuando uses se_populate en modo edición, SIEMPRE usa .val() y .trigger('change') de jQuery para establecer el valor:

       ```javascript
       form_search.se_populate({
           // ... parámetros
       }).then(() => {
           {% if mobj and mobj.categoriaobj %}
               $('#form_producto_{{ rr }} select[name=categoriaobj_id]').val('{{ mobj.categoriaobj.id }}').trigger('change');
           {% endif %}
       });
       ```

       ❌ INCORRECTO (usando qelem y .value):
       ```javascript
       qelem('#form_producto_{{ rr }} select[name=categoriaobj_id]').value = '{{ mobj.categoriaobj.id }}';
       ```

       ✅ CORRECTO (usando jQuery .val() y .trigger('change')):
       ```javascript
       $('#form_producto_{{ rr }} select[name=categoriaobj_id]').val('{{ mobj.categoriaobj.id }}').trigger('change');
       ```

       El .trigger('change') es REQUERIDO para inicializar correctamente el componente select2 en modo edición.
   * Si se usa se_select, el parámetro sterm debe contener algo, ya que es el campo(s) donde se buscará lo que el usuario escriba
   * Si usas se_select, no retorna una promesa, así que a diferencia de se_populate, no puedes usar .then
   * Si el formulario abierto es para edición y se usa se_select dentro de él, según el campo requerido, debes crear la opción para el select, ya que no estará disponible para una simple llamada .val() - debe ser creada. Ejemplo:

       {% if mobj %}
         nopt = new Option('{{ mobj.username }}', '{{ mobj.username }}', false, false);
         $('#form_mobileappconfig_{{ rr }} select[name=username]').append(nopt).trigger('change');
       {% endif %}

   * Si se_select o se_populate es una representación de una foreignkey, el name del elemento select debe ser como el _id está en la base de datos.

       class Model:
           app = models.Foreignkey(ModelRelated)

      Entonces el atributo name debe ser name="app_id"

  * Implementar el método de eliminar registros, esto debe ser llamado desde la UI del grid.
    Seleccionando el registro y enviándolo al backend.

    Esta es la huella (ejemplo) para el método del backend.
        def delete_anime(self, *args, **kwargs) -> dict:
            ios = IoS()
            userobj = kwargs.get('userobj')
            q: dict = kwargs.get('qdict', {})
            dbcon = q.get('dbcon', 'default')
            ids = io_json.from_json(q.get('ids'))
            msgs = []
            if not ids:
                  return msgs.append({'error': 'Falta los IDs de los registros a eliminar'})
                  return {'msgs': msgs }
            for pk in ids:
                  mobj = Anime.objects.using(dbcon).get(pk=pk)
                  mobj.delete()
                  msgs.append({'success': 'Registro eliminado exitosamente'})
            return { 'msgs': msgs }

   Esta es la huella (ejemplo) para el método del front-end.
      qelem('#btn_borrar_anime').addEventListener('click', function() {
         let table = $(`#${t_anime}`).DataTable();
         let selectedRows = table.rows({ selected: true });
         if (selectedRows.count() === 0) {
               UiB.MsgError('Por favor, selecciona al menos un registro para borrar.');
               return;
         }
         let idsToDelete = selectedRows.data().toArray().map(row => row.id);
         UiB.MsgSwall({
               msg: `¿Estás seguro de que deseas borrar ${idsToDelete.length} registro(s)? Esta acción no se puede deshacer.`,
               ttype: 'info'
         }).then((result) => {
               let gbe = new FormData();
               gbe.append('module', 'Anime');
               gbe.append('package', 'mng_anime');
               gbe.append('attr', 'MAnime');
               gbe.append('mname', 'delete_anime');
               gbe.append('dbcon', 'default');
               gbe.append('ids', jfy(idsToDelete));
               axios.post('{% url "iom" %}', gbe).then((rsp)=>{
                  msgs = rsp.data.msgs;
                  log.info(`Mensaje recibido del backend: ${jfy(msgs)}`);
                  UiB.BeMsgHandle({
                     rsps: msgs,
                     timer: 2000,
                     offcanvasglobal: true
                  })
                  $(`#${t_anime}`).DataTable().ajax.reload();
               }).catch((err)=>{
                  log.error(`Error al borrar registros: ${jfy(err)}`);
                  UiB.MsgError('Ocurrió un error al borrar los registros. Por favor, intenta de nuevo.');
               });
         });
      });

   * Implementar el método de búsqueda a través de la variable gmquery, esto significa que el parámetro check_gmquery debe ser true, los campos a usar en la búsqueda deben corresponder a los campos del grid. Así que necesitas leer el modelo de la interfaz
      La variable gmquery debe aplicarse en la función del valor builder_be.

      if (gmquery.length > 0) {
         log.info(`Agregando mquery global: ${jfy(gmquery)}`);
         mquery = [...mquery, ...gmquery];
      }

      qelem('#input_buscar_apps').onkeydown = (evt) => {
         if (evt.key === 'Enter') {
               gmquery = [];
               if (qelem('#input_buscar_apps').value.trim() !== '') {
                  gmquery.push({
                     'field': 'or_app_name__icontains', 'value': qelem('input#input_buscar_apps').value
                  })
                  gmquery.push({
                     'field': 'or_friendly_name__icontains', 'value': qelem('input#input_buscar_apps').value
                  })
                  gmquery.push({
                     'field': 'or_url__icontains', 'value': qelem('input#input_buscar_apps').value
                  })
               }
               $(`#${t_apps}`).DataTable().ajax.reload();

         }
      }


## Patrón de Manejo de Respuesta del Backend

**CRÍTICO**: Siempre maneja las respuestas del backend siguiendo este patrón (ver `templates/OptsIO/MenuCreateUi.html`):

```javascript
axios.post('{% url "iom" %}', fdata).then((rsp) => {
    var msgs = rsp.data.msgs;
    log.info('#form_xxx_{{ rr }} Response msgs: ' + jfy(msgs));

    // Si la respuesta no tiene propiedad 'msgs', envolver data en array
    if (!rsp.data.hasOwnProperty('msgs')) {
        msgs = [rsp.data];
    }

    // Verificar errores
    var got_error = false;
    msgs.forEach((ee) => {
        if (ee.error) {
            log.error('#form_xxx_{{ rr }} Hay un error del backend ' + jfy(ee));
            got_error = true;
        }
    });

    // Usar BeMsgHandle para mostrar mensajes y auto-cerrar offcanvas
    log.info('#form_xxx_{{ rr }} Compilando mensajes para mostrar al usuario ' + jfy(msgs));
    UiB.BeMsgHandle({
        rsps: msgs,
        timer: 2000,
        offcanvasglobal: true  // Auto-cierra offcanvas en éxito
    });

    return msgs;
}).then((msgs) => {
    // Después de mostrar mensajes, hacer acciones adicionales si no hay errores
    if (got_error === false) {
        log.success('#form_xxx_{{ rr }} No hay error recargar datatable {{ t_guid }}');
        $('#{{ t_guid }}').DataTable().ajax.reload();
    }
});
```

**IMPORTANTE**: Nota el uso de `{{ t_guid }}` - esto viene del objeto `dattrs` pasado al llamar `OptsIO.getTmpl()`.

### Entendiendo dattrs y Variables de Template Django

Cuando llamas `OptsIO.getTmpl()` desde la UI de lista (ej., `MenuUi.html`), el objeto `dattrs` se convierte en variables de template Django en la UI del formulario (ej., `MenuCreateUi.html`):

**En MenuUi.html:**
```javascript
dattrs = {
    title: 'Crear Menú',
    t_guid: t_menu,           // ← Esta variable de MenuUi.html
    sui_rr: '{{ rr }}',
    from_MenuUi: true,
    offcanvasglobal: true
}

tps = {
    model_app_name: 'OptsIO',
    model_name: 'Menu',
    dbcon: 'default',
    url: '{% url "dtmpl" %}',
    dattrs: dattrs,           // ← Pasado al endpoint dtmpl
    template: 'OptsIO/MenuCreateUi.html',
    raw: true,
}
```

**En MenuCreateUi.html:**
```javascript
// Ahora puedes usar {{ t_guid }} como variable de template Django
if (got_error === false) {
    log.success('#form_menu_{{ rr }} No hay error recargar datatable {{ t_guid }}');
    $('#{{ t_guid }}').DataTable().ajax.reload();  // ← Usa el t_guid de dattrs
}
```

**Patrones INCORRECTOS** (NO USAR):
```javascript
// ❌ INCORRECTO - Manejo manual de mensajes no cierra offcanvas correctamente
if (rsp.data.success) {
    UiB.MsgSuccess(rsp.data.success);
    setTimeout(() => {
        bsOffcanvas.hide();  // Esto no funciona confiablemente
    }, 1500);
}

// ❌ INCORRECTO - Hardcodear ID de tabla en lugar de usar {{ t_guid }}
if (got_error === false) {
    $(`#t_producto`).DataTable().ajax.reload();  // ← ¡Incorrecto! Esta variable no existe en este scope
}

// ✅ CORRECTO - Usar {{ t_guid }} de dattrs
if (got_error === false) {
    $('#{{ t_guid }}').DataTable().ajax.reload();  // ← ¡Correcto! Usa variable de template Django
}
```

## Utilidades adicionales.
   * OptsIO.s4generate() se usa para generar un identificador único, esto viene de a_ui.js


## Flujo de Trabajo

- ** Crear un .html en el directorio templates en la carpeta de la app
- ** Especificar el modelo a recuperar
- ** Especificar los campos a mostrar
- ** Crear el formulario para crear un registro.
- ** El mismo formulario que se usa para creación se usaría para actualizar el registro. El {{ mobj }} en el template controla cuando es para creación o cuando es para actualización.
- ** Después de la creación de ambos archivos (la lista de registros y el formulario de crear/actualizar), crear las entradas en el modelo Apps directamente usando Django shell o comando de management.

### Creando Entradas de Apps

En lugar de solo generar salida de diccionario, CREA DIRECTAMENTE los registros en Apps:

```python
from OptsIO.models import Apps

entry = {
    'prioridad': 100,  # Usa siempre 100
    'menu': 'Maestros',  # Nombre del menú - creará automáticamente el menú si no existe
    'app_name': 'Producto',  # Nombre del modelo
    'friendly_name': 'Productos',  # Nombre corto y amigable
    'icon': 'mdi mdi-package-variant',  # Material Design Icon
    'url': 'Sifen/ProductoUi.html',  # Ruta al template
    'version': 1,  # Siempre usa versión 1
    'background': '#FFFFFF',  # Siempre usa blanco (#FFFFFF)
    'active': True,
}

Apps.objects.create(**entry)
```

Para múltiples interfaces, usa un loop:

```python
entries = [
    {
        'prioridad': 100,
        'menu': 'Maestros',
        'app_name': 'Categoria',
        'friendly_name': 'Categorías',
        'icon': 'mdi mdi-shape',
        'url': 'Sifen/CategoriaUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
    {
        'prioridad': 100,
        'menu': 'Maestros',
        'app_name': 'Marca',
        'friendly_name': 'Marcas',
        'icon': 'mdi mdi-tag',
        'url': 'Sifen/MarcaUi.html',
        'version': 1,
        'background': '#FFFFFF',
        'active': True,
    },
]

for entry in entries:
    Apps.objects.create(**entry)
    print(f'✓ Creado: {entry["friendly_name"]}')
```

**IMPORTANTE**: El campo 'menu' crea automáticamente la estructura del menú en el sidebar. Ver `.claude/menu.md` para detalles.
## Notas.
  * En la definición de columnas para usar el método render es así:
      render: (data, type, rowobj) => {
            return ..lógica o html con css ...etc
      }

  * El método del backend para creación o actualización de los registros siempre se maneja por.

    fdata.append('module', 'OptsIO');
    fdata.append('package', 'io_maction');
    fdata.append('attr', 'IOMaction');
    fdata.append('mname', 'process_record');

   Esta es una implementación genérica, por eso existen los parámetros.
        fdata.append('model_app_name', 'Anime');
        fdata.append('model_name', 'Anime');


## Estructura de archivos

```
templates/{app_name}/
├── {Modelo}Ui.html          # Para mostrar los registros con datatables
└── {Modelo}CreateUi.html    # El formulario de crear/actualizar

{app_name}/
└── {module}.py           # Métodos que el .html estaría usando
```

Te proporcionaré los nombres de los módulos

## Ejemplo funcional

### En BASE_DIR/templates/OptsIO/ hay un ejemplo funcional.
    * templates/OptsIO/MenuUi.html
    * templates/OptsIO/MenuCreateUi.html
   # Ejemplos que tienen relaciones Header y Detail.
    * templates/Sifen/DocumentNcUi.html
    * templates/Sifen/DocumentHeaderUi.html
    * templates/Sifen/DocumentCreateNcUi.html
    * templates/Sifen/DocumentCreateUi.html


### El método de creación para el backend

**CRÍTICO**: Cada modelo DEBE tener un método `create_{model_name_en_minusculas}` que se llama desde el parámetro `c_a` en el formulario CreateUi.

**Referencia**: Ver método `create_menu` en `OptsIO/io_apps.py` para el patrón exacto.

```python
from django.forms import model_to_dict
from OptsIO.io_serial import IoS
from OptsIO.io_json import from_json

def create_{model_name_en_minusculas}(self, *args, **kwargs) -> tuple:
    """
    Crea o actualiza un registro de {ModelName}
    """
    ios = IoS()
    userobj = kwargs.get('userobj')
    q: dict = kwargs.get('qdict', {})
    dbcon = q.get('dbcon', 'default')
    uc_fields: dict = from_json(q.get('uc_fields', {}))
    rnorm, rrm, rbol = ios.format_data_for_db({ModelName}, uc_fields)
    for c in rrm: uc_fields.pop(c)
    for f, fv in rbol: uc_fields[f] = fv
    for f, fv in rnorm: uc_fields[f] = fv
    ff = ios.form_model_fields(uc_fields, {ModelName}._meta.fields)
    for rr in ff:
        uc_fields.pop(rr)
    pk = uc_fields.get('id')
    msg = 'Registro creado exitosamente'
    files: dict = kwargs.get('files')
    if pk:
        mobj = {ModelName}.objects.get(pk=pk)
        msg = 'Registro actualizado exitosamente'
        u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
        if not u_fields and not files:
            return {'info': f'Nada que actualizar'}, args, kwargs
        if not u_fields and files:
            msg = 'Archivos actualizados exitosamente'
        if u_fields:
            {ModelName}.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
        if u_fields and files:
            msg = 'Registro y archivos actualizados exitosamente'
    else:
        mobj = {ModelName}.objects.using(dbcon).create(**uc_fields)
    return {'success': msg,
            'record_id': mobj.id
        }, args, kwargs
```

**Este método debe llamarse desde el template CreateUi vía el parámetro `c_a`**:

```javascript
fdata.append('c_a', jfy([
    {
        'module': 'Sifen',              // Nombre de la app
        'package': 'mng_producto',       // Nombre del archivo del módulo Python
        'attr': 'MProducto',             // Nombre de la clase
        'mname': 'create_categoria',     // Nombre del método
        'cont': false,
        'show_success': true
    },
]))
```

**INCORRECTO**:
```javascript
// ❌ INCORRECTO - Array c_a vacío
fdata.append('c_a', jfy([]))
```

**Explicación de Parámetros**:
- `b_vals`: Array de métodos a ejecutar ANTES de `c_a` (usualmente vacío `[]`)
- `c_a`: Array con el método de creación a llamar (REQUERIDO - ver ejemplo arriba)
- `a_vals`: Array de métodos a ejecutar DESPUÉS de `c_a` (usualmente vacío `[]`)

### Manejando Subidas de Archivos (Imágenes, Documentos, etc.)

**CRÍTICO**: Cuando trabajas con modelos que tienen `ImageField` o `FileField`, debes manejar archivos separadamente de los datos regulares del formulario.

#### Patrón del Backend para Subida de Archivos

En tu método `create_{model_name}`, agrega manejo de archivos después de la creación/actualización del registro principal:

```python
from django.core.files import File

def create_{model_name}(self, *args, **kwargs) -> tuple:
    """
    Crea o actualiza un registro de {ModelName} con soporte para archivos
    """
    ios = IoS()
    userobj = kwargs.get('userobj')
    q: dict = kwargs.get('qdict', {})
    dbcon = q.get('dbcon', 'default')
    uc_fields: dict = from_json(q.get('uc_fields', {}))
    files: dict = kwargs.get('files')  # ← Obtener archivos de kwargs

    # ... [código estándar de procesamiento de campos] ...

    pk = uc_fields.get('id')
    msg = 'Registro creado exitosamente'

    if pk:
        mobj = {ModelName}.objects.get(pk=pk)
        msg = 'Registro actualizado exitosamente'
        u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
        if not u_fields and not files:
            return {'info': f'Nada que actualizar'}, args, kwargs
        if not u_fields and files:
            msg = 'Archivos actualizados exitosamente'
        if u_fields:
            {ModelName}.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)
        if u_fields and files:
            msg = 'Registro y archivos actualizados exitosamente'
    else:
        mobj = {ModelName}.objects.using(dbcon).create(**uc_fields)

    # Manejar subidas de archivos
    if files:
        for name, fobj in files.items():
            fname = f'user_{userobj.username}_{fobj.name}'
            dfobj = File(fobj, name=fname)
            setattr(mobj, name, dfobj)
        mobj.save()

    return {'success': msg, 'record_id': mobj.id}, args, kwargs
```

**Puntos Clave**:
- Los archivos vienen de `kwargs.get('files')` separadamente de los datos regulares del formulario
- Verificar `if files:` para manejar subidas de archivos
- Usar `File(fobj, name=fname)` para envolver el archivo subido
- Usar `setattr(mobj, name, dfobj)` para asignar el archivo al campo del modelo
- Llamar `mobj.save()` después de establecer archivos
- Prefijar nombres de archivo con username para trazabilidad

#### Patrón del Frontend para Subida de Archivos

En tu template CreateUi, maneja inputs de archivo separadamente de los datos regulares del formulario:

```javascript
save_{model_name} = (target) => {
    log.info(`#form_{model_name}_{{ rr }} Preparando datos para enviar al backend`);
    let formData = new FormData(target);

    // Extraer datos del formulario para edata (excluyendo archivos)
    let edata = form_serials.form_to_json(formData);

    // Crear FormData para backend
    var fdata = new FormData();
    fdata.append('module', 'OptsIO');
    fdata.append('package', 'io_maction');
    fdata.append('attr', 'IOMaction');
    fdata.append('mname', 'process_record');
    fdata.append('model_app_name', '{NombreApp}');
    fdata.append('model_name', '{NombreModelo}');
    fdata.append('dbcon', 'default');

    // ... [manejar selects y otros campos especiales] ...

    fdata.append('uc_fields', jfy(edata));
    fdata.append('b_vals', jfy([]));
    fdata.append('c_a', jfy([{
        'module': '{NombreApp}',
        'package': '{nombre_modulo}',
        'attr': '{NombreClase}',
        'mname': 'create_{model_name}',
        'cont': false,
        'show_success': true
    }]));
    fdata.append('a_vals', jfy([]));

    // Manejar inputs de archivo usando helper form_serials
    const efiles = form_serials.form_files(formData);
    efiles.forEach((idx) => {
        ff = formData.get(idx);
        fdata.append(idx, ff, ff.name)
    });

    // ... [resto del axios post] ...
}
```

**Puntos Clave**:
- Usar `form_serials.form_to_json(formData)` para extraer datos regulares del formulario
- Usar `form_serials.form_files(formData)` para obtener nombres de campos de archivo
- Adjuntar cada archivo a `fdata` con su nombre de archivo original
- Los archivos se envían separadamente de `uc_fields`

#### Template HTML para Input de Archivo

```html
<div class="row">
    <div class="col-md-12">
        <label>Foto del Producto</label>
        <div class="mb-3">
            {% if mobj and mobj.photo %}
                <div class="mb-2">
                    <img src="{{ mobj.photo.url }}" alt="{{ mobj.descripcion }}"
                         id="preview_photo_{{ rr }}"
                         style="max-width: 200px; max-height: 200px; object-fit: cover; border-radius: 8px;">
                </div>
            {% else %}
                <div class="mb-2" id="preview_container_{{ rr }}" style="display: none;">
                    <img src="" alt="Preview" id="preview_photo_{{ rr }}"
                         style="max-width: 200px; max-height: 200px; object-fit: cover; border-radius: 8px;">
                </div>
            {% endif %}
            <input type="file" name="photo" class="form-control"
                   accept="image/*" id="input_photo_{{ rr }}">
            <small class="text-muted">Formatos permitidos: JPG, PNG, GIF. Tamaño máximo: 5MB</small>
        </div>
    </div>
</div>
```

#### JavaScript para Preview de Imagen

```javascript
// Preview de foto
qelem('#input_photo_{{ rr }}').addEventListener('change', function(e) {
    var file = e.target.files[0];
    if (file) {
        var reader = new FileReader();
        reader.onload = function(e) {
            var preview = qelem('#preview_photo_{{ rr }}');
            preview.src = e.target.result;
            {% if not mobj or not mobj.photo %}
                qelem('#preview_container_{{ rr }}').style.display = 'block';
            {% endif %}
        };
        reader.readAsDataURL(file);
    }
});
```

**Ejemplo de Referencia Completo**: Ver `templates/Sifen/ProductoCreateUi.html` para implementación completa.


### DIRECTRICES DE DESARROLLO.

   No uses try {} except {} en los métodos python

### Renderizar registro único.

   Si un registro tiene que ser llamado desde un template, usa dtmpl para renderizar el template con la instancia del modelo en él {{ mobj }}

        dattrs = {
            title: `Lote ${lote}`,
            t_guid: t_documentheader, //referencia del grid
            sui_rr: '{{ rr }}',
            from_[nombre_del_template_desde_donde_llama]: true,
            offcanvasglobal: true
        }

        tps = {
            model_app_name: 'Sifen',
            model_name: 'TrackLote',
            dbcon: 'default',
            url: '{% url "dtmpl" %}',
            dattrs: dattrs,
            template: 'Sifen/TrackLoteRecordUi.html',
            raw: true,

        }
	tps['pk'] = pk;
	dattrs['title'] = 'Visualizar Trazabilidad del Lote';
        OptsIO.getTmpl(tps).then((rsp)=>{
            let data = rsp.data;
            $('#offcanvasGlobalUiBody').html(data);
            let bsOffcanvas = new bootstrap.Offcanvas('#offcanvasGlobalUi')
            bsOffcanvas.show();
            let tmpOffcanvas = document.getElementById('offcanvasGlobalUi')
            tmpOffcanvas.addEventListener('hidden.bs.offcanvas', event => {
                $('#offcanvasGlobalUiBody').html('');
            })
            UiB.kILLLoaderAjax();
        })

**Última actualización**: 2025-11-16
**Mantenido por**: AltaMachines Tech
