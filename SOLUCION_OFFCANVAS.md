# SOLUCIÓN: Offcanvas Global para DocumentHeaderHomeUi

## Problema Identificado

El botón "Facturar" en `DocumentHeaderHomeUi.html` intentaba abrir un offcanvas que **NO EXISTÍA** en el DOM.

### Código del botón:
```javascript
qelem(`#btn-proforma-{{rr}}-create`).addEventListener('click', (evt)=>{
    OptsIO.getTmpl({...}).then((rsp)=>{
        let data = rsp.data;
        $('#offcanvasGlobalUiBody').html(data);  // ❌ Elemento no existía
        let bsOffcanvas = new bootstrap.Offcanvas('#offcanvasGlobalUi')  // ❌ Elemento no existía
        bsOffcanvas.show();
    })
})
```

### Elementos que se buscaban:
- `#offcanvasGlobalUi` - **NO EXISTÍA**
- `#offcanvasGlobalUiBody` - **NO EXISTÍA**

---

## Solución Aplicada

### 1. Agregado Offcanvas Global en `templates/AMOffcanvasUi.html`

```html
<!-- Offcanvas Global (100% de pantalla) -->
<div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvasGlobalUi"
     aria-labelledby="offcanvasGlobalUiLabel" data-bs-backdrop="true"
     data-bs-keyboard="true" style="width: 100% !important;">
    <div class="offcanvas-header border-bottom bg-primary text-white">
        <h5 class="offcanvas-title" id="offcanvasGlobalUiLabel">
            <i class="mdi mdi-file-document-outline me-2"></i>
            Documento
        </h5>
        <button type="button" class="btn-close btn-close-white"
                data-bs-dismiss="offcanvas" aria-label="Close"></button>
    </div>
    <div class="offcanvas-body p-0" id="offcanvasGlobalUiBody">
        <!-- El contenido se cargará aquí dinámicamente -->
    </div>
</div>
```

### 2. CSS para offcanvas al 100%

```css
/* Estilos para el offcanvas global (100% pantalla) */
#offcanvasGlobalUi {
    width: 100% !important;
    max-width: 100% !important;
}

#offcanvasGlobalUi .offcanvas-body {
    overflow-y: auto;
    background: #f5f7fa;
    padding: 0 !important;
}

#offcanvasGlobalUi .offcanvas-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem 1.5rem;
}
```

---

## Características del Offcanvas Global

### ✅ **Configuración:**
- **Ancho:** 100% de la pantalla
- **Posición:** Desde la derecha (`offcanvas-end`)
- **Backdrop:** Habilitado (oscurece el fondo)
- **Teclado:** ESC para cerrar
- **Header:** Fondo degradado azul/morado
- **Body:** Sin padding, fondo gris claro

### ✅ **Funcionalidad:**
1. Se abre desde la derecha
2. Ocupa 100% del ancho de la pantalla
3. El contenido se carga dinámicamente mediante `OptsIO.getTmpl()`
4. Se limpia automáticamente al cerrar
5. Tiene botón de cierre

---

## Cómo Funciona el Flujo

### 1. Usuario hace click en botón "Facturar"
```html
<button id="btn-proforma-{{rr}}-create" class="btn btn-lg btn-info">Factura</button>
```

### 2. JavaScript captura el evento
```javascript
qelem(`#btn-proforma-{{rr}}-create`).addEventListener('click', (evt)=>{
    dattrs = {
        t_guid: t_ofh,
        sui_rr: '{{ rr }}',
        from_consultar_documentheader: true,
        tipo: 'FE',
        offcanvasglobal: true
    }
