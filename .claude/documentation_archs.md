# Arquitectura de Amachine — índice de documentación

Leer estos documentos (todos en `.claude/`) antes de codificar. Cada uno describe una pieza real del proyecto.

## Documentos

| Documento | Cuándo leerlo |
|-----------|---------------|
| `context.md` | Siempre primero: endpoints, directrices generales, nombres de archivos, verificación antes de codificar |
| `CrearInterfaz.md` | Crear una pantalla: listado (`{Modelo}Ui.html`) + formulario (`{Modelo}CreateUi.html`) |
| `crud_patterm.md` | CRUD genérico con `process_record`, `c_a`, manejo de respuesta, Inputmask, subida de archivos |
| `axios_backend_calls.md` | Llamadas a `iom` (métodos Python) y `dtmpl` (templates); APIs por token |
| `record_from_backend.md` | Traer registros en JSON con `IoS.seModel` (fields, methods, mquery) |
| `table_ui.md` | Parámetros de `Grid.datatables_wrapper` (DataTables) |
| `form_ui.md` | `form_serials`, `form_search.se_populate/se_select`, validaciones de formulario |
| `javascript_methods.md` | Métodos JS que existen (`OptsIO`, `Grid`, `UiB`, `Form`). No inventar métodos |
| `menu.md` / `DisponibilizarApps.md` | Registrar apps en el menú / launcher y asignarlas a roles |
| `models_reference.md` | `UserProfile`, `UserBusiness`, `Business` y cómo obtener el negocio activo |
| `plugin_system.md` | Core vs plugins, `plugin.py`, bus de eventos, workflow de operaciones |
| `setup_system.md` | Setup autoconfigurable de una instalación nueva |

## Stack y piezas base

- **Backend**: Django + Channels + Celery + PostgreSQL + Redis. Sin endpoints por pantalla: todo pasa por `iom` (ejecuta `module.package.attr.mname`) y `dtmpl` (renderiza un template, con `mobj` si se pasa `pk`).
- **Frontend**: templates parciales cargados por ajax dentro de `BaseUi.html`; Bootstrap 5, axios (nunca fetch), DataTables vía `Grid.datatables_wrapper`, select2 vía `form_search`, SweetAlert2 vía `UiB`, Inputmask, moment. Formularios en el offcanvas global `#offcanvasGlobalUi`.
- **Lógica**: módulos `mng_*.py` con una clase `M*`; los métodos reciben `userobj`, `rq`, `files`, `qdict` y devuelven `dict` (`success` / `error` / `info`), o `(dict, args, kwargs)` si son parte de una cadena `c_a`.

## Core y plugins

- `INSTALLED_APPS` = Django + core (`OptsIO`, `Sifen`, `Finance`) + `AMACHINE_PLUGINS` del `.env` de cada instalación. `Amachine/plugin_loader.py` agrega solo las dependencias declaradas en cada `plugin.py` (pedir `Ecommerce` instala `Almacen`).
- Un plugin con páginas públicas expone `urls.py` con `URL_PREFIX`; `Amachine/urls.py` lo monta solo (ej: `Ecommerce` → `/tienda/<slug>/`).
- Un plugin es una app Django con `plugin.py` (`BasePlugin`): menús, datos de referencia, handlers de eventos. Sus templates viven en `<App>/templates/<App>/`.
- **El core nunca importa un plugin.** Un plugin puede depender de otro (declararlo en `dependencies`). Si el core necesita un modelo opcional: `apps.is_installed()` + `apps.get_model()`.
- Dependencias: `Tesoreria` ← `Egreso`, `Deposito`; `Almacen` ← `Ecommerce`; `Contabilidad` y `Deposito` escuchan eventos de los demás y nadie depende de ellos.

## Multi-tenant

- Modelos nuevos: FK `businessobj` a `Sifen.Business`. Con eso el core los aísla solo por negocio activo: lecturas (`seModel`, grids, selects), escrituras (`IOMaction.uc_record` fija el negocio en el servidor) y edición (`dtmpl` responde 403 ante un registro ajeno).
- Modelos históricos usan `bs_ruc` (sin aislamiento automático).
- En Python: `OptsIO.io_business.get_active_business(userobj)`. Nunca confiar en un negocio enviado por el cliente.

## Estados y auditoría

- Auditoría por paso con el par `<paso>_fecha` / `<paso>_usuario` (`cargado_`, `actualizado_`, `verificado_`, `aprobado_`, `anulado_`). `IOMaction` completa `cargado_*` y `actualizado_*` automáticamente; `_usuario` guarda `first_name` (usar `io_business.user_label`).
- Estado de una operación: campo `estado` (CharField). Operaciones con circuito de aprobación heredan `OptsIO.workflow.WorkflowMixin`: `cargado → verificado → aprobado` (extensible con `WORKFLOW_STATES`), permiso Django por paso, segregación de usuarios opcional, `anular()`, historial en `workflow_log`.
- El cierre (`aprobado`) es lo que dispara automatismos; nunca generar asientos ni movimientos de fondos desde un estado intermedio.

## Eventos y automatismos

