# Disponibilizar Apps en AMLauncherUi

Guía para agregar una interfaz al launcher principal (`templates/AMLauncherUi.html`).

---

## Cómo funciona

El launcher usa el método `Menu.get_apps` para armar el grid de apps agrupadas por menú:

```javascript
// AMLauncherUi.html → loadApps()
fdata.append('module',  'OptsIO');
fdata.append('package', 'apps_ui');
fdata.append('attr',    'Menu');
fdata.append('mname',   'get_apps');
```

`Menu.get_apps` (`OptsIO/apps_ui.py`) combina tres cosas:

1. **Prioridad de los menús** — desde el modelo `Menu`
2. **Permisos del usuario** — vía `UserProfile` + `RolesUser` + `RolesApps` (superuser ve todo)
3. **Apps activas** — desde el modelo `Apps`

Retorna la lista ordenada por `(menu_prioridad, app.prioridad)`. El launcher la agrupa por `app.menu` (string exacto) y pinta una sección por cada grupo.

---

## Los modelos

### `Apps` — cada entrada es un card en el launcher

Ejemplo real:
```python
{
    'id': 76,
    'prioridad': 1,
    'menu': 'COBROS',
    'menu_icon': 'mdi mdi-cash-register',
    'app_name': 'cobro_gestion',
    'friendly_name': 'Gestión de Cobros',
    'icon': 'mdi mdi-cash-multiple',
    'url': 'Cobro/GestionUi.html',
    'version': '1.0',
    'background': '#10B981',
    'active': True,
}
```

### `Menu` — define la sección y su orden

Ejemplo real:
```python
{
    'id': 19,
    'prioridad': 40,
    'menu': 'COBROS',
    'friendly_name': 'COBROS',
    'icon': 'mdi mdi-cash-register',
    'url': '#',
    'background': '#8B5CF6',
    'active': True,
}
```

**Importante:** no hay FK entre `Apps` y `Menu`. La relación es **implícita por el campo `menu`** (mismo string en ambos modelos).

---

## Procedimiento para disponibilizar una interfaz

Cuando el pedido es *"disponibilizá la interfaz `X` en el menú `Y`"*, los pasos son:

### 1. Verificar si el `Menu` ya existe

```python
from OptsIO.models import Menu as MenuModel
MenuModel.objects.filter(menu='Transacciones').first()
```

- **Si existe:** reusar su `menu_icon` para la entrada en `Apps` (consistencia visual).
- **Si NO existe:** crearlo primero, eligiendo:
  - `prioridad`: un número que lo ubique en la posición deseada (mirar las prioridades existentes)
  - `menu_icon` / `icon`: un `mdi-*` que represente la sección
  - `background`: color hex

### 2. Calcular la `prioridad` de la nueva `Apps`

Contar cuántas apps hay ya en ese menú y asignar el siguiente número:

```python
from OptsIO.models import Apps
next_prioridad = Apps.objects.filter(menu='Transacciones').count() + 1
```

Así la nueva app queda al final de su sección.

### 3. Crear la entrada en `Apps`

```python
Apps.objects.create(
    prioridad=next_prioridad,
    menu='Transacciones',                          # mismo string que Menu.menu
    menu_icon='mdi mdi-swap-horizontal',           # mismo que Menu.icon (si existía)
    app_name='sifen_bi_rpt_productos',             # identificador único, sin espacios
    friendly_name='BI - Ventas por Producto',      # texto visible en el card
    icon='mdi mdi-chart-bar',                      # icono del card
    url='Sifen/DocumentHeaderBiRptUi.html',        # path relativo a templates/
    version='1.0',
    background='#8B5CF6',                          # color hex del card
    active=True,
)
```

### 4. (Si el usuario no es superuser) Asignar a un rol

```python
from OptsIO.models import Apps, Roles, RolesApps
app = Apps.objects.get(app_name='sifen_bi_rpt_productos')
rol = Roles.objects.get(name='Administrador', businessobj__ruc='80070523')
RolesApps.objects.create(rolesobj=rol, appsobj=app, businessobj=rol.businessobj, active=True)
```

---

## Valores a elegir cuando se crea la entrada

| Campo | Cómo elegirlo |
|-------|---------------|
| `prioridad` | `Apps.objects.filter(menu=X).count() + 1` — va al final de su sección |
| `menu` | El nombre exacto del menú (crear en `Menu` si no existe) |
| `menu_icon` | Copiar de `Menu.icon` si el menú ya existía |
| `app_name` | Identificador único, sin espacios, snake_case (ej. `sifen_bi_rpt_productos`) |
| `friendly_name` | Texto visible al usuario |
| `icon` | `mdi-*` que represente la funcionalidad específica |
| `url` | Path relativo a `templates/` |
| `version` | Siempre `'1.0'` por ahora |
| `background` | Color hex — puede ser random o consistente con la sección |
| `active` | Siempre `True` salvo indicación contraria |

---

## Troubleshooting

| Síntoma | Causa |
|---------|-------|
| App no aparece (usuario no-super) | Falta `RolesApps` para el rol del usuario |
| App no aparece (superuser) | `active=False`, template no existe, o falta el registro en `Apps` |
| App aparece pero click da error | `url` apunta a template inexistente o con error |
| App en sección incorrecta | `Apps.menu` no coincide con `Menu.menu` (case-sensitive) |
| Sección desordenada | Falta registro en `Menu` para esa sección, o `Menu.active=False` |