```

### 3. Se solicita el template al servidor
```javascript
OptsIO.getTmpl({
    model_app_name: 'Sifen',
    model_name: 'DocumentHeader',
    dbcon: 'default',
    url: '{% url "dtmpl" %}',
    dattrs: dattrs,
    template: 'Sifen/DocumentHeaderCreateUi.html',
    raw: true,
})
```

### 4. El servidor responde con HTML renderizado
- Vista: `OptsIO/views.py:dtmpl()`
- Template: `Sifen/DocumentHeaderCreateUi.html`
- Contexto: incluye `rr`, `mobj`, etc.

### 5. JavaScript inserta el HTML y muestra el offcanvas
```javascript
.then((rsp)=>{
    let data = rsp.data;
    $('#offcanvasGlobalUiBody').html(data);  // ✅ Ahora existe
    let bsOffcanvas = new bootstrap.Offcanvas('#offcanvasGlobalUi')  // ✅ Ahora existe
    bsOffcanvas.show();  // ✅ Se muestra
})
```

### 6. Al cerrar, se limpia el contenido
```javascript
let tmpOffcanvas = document.getElementById('offcanvasGlobalUi')
tmpOffcanvas.addEventListener('hidden.bs.offcanvas', event => {
    $('#offcanvasGlobalUiBody').html('');  // Limpia el contenido
})
```

---

## Verificación en el Navegador

### 1. Abrir la aplicación
```
http://localhost:8002/
```

### 2. Abrir DevTools (F12)
```
Console > Ejecutar:
document.getElementById('offcanvasGlobalUi')
```
**Resultado esperado:** Debe devolver el elemento, no `null`

### 3. Verificar que el botón existe
```javascript
// En la consola del navegador
document.querySelectorAll('[id*="btn-proforma"]')
```
**Resultado esperado:** Debe mostrar el botón con ID único

### 4. Verificar evento click
```javascript
// Obtener el botón y verificar listeners
getEventListeners(document.querySelector('[id*="btn-proforma"]'))
```

---

## Posibles Problemas Adicionales

### A. El botón no aparece

**Causa:** Permisos no habilitados
```html
{% if perms.OptsIO.table_documentheader_eje_factura  %}
    <button id="btn-proforma-{{rr}}-create">Factura</button>
{% endif %}
```

**Solución:** Verificar que el usuario tenga el permiso `OptsIO.table_documentheader_eje_factura`

**Verificar en Django Admin:**
```python
# En Django shell
python manage.py shell

from django.contrib.auth.models import User, Permission
user = User.objects.get(username='tu_usuario')
perms = user.get_all_permissions()
print([p for p in perms if 'documentheader' in p])
```

### B. El evento no se registra

**Causa:** JavaScript se ejecuta antes de que el botón se renderice

**Solución:** El código ya usa `qelem()` que es `querySelector`, pero se ejecuta cuando el template se carga. Si el botón se carga dinámicamente DESPUÉS, el evento no se registrará.

**Verificar:**
```javascript
// Debe ejecutarse DESPUÉS de que el botón esté en el DOM
qelem(`#btn-proforma-{{rr}}-create`)  // No debe ser null
```

### C. OptsIO.getTmpl falla

**Causa:** Error en la petición AJAX

**Verificar en Network tab:**
- URL: `/io/dtmpl/`
- Método: GET
- Parámetros: `tmpl=Sifen/DocumentHeaderCreateUi.html`
- Status: 200 OK

**Si da 403 CSRF:**
- Verificar que `OptsIO.getCookie('csrftoken')` funcione
- Verificar headers de axios

---

## Archivos Modificados

### 1. `templates/AMOffcanvasUi.html`
- ✅ Agregado `#offcanvasGlobalUi`
- ✅ Agregado CSS para offcanvas al 100%
- ✅ Mantiene `#appOffcanvas` existente

### 2. No se requieren más cambios
El código en `DocumentHeaderHomeUi.html` ya estaba correcto, solo faltaba el elemento del offcanvas.

---

## Testing Checklist

- [ ] Verificar que el servidor esté corriendo (puerto 8002)
- [ ] Abrir aplicación en navegador
- [ ] Abrir DevTools (F12)
- [ ] Verificar que `offcanvasGlobalUi` existe en el DOM
- [ ] Navegar a DocumentHeaderHomeUi
- [ ] Verificar que el botón "Factura" aparece
- [ ] Click en botón "Factura"
- [ ] Verificar que el offcanvas se abre al 100%
- [ ] Verificar que el contenido se carga
- [ ] Cerrar offcanvas
- [ ] Verificar que el contenido se limpia

---

## Próximos Pasos

1. **Reiniciar navegador** para cargar cambios en templates
2. **Limpiar caché** (Ctrl+Shift+Delete)
3. **Probar funcionalidad** siguiendo el checklist
4. **Revisar permisos** si el botón no aparece
5. **Revisar consola** para errores JavaScript

---

## Notas Adicionales

### Variable `{{rr}}`
- Se genera en la vista `dtmpl()` (OptsIO/views.py:33)
- Es un UUID de 5 caracteres: `rr = str(uuid.uuid4()).replace('-', '')[0:5]`
- Se usa para IDs únicos en elementos dinámicos
- Ejemplo: `btn-proforma-a1b2c-create`

### Otros botones que usan el mismo offcanvas
En el mismo template se usan:
- `#btn-nc-{{rr}}-create` - Nota Crédito
- `#btn-af-{{rr}}-create` - Auto Factura
- `#btn-proforma-{{rr}}-recibo` - Recibo

Todos usan `#offcanvasGlobalUi` de la misma manera.

---

**Solución implementada por:** Claude (Anthropic)
**Fecha:** 14 de Noviembre, 2025
**Archivo principal modificado:** `templates/AMOffcanvasUi.html`