- `OptsIO.events.emit('<plugin>.<modelo>.<estado>', obj, business=...)` registra el evento una sola vez (clave de idempotencia) y lo procesa **Celery**. No usar crontab de sondeo para lógica de negocio.
- Cada handler se ejecuta con éxito una sola vez por evento, en la misma transacción que su efecto. Aun así, un handler debe ser idempotente por sí mismo (ej: `MTesoreria.registrar_movimiento(clave=...)`).
- Suscripción en `plugin.py` con `get_event_handlers()`; acepta comodines (`'*.aprobado'`).
- Un evento sin oyentes instalados no se persiste (`emit` devuelve `None`): instalar un plugin oyente más tarde no recupera lo anterior a su instalación.

### Eventos publicados

| Evento | Lo emite | Lo escuchan |
|--------|----------|-------------|
| `sifen.documento.aprobado` / `.cancelado` | Core Sifen (`Sifen/sifen_events.py`, al cerrar el tracking de lotes o consultar un CDC) | Contabilidad (venta / NC / reverso) |
| `cobro.recibo.aprobado` | Cobro, al generar el recibo | Deposito (depósitos pendientes), Contabilidad |
| `deposito.deposito.<estado>` | Deposito (workflow) | Contabilidad |
| `egreso.gasto.<estado>`, `egreso.gasto.rendido` | Egreso | Contabilidad |
| `egreso.pago.<estado>`, `egreso.transferencia.<estado>` | Egreso | Contabilidad |
| `ecommerce.pedido.<estado>` | Ecommerce (`recibido → pagado → preparado → despachado`) | `pagado`: Ecommerce (factura electrónica), Deposito (depósito pendiente) |
| `almacen.recepcion.<estado>`, `almacen.ajuste.<estado>` | Almacen | — |
| `<plugin>.<modelo>.anulado` | `WorkflowMixin.anular()` | Contabilidad (contra-asiento) |

El payload lleva todo lo que el oyente necesita (montos, ids de cuenta/caja/categoría, número, fecha): un plugin
oyente no importa modelos del emisor.

## Contabilidad

- Plan de cuentas por **plantillas** (`Contabilidad/plantillas/planes.py`): idempotentes, combinables y extensibles a mano.
- Los **formatos de asiento** (`plantillas/formatos.py` → `FormatoAsiento`, editables por negocio) hablan de **roles**
  (`clientes`, `iva_debito_10`, `banco`...) y de **claves de monto** que calcula el handler del evento. `CuentaRol` asigna
  la cuenta de cada rol; `MapeoCuenta` da cuenta propia a un banco, caja o categoría de gasto.
- `MotorAsientos.generar()` es idempotente (`Asiento.clave`), asienta siempre en guaraníes y deja el evento en error si
  falta configuración; `MContabilidad.reprocesar_eventos` lo recupera sin duplicar.
- Para que un plugin nuevo asiente: emitir su evento de cierre con el payload, agregar un handler en
  `Contabilidad/handlers.py`, su formato en `plantillas/formatos.py` y suscribirlo en `Contabilidad/plugin.py`.

## Inventario y tienda online

- `Almacen`: todo cambio de stock pasa por `Almacen.models.mover_stock` (idempotente por `clave`, nunca negativo, sincroniza `Producto.stock`).
  Para vender: `reservar` → `despachar` (picking → almacenaje → recepción) o `liberar_reservas`. `averiados` no es vendible.
- `Ecommerce`: publica productos del maestro `Sifen.Producto` en una `Tienda`. El carrito vive en la sesión; precios y stock se validan
  siempre en el servidor. El seguimiento público del pedido usa un `token` UUID, nunca el número correlativo.
- Temas: `TemaTienda` = layout base + variables de color/tipografía + archivo CSS propio + CSS rápido, cargados después de
  `Ecommerce/static/Ecommerce/tienda.css`. Los valores del tema se validan/sanitizan antes de salir en un `<style>` público.

## Directrices de código (resumen; el detalle está en `context.md` y `crud_patterm.md`)

- Imports siempre al inicio del archivo, nunca dentro de métodos.
- Sin `try/except` en los métodos Python de negocio: validar y devolver `{'error': ...}`. Las excepciones de regla de negocio (`TesoreriaError`, `WorkflowError`) son para la API interna entre plugins.
- Archivos: lógica `mng_*.py`; templates terminan en `Ui.html`.
- Templates cargados por ajax: sin `let`/`const` a nivel superior; IDs con `{{ rr }}`; elementos de formulario referenciados por `name`.
- Numéricos: `type="text"` + Inputmask, y leer `inputmask.unmaskedvalue()` al guardar (el backend recibe punto decimal).
- Respuestas del backend: patrón `msgs` + `UiB.BeMsgHandle` y recarga del DataTable con `{{ t_guid }}`.
- URLs siempre con `{% url %}`; nunca hardcodeadas.
- No cambiar el comportamiento del CRUD genérico salvo pedido explícito.
- Migraciones: no van a git, cada entorno genera las suyas.

## Generador de pantallas CRUD

`bin/gen_plugin_ui.py` genera el par listado + formulario con el patrón de `CrearInterfaz.md` a partir de un spec Python (`bin/ui_specs/<plugin>.py`). Uso: `python bin/ui_specs/tesoreria.py`. Las pantallas que no son CRUD puro (paneles, flujos) se escriben a mano.
