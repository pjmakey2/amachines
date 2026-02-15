Crear una estructura de modelos en OptsIo 

 * Roles (Los roles de los usuarios)
 * RolesUser (Relacion de que roles tiene el usuario, un usuario puede tener multiple roles )
 * UserProfile (Extender los usuarios de django User)
 * RolesApps (Relacion de Modelos Apps con la de Roles).
    -> Para controlar que apps pueden ver que roles.
 * Crear las interfaces .html correspondientes baso ./templates/OptsIO/

Estos puntos son vitables para empezar cualquier proyecto

Lee todos los archivos .md dentro .claude/ la lectura de los .md dentro de .claude/ debe ser lenta y exhaustiva, aqui esta el disenho de la base estructural del proyecto, asi que cada descripcion de directris definida ahi es crucial que la entiendas y debes de leer todos los archivos .md, sin pasarte por alto ninguno


1. Ser explícito con verificación:
    - "Lee TODOS los .md en .claude/. Antes de continuar, lista los archivos que leíste."
    - "Confirma que leíste los X archivos antes de proceder"
2. Pedir confirmación de completitud:
    - "Primero usa Glob o find ./claude/ -name "*.md" -ls para listar todos los .md, luego lee cada uno"
4. Consecuencia explícita:
    - "Si empiezas sin leer todo, el código estará mal y tendrás que rehacerlo"

---

## Resumen de Implementación Completada

### 1. Modelos (OptsIO/models.py:212-283)
- **Roles**: Definición de roles por negocio
- **RolesUser**: Relación muchos-a-muchos entre usuarios y roles
- **RolesApps**: Control de qué aplicaciones puede ver cada rol

### 2. Backend (OptsIO/io_roles.py)
Clase `IORoles` con métodos:
- `create_roles()` / `delete_roles()`
- `create_rolesuser()` / `delete_rolesuser()`
- `create_rolesapps()` / `delete_rolesapps()`

### 3. Migración
- `OptsIO/migrations/0009_roles_rolesapps_rolesuser.py`

### 4. Interfaces HTML (templates/OptsIO/)
- **RolesUi.html** / **RolesCreateUi.html** - Gestión de roles
- **RolesUserUi.html** / **RolesUserCreateUi.html** - Asignación de roles a usuarios
- **RolesAppsUi.html** / **RolesAppsCreateUi.html** - Permisos de aplicaciones

### 5. Entradas de Menú
Agregadas 3 aplicaciones en el menú "Sistema":
- Roles
- Roles de Usuarios
- Permisos de Aplicaciones

## Pasos para Aplicar los Cambios

1. **Ejecutar la migración:**
```bash
python manage.py migrate OptsIO
```

2. **Crear entradas en el menú:**
```bash
python manage.py setup_sifen_menu
```

## Características del Sistema

- **Multi-tenant**: Cada negocio tiene sus propios roles
- **CRUD completo**: Crear, editar, borrar con confirmación
- **Búsqueda**: Búsqueda en tiempo real en todas las interfaces
- **Validación**: Unique constraints para evitar duplicados
- **Auditoría**: Campos created_at y updated_at automáticos

El sistema está listo para usar. Una vez ejecutes los comandos, podrás acceder a las tres aplicaciones desde el menú Sistema.

---

## Gestión de Usuarios - Implementación Completada

### Archivos Creados

#### Backend (OptsIO/mng_master.py)
Clase `MMaster` con métodos:
- `create_user()` - Crea/actualiza User de Django y UserProfile simultáneamente
- `delete_user()` - Elimina User y UserProfile asociado

**Características del método create_user:**
- Maneja User (Django auth) y UserProfile en una transacción
- Campos de User: username, email, first_name, last_name, password, is_active, is_staff, is_superuser
- Campos de UserProfile: photo (ImageField)
- Password encriptado con `set_password()`
- Validación de contraseñas coincidentes
- En modo edición, password opcional (solo si se quiere cambiar)
- Username no modificable en edición
- Subida de foto de perfil con preview

#### Interfaces HTML (templates/OptsIO/)
- **UserUi.html** - Lista de usuarios con DataTables
  - Columnas: username, email, nombre, apellido, activo, staff, superusuario, último login
  - Búsqueda por username, email, nombre, apellido
  - Selección múltiple para borrado

