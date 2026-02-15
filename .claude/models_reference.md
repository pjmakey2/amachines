# Referencia de Modelos - Amachine

## Estructuras Críticas de Modelos

### UserProfile (OptsIO/models.py)

```python
class UserProfile(models.Model):
    username = models.CharField(max_length=80, unique=True)  # ¡NO es ForeignKey!
    preferences = models.JSONField(default=dict)
    last_login = models.DateTimeField(null=True, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    last_change_password = models.DateTimeField(null=True, blank=True)
```

**IMPORTANTE**:
- `username` es un CharField, NO un ForeignKey al modelo User
- Para filtrar por usuario: `userprofileobj__username` NO `userprofileobj__user__username`

### UserBusiness (OptsIO/models.py)

```python
class UserBusiness(models.Model):
    userprofileobj = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
```

**Lógica de Negocio**:
- Un usuario puede tener MÚLTIPLES negocios asignados
- Solo UN negocio puede tener `active=True` a la vez
- `active` significa "el negocio con el que el usuario está trabajando actualmente"
- Al establecer un negocio como activo, DEBE desactivar todos los demás primero:
  ```python
  UserBusiness.objects.filter(userprofileobj=profile).update(active=False)
  UserBusiness.objects.create(userprofileobj=profile, businessobj=business, active=True)
  ```

**Consultas con seModel**:
```javascript
// Obtener negocios del usuario
tdata.append('model_name', 'UserBusiness');
tdata.append('fields', jfy(['id', 'active', 'businessobj__id', 'businessobj__name']));
tdata.append('mquery', jfy([{'field': 'userprofileobj__username', 'value': username}]));
```

### Business (Sifen/models.py)

```python
class Business(models.Model):
    name = models.CharField(max_length=120)
    abbr = models.CharField(max_length=60)
    ruc = models.CharField(max_length=60, unique=True)
    ruc_dv = models.IntegerField(default=0)
    contribuyenteobj = models.ForeignKey(TipoContribuyente, on_delete=models.CASCADE)
    nombrefactura = models.CharField(max_length=120)
    nombrefantasia = models.CharField(max_length=120)
    numero_casa = models.IntegerField(default=0)
    direccion = models.CharField(max_length=200, null=True)
    dir_comp_uno = models.CharField(max_length=200, null=True)
    dir_comp_dos = models.CharField(max_length=200, null=True)
    ciudadobj = models.ForeignKey(Ciudades, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=40, default=0)
    celular = models.CharField(max_length=40, default=0)
    correo = models.CharField(max_length=120)
    denominacion = models.CharField(max_length=120)
    logo = models.FileField(upload_to='business', max_length=500, null=True)
    actividadecoobj = models.ForeignKey(ActividadEconomica, on_delete=models.CASCADE)
    # ... campos de auditoría
```

## Patrones de Consulta Comunes

### Obtener Negocio Activo del Usuario
```javascript
var tdata = new FormData();
tdata.append('module', 'OptsIO');
tdata.append('package', 'io_serial');
tdata.append('attr', 'IoS');
tdata.append('mname', 'seModel');
tdata.append('model_app_name', 'OptsIO');
tdata.append('model_name', 'UserBusiness');
tdata.append('fields', jfy(['businessobj__id', 'businessobj__name', 'businessobj__ruc']));
tdata.append('dbcon', 'default');
tdata.append('mquery', jfy([
    {'field': 'userprofileobj__username', 'value': username},
    {'field': 'active', 'value': true}
]));
```

### Obtener Todos los Negocios (para asignación)
```javascript
tdata.append('model_app_name', 'Sifen');
tdata.append('model_name', 'Business');
tdata.append('fields', jfy(['id', 'name', 'ruc', 'logo']));
// Sin mquery = todos los registros
```

## Métodos del Backend

### Ubicación: OptsIO/mng_user_profile.py

**assign_business_to_user()**
- Asigna un Business existente a un Usuario
- Crea registro UserBusiness
- Puede establecer como activo o no (parámetro set_active)
- Limpia flag de sesión en éxito

**create_business_and_assign()**
- Crea nuevo Business
- Automáticamente asigna al usuario actual
- Establece como activo por defecto
- Maneja subida de archivo (logo)
- Limpia flag de sesión en éxito

### Ubicación: OptsIO/mng_registration.py

**set_active_business()**
- Cambia qué negocio está activo
- Desactiva todos los demás primero
- Actualiza campo UserBusiness.active

**get_active_business()**
- Retorna datos del negocio activo para usuario logueado
- Usado por toolbar para obtener pk para edición

## Errores Comunes a Evitar

1. ❌ Filtrar por `userprofileobj__user__username` (UserProfile no tiene FK a User)
   ✅ Filtrar por `userprofileobj__username`

2. ❌ Tener múltiples negocios con active=True para el mismo usuario
   ✅ Siempre desactivar otros antes de activar uno

3. ❌ Usar global Business.objects.first() para logo/config
   ✅ Obtener negocio activo desde UserBusiness para usuario actual

4. ❌ Asumir que UserProfile está directamente vinculado a Django User
   ✅ UserProfile.username es un CharField que coincide con User.username

---

**Última Actualización**: 2025-11-22
**Mantenido por**: Equipo de Desarrollo Amachine
