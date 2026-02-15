# Referencia de Métodos JavaScript

## Métodos del Objeto OptsIO (static/amui/a_ui.js)

Estos son los **ÚNICOS** métodos disponibles en el objeto `OptsIO`. **NUNCA** inventes métodos que no existen aquí.

### Métodos Disponibles:

```javascript
OptsIO.getToken()              // Obtener token del localStorage
OptsIO.setToken(token)         // Establecer token en localStorage
OptsIO.getCookie(name)         // Obtener valor de cookie por nombre
OptsIO.getTmpl({...})          // Cargar template desde backend vía endpoint dtmpl
OptsIO.setInnerHTML(elm, html) // Establecer innerHTML y ejecutar scripts
OptsIO.s4generate()            // Generar string hexadecimal aleatorio de 4 caracteres
OptsIO.getuuid()               // Generar UUID usando s4generate()
OptsIO.gen_tracking_string()   // Generar string de tracking con timestamp
OptsIO.drawModal({...})        // Crear y mostrar modal de Bootstrap
```

### Uso de OptsIO.getTmpl()

**IMPORTANTE**: Este método llama al endpoint `dtmpl` y **genera automáticamente la variable `rr`** para el template cargado.

```javascript
// Uso correcto desde templates existentes
var dattrs = {
    title: 'Título Aquí',
    sui_rr: OptsIO.s4generate(),  // Solo cuando se llama desde un template que tiene {{ rr }}
    offcanvasglobal: true
};

var tps = {
    model_app_name: 'NombreApp',
    model_name: 'NombreModelo',
    dbcon: 'default',
    url: '{% url "dtmpl" %}',
    dattrs: dattrs,
    template: 'NombreApp/TemplateUi.html',
    raw: true
};

OptsIO.getTmpl(tps).then((rsp) => {
    var data = rsp.data;
    $('#offcanvasGlobalUiBody').html(data);
    var bsOffcanvas = new bootstrap.Offcanvas('#offcanvasGlobalUi');
    bsOffcanvas.show();
});
```

**Cuándo usar `sui_rr` en `dattrs`**:
- ✅ Cuando se llama desde un template que **ya tiene** `{{ rr }}` disponible
- ❌ Cuando se llama desde BaseUi.html o cualquier template sin `{{ rr }}` existente
- ❌ **NUNCA** uses `OptsIO.generateRandomString()` - **NO EXISTE**

**Parámetros para OptsIO.getTmpl()**:
```javascript
{
    url: '{% url "dtmpl" %}',          // Requerido: URL del endpoint
    template: 'path/to/Template.html',  // Requerido: ruta del template
    dattrs: {...},                      // Opcional: atributos de datos para el template
    model_app_name: 'NombreApp',        // Opcional: nombre de app Django
    model_name: 'NombreModelo',         // Opcional: nombre del modelo
    pk: 123,                            // Opcional: clave primaria para registro
    dbcon: 'default',                   // Opcional: conexión de base de datos
    raw: true,                          // Opcional: retornar respuesta raw
    container: '#selector',             // Opcional: contenedor para inyectar HTML
    surround: 'BaseUi.html',           // Opcional: template para envolver contenido
    responseType: 'text'                // Opcional: tipo de respuesta
}
```

## Métodos del Objeto Grid (static/amui/table_ui.js)

```javascript
Grid.datatables_wrapper({...})  // Crear DataTable con integración de backend
Grid.datatables_cfilter(data, settings)  // Filtro personalizado para DataTables
```

## Métodos del Objeto UiB (static/amui/a_ui.js)

```javascript
UiB.MsgSuccess(msg)           // Mostrar mensaje de éxito
UiB.MsgError(msg)             // Mostrar mensaje de error
UiB.MsgInfo(msg)              // Mostrar mensaje informativo
UiB.MsgSwall({...})           // Mostrar confirmación SweetAlert2
UiB.BeMsgHandle({...})        // Manejar mensajes del backend
UiB.StartLoaderAjax()         // Iniciar loader de página
UiB.kILLLoaderAjax()          // Terminar loader de página
UiB.BlockLoaderSpecifyAjax({...})  // Bloquear elemento específico con loader
UiB.StartLoaderSpecifyAjax({...})  // Iniciar loader en elemento específico
```

## Métodos del Objeto Form (static/amui/form_ui.js)

```javascript
Form.form_serials(formId)      // Serializar formulario a objeto
Form.se_populate({...})        // Poblar select con datos del backend
Form.se_select({...})          // Select2 con búsqueda en backend
Form.se_select_plus({...})     // Select2 plus con botón de agregar
Form.data_2_form({...})        // Llenar formulario con objeto de datos
Form.sig2file(base64)          // Convertir firma a archivo
Form.form_empty_localStorage(formId)  // Limpiar localStorage para formulario
```

## Funciones Helper Globales

```javascript
jfy(obj)                       // Wrapper de JSON.stringify
qelem(selector)                // Wrapper de document.querySelector
log.info(msg)                  // Log info en consola
log.error(msg)                 // Log error en consola
log.warn(msg)                  // Log warning en consola
```

## Patrones Comunes

### Generar ID Único de Tabla
```javascript
t_tablename = `dtable_${OptsIO.s4generate()}`;
```

### Generar UUID
```javascript
uuid = OptsIO.getuuid();
```

### Obtener Token CSRF
```javascript
csrfToken = OptsIO.getCookie('csrftoken');
```

## REGLAS CRÍTICAS

1. **NUNCA** inventes métodos que no existen en esta lista
2. **SIEMPRE** verifica que un método existe antes de usarlo
3. **NUNCA** asumas que `OptsIO.generateRandomString()` existe - usa `OptsIO.s4generate()` en su lugar
4. Cuando cargas templates con `OptsIO.getTmpl()`, el backend **genera automáticamente `rr`**
5. Solo pasa `sui_rr` en `dattrs` cuando llamas desde un template que ya tiene `{{ rr }}`

## Antes de Usar CUALQUIER Método JavaScript

1. Revisa este archivo primero
2. Si no está aquí, usa `Grep` para buscarlo en el código
3. Si aún no lo encuentras, **PREGUNTA AL USUARIO** - no asumas que existe