- **UserCreateUi.html** - Formulario crear/editar usuario
  - Sección "Datos del Usuario": username, email, nombre, apellido
  - Sección "Contraseña": password y confirmación (opcional en edición)
  - Sección "Permisos": is_active, is_staff, is_superuser
  - Sección "Foto de Perfil": subida con preview

#### Entrada de Menú
- Agregada aplicación "Usuarios" en menú Sistema (prioridad 5)
- Icono: `mdi mdi-account-multiple`

### Integración User y UserProfile

El sistema maneja ambos modelos de forma transparente:
1. Al crear un User, se crea automáticamente su UserProfile
2. Al actualizar, se actualizan ambos modelos
3. Al eliminar, se eliminan ambos en cascada
4. La foto se guarda en UserProfile
5. Username se comparte entre ambos modelos

### Seguridad

- Contraseñas encriptadas con Django's `set_password()`
- Validación de contraseñas coincidentes
- Username inmutable después de creación
- Permisos granulares (activo, staff, superusuario)

El sistema está listo para usar. Una vez ejecutes los comandos, podrás acceder a las cuatro aplicaciones desde el menú Sistema.

---

## Filtrado de Aplicaciones por Roles - Implementación Completada

### Archivo Modificado

#### OptsIO/apps_ui.py - Método `get_apps()`

Se implementó el filtrado de aplicaciones basado en roles del usuario. El método ahora funciona de la siguiente manera:

**Lógica de Filtrado:**

1. **Usuario Superusuario** (`is_superuser=True`):
   - Retorna TODAS las aplicaciones activas
   - Sin restricciones de roles

2. **Usuario Regular con Roles**:
   - Obtiene el UserProfile del usuario
   - Consulta RolesUser para obtener los roles activos asignados al usuario
   - Consulta RolesApps para obtener las aplicaciones asignadas a esos roles
   - Retorna solo las aplicaciones que tienen permisos

3. **Usuario sin Roles o sin UserProfile**:
   - Retorna lista vacía (sin acceso a aplicaciones)

4. **Usuario no autenticado**:
   - Retorna lista vacía

**Código Implementado:**

```python
def get_apps(self, *args, **kwargs):
    """
    Obtiene las apps activas filtradas por roles del usuario.
    - Si el usuario es superuser: retorna todas las apps
    - Si el usuario tiene roles: retorna solo las apps asignadas a sus roles
    - Si el usuario no tiene roles: retorna lista vacía
    """
    userobj = kwargs.get('userobj')

    if userobj and userobj.is_superuser:
        # Superuser ve todas las apps
        apps = Apps.objects.filter(active=True).values(...)
    elif userobj:
        # Usuario regular: filtrar por roles
        user_profile = UserProfile.objects.get(username=userobj.username)
        user_roles = RolesUser.objects.filter(
            userprofileobj=user_profile,
            active=True
        ).values_list('rolesobj_id', flat=True)

        allowed_app_ids = RolesApps.objects.filter(
            rolesobj_id__in=user_roles,
            active=True
        ).values_list('appsobj_id', flat=True).distinct()

        apps = Apps.objects.filter(id__in=allowed_app_ids, active=True).values(...)
```

**Flujo de Permisos:**

```
Usuario → RolesUser → Roles → RolesApps → Apps
```

**Ventajas del Sistema:**

- **Seguridad por defecto**: Los usuarios sin roles no ven ninguna aplicación
- **Flexibilidad**: Superusuarios mantienen acceso completo
- **Granularidad**: Control preciso de qué aplicaciones ve cada rol
- **Multi-tenant**: Respeta la estructura de negocios del sistema
- **Performance**: Usa queries optimizadas con `values_list` y `distinct()`

**Casos de Uso:**

1. **Administrador del Sistema** (is_superuser=True):
   - Ve todas las apps: Usuarios, Roles, Ventas, Compras, etc.

2. **Rol "Vendedor"** asignado a Apps: Ventas, Clientes:
   - Usuario con rol Vendedor solo ve: Ventas, Clientes

3. **Usuario Nuevo sin Roles**:
   - No ve ninguna aplicación hasta que se le asigne un rol

El sistema está completamente funcional y listo para usar.

---

## Asignación de Negocios a Usuarios - Implementación Completada

### Archivos Creados

