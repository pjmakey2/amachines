# Llamadas Backend desde Axios

Documentación de los endpoints genéricos para invocar lógica Python desde el frontend.

---

## Endpoints disponibles

| URL | Nombre | Método | Auth | Uso |
|-----|--------|--------|------|-----|
| `/io/iom/` | `iom` | POST | Sesión Django (login_required) | Ejecuta cualquier método Python desde el frontend web |
| `/io/dtmpl/` | `dtmpl` | GET | Sesión Django | Renderiza un template HTML con contexto |
| `/io/api_iom/` | `api_iom` | POST | JWT Bearer | Versión API REST de `iom` (mobile / sistemas externos) |
| `/io/api_dtmpl/` | `api_dtmpl` | GET | JWT Bearer | Versión API REST de `dtmpl` |
| `/io/api_isauth/` | `api_isauth` | POST | JWT Bearer | Verifica si el token es válido |
| `/io/api_refresh/` | `api_refresh` | POST | — | Renueva el access token con un refresh token |

---

## 1. `iom` — Ejecutar método Python

Es el endpoint estrella. Permite ejecutar cualquier método de cualquier clase Python del proyecto.

### Parámetros (FormData, POST)

| Campo | Descripción |
|-------|-------------|
| `module` | App Django (ej. `Sifen`, `OptsIO`, `am_shopify`) |
| `package` | Archivo .py dentro del app (ej. `mng_sifen`) |
| `attr` | Clase a instanciar (ej. `MSifen`) |
| `mname` | Método de la clase a ejecutar (ej. `cancelar_doc`) |
| `dbcon` | Conexión Django DB (`default`) |
| `...resto...` | Argumentos del método, accesibles vía `qdict` |

### Cómo llega al método

El backend ejecuta:
```python
cls = MSifen()
return cls.cancelar_doc(userobj=request.user, rq=request, files=request.FILES, qdict=request.POST)
```

Tu método debe leer parámetros desde `kwargs.get('qdict', {})`:
```python
def cancelar_doc(self, *args, **kwargs) -> dict:
    q = kwargs.get('qdict', {})
    doc_id = q.get('doc_id')
    motivo = q.get('motivo', '').strip()
    ...
    return {'success': '...'}  # o {'error': '...'}
```

### Ejemplo desde JS

```javascript
let fdata = new FormData();
fdata.append('module', 'Sifen');
fdata.append('package', 'mng_sifen');
fdata.append('attr', 'MSifen');
fdata.append('mname', 'cancelar_doc');
fdata.append('doc_id', rowobj.id);
fdata.append('motivo', 'Error en la emisión');
fdata.append('dbcon', 'default');

axios.post('{% url "iom" %}', fdata, {
    headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')}
}).then((rsp) => {
    let d = Array.isArray(rsp.data) ? rsp.data[0] : rsp.data;
    if (d.success) {
        UiB.MsgSuccess(d.success);
    } else {
        UiB.MsgError(d.error || 'Error desconocido');
    }
});
```

### Patrón de respuesta

El método debe retornar `dict` o `tuple(dict, args, kwargs)`. Convención:
- Éxito: `{'success': 'mensaje'}` o cualquier dict con datos
- Error: `{'error': 'mensaje'}`

En el frontend usar `Array.isArray(rsp.data) ? rsp.data[0] : rsp.data` para normalizar (cuando el método retorna tuple, llega como array).

---

## 2. `dtmpl` — Renderizar template

Devuelve HTML renderizado de un template con contexto opcional. Usado para abrir formularios/modals dinámicamente.

### Parámetros (querystring, GET)

| Campo | Descripción |
|-------|-------------|
| `tmpl` | Path al template (ej. `Sifen/DocumentHeaderCreateUi.html`) |
| `dattrs` | JSON con atributos a pasar al template como contexto |
| `model_app_name` + `model_name` + `pk` | Si se pasan, carga el objeto y lo inyecta en el contexto como `mobj` |
| `dbcon` | Conexión DB (default `default`) |
| `surround` | Template padre con `{% extends %}` |
| `specific_qdict` | JSON con `{module, package, attr, mname}` para ejecutar Python y mergear su retorno al contexto |

### Wrapper JS estándar — `OptsIO.getTmpl`

```javascript
OptsIO.getTmpl({
    url: '{% url "dtmpl" %}',
    template: 'Sifen/DocumentHeaderCreateUi.html',
    model_app_name: 'Sifen',
    model_name: 'DocumentHeader',
    dbcon: 'default',
    pk: 123,                         // opcional: edita en vez de crear
    dattrs: {
        title: 'Editar Documento',
        t_guid: t_documentheader,
        sui_rr: '{{ rr }}',
        offcanvasglobal: true
    },
    raw: true                        // retorna axios promise sin pintar automáticamente
}).then((rsp) => {
    $('#offcanvasGlobalUiBody').html(rsp.data);
    new bootstrap.Offcanvas('#offcanvasGlobalUi').show();
});
```

Si `raw: false` (default), `getTmpl` inserta el HTML directamente en `container` (selector CSS) ejecutando los `<script>` inline.

### Lectura del contexto en el template

```django
{% if mobj %}
    <input name="id" value="{{ mobj.pk }}">
    <input name="pdv_ruc" value="{{ mobj.pdv_ruc }}">
{% endif %}

<div id="form_{{ rr }}">...</div>
```

`rr` es un id aleatorio único por render (5 chars hex), útil para evitar colisiones de IDs cuando se abren múltiples instancias.

---

## 3. APIs externas (mobile / sistemas externos)

`api_iom` y `api_dtmpl` son idénticos a sus contrapartes pero usan **JWT Bearer Auth** en vez de sesión Django.

### Login para obtener tokens

```javascript
// Primero obtener tokens (endpoint propio, no documentado aquí)
// Luego usar:

axios.post('/io/api_iom/', fdata, {
    headers: {
        'Authorization': refreshToken    // SimpleJWT RefreshToken
    }
});
```

### Renovar access token

```javascript
axios.post('/io/api_refresh/', { refresh: refreshToken });
// → { access: '...' }
```

### Verificar autenticación

```javascript
axios.post('/io/api_isauth/', null, {
    headers: { 'Authorization': refreshToken }
});
// → { is_authenticated: true, accessToken: '...', refreshToken: '...' }
```

---

## Convenciones del proyecto

- **CSRF token**: `iom` y `dtmpl` requieren `X-CSRFToken` desde sesión Django. Usar `OptsIO.getCookie('csrftoken')`.
- **Overlay loading**: agregar/quitar clases `overlay-container overlay` al contenedor durante la petición:
  ```javascript
  let tt = qelem('#mi_tabla');
  tt.classList.add('overlay-container', 'overlay');
  axios.post(...).finally(() => {
      tt.classList.remove('overlay-container', 'overlay');
  });
  ```
- **Mensajes**: `UiB.MsgSuccess(msg)`, `UiB.MsgError(msg)`, `UiB.MsgInfo(msg)`, `UiB.MsgSwall({msg, ttype})` para confirmaciones.
- **Recargar DataTable**: `$(`#${t_documentheader}`).DataTable().ajax.reload(null, false);`
- **Logging**: `log.info(msg)`, `log.error(msg)` — usa el wrapper interno.