#### Backend (OptsIO/mng_master.py)

Se agregaron métodos a la clase `MMaster`:

- **`create_userbusiness()`** - Asigna un negocio a un usuario
  - Valida que usuario y negocio existan
  - Previene asignaciones duplicadas
  - Solo permite UN negocio activo por usuario a la vez
  - Al activar un negocio, desactiva automáticamente los demás del usuario
  - Maneja tanto creación como actualización

- **`delete_userbusiness()`** - Elimina asignaciones de negocio a usuario
  - Permite eliminación individual o múltiple
  - Retorna mensajes descriptivos por cada eliminación

#### Interfaces HTML (templates/OptsIO/)

- **BusinessUserUi.html** - Lista de asignaciones negocio-usuario con DataTables
  - Columnas: ID, Usuario, Email, Negocio, RUC, Activo, Acciones
  - Búsqueda por username, email, nombre de negocio, RUC
  - Selección múltiple para borrado masivo
  - Botones: Asignar nuevo, Editar, Eliminar

- **BusinessUserCreateUi.html** - Formulario asignar/editar negocio a usuario
  - Sección principal: Usuario (select), Negocio (select), Estado (activo/inactivo)
  - Nota informativa: "Solo puede haber un negocio activo por usuario"
  - Validaciones: Usuario y negocio requeridos

#### Entrada de Menú

- Agregada aplicación "Usuarios de Negocio" en menú **Negocio** (prioridad 4)
- Icono: `mdi mdi-account-network`
- Background: `#0D9488` (teal)

### Lógica de Negocio

**Regla Crítica:** Un usuario puede tener MÚLTIPLES negocios asignados, pero solo UNO puede estar `active=True` a la vez.

**Flujo de Asignación:**

1. **Crear nueva asignación activa:**
   ```python
   # Desactiva todos los negocios del usuario
   UserBusiness.objects.filter(userprofileobj=profile).update(active=False)

   # Crea la nueva asignación como activa
   UserBusiness.objects.create(
       userprofileobj=profile,
       businessobj=business,
       active=True
   )
   ```

2. **Actualizar asignación a activa:**
   ```python
   # Si se activa, desactiva todos los demás primero
   if active and not user_business.active:
       UserBusiness.objects.filter(
           userprofileobj=user_business.userprofileobj
       ).update(active=False)

   user_business.active = active
   user_business.save()
   ```

3. **Prevención de duplicados:**
   - Antes de crear, verifica que no exista la misma combinación usuario-negocio
   - Si existe, retorna error descriptivo

### Casos de Uso

**Caso 1: Usuario con múltiples negocios**
```
Usuario: juan@example.com
  - Negocio A (RUC: 12345) - ACTIVO ✓
  - Negocio B (RUC: 67890) - Inactivo
  - Negocio C (RUC: 11111) - Inactivo
```
Juan trabaja actualmente con Negocio A. Puede cambiar al Negocio B desde el toolbar, lo cual desactivará A y activará B.

**Caso 2: Múltiples usuarios de un negocio**
```
Negocio XYZ (RUC: 99999)
  - Usuario: admin@xyz.com - ACTIVO
  - Usuario: vendedor@xyz.com - ACTIVO
  - Usuario: contador@xyz.com - ACTIVO
```
Varios usuarios pueden tener el mismo negocio activo simultáneamente.

**Caso 3: Usuario sin negocios**
```
Usuario: nuevo@example.com
  - Sin asignaciones
```
El sistema mostrará modal de setup inicial pidiendo asignar o crear negocio.

### Integración con Sistema Existente

Esta funcionalidad se integra con:

1. **OptsIO/mng_user_profile.py:**
   - `assign_business_to_user()` - Usado en setup inicial
   - `create_business_and_assign()` - Usado en setup inicial

2. **Template Tags (OptsIO/templatetags/io_tags.py):**
   - `{% business_name %}` - Obtiene negocio activo del usuario
   - `{% business_logo %}` - Logo del negocio activo
   - Etc.

3. **Middleware:**
   - Verifica que usuario tenga negocio activo
   - Redirige a setup si no tiene negocio

### Comandos para Aplicar

```bash
# Ejecutar setup de menú para crear la entrada
python manage.py setup_sifen_menu
```

El sistema está completamente funcional y listo para usar.
