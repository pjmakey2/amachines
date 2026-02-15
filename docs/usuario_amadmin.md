# Usuario Administrador por Defecto - amadmin

## 📋 Descripción

El sistema TOCA3D incluye un comando de Django management para crear automáticamente un usuario administrador por defecto llamado `amadmin` con contraseña autogenerada de forma segura.

## 🔑 Características

- **Usuario**: `amadmin`
- **Tipo**: Superusuario (acceso completo al sistema)
- **Contraseña**: Generada automáticamente con caracteres seguros
- **Email**: `admin@toca3d.local`
- **Nombre**: Admin Master

### Seguridad de la Contraseña

La contraseña generada cumple con los siguientes criterios:
- Longitud: 20 caracteres por defecto (configurable)
- Incluye: letras mayúsculas, minúsculas, números y símbolos
- Generada con `secrets` module (criptográficamente seguro)
- Garantiza al menos:
  - 1 letra mayúscula
  - 1 letra minúscula
  - 1 número
  - 1 símbolo especial (!@#$%^&*)

## 🚀 Uso

### Crear el Usuario Administrador

```bash
python manage.py create_amadmin
```

Este comando:
1. Genera una contraseña segura aleatoria de 20 caracteres
2. Crea el superusuario `amadmin`
3. Guarda las credenciales en el archivo `.amadmin` en la raíz del proyecto
4. Establece permisos restrictivos (600) al archivo para protegerlo

### Opciones Disponibles

#### Forzar Recreación

Si el usuario ya existe, puedes forzar su recreación:

```bash
python manage.py create_amadmin --force
```

Esto eliminará el usuario existente y creará uno nuevo con una nueva contraseña.

#### Personalizar Longitud de Contraseña

```bash
python manage.py create_amadmin --length 30
```

Genera una contraseña de 30 caracteres en lugar de 20.

#### Combinación de Opciones

```bash
python manage.py create_amadmin --force --length 25
```

## 📄 Archivo de Credenciales (.amadmin)

### Ubicación

```
/home/peter/projects/Toca3d/.amadmin
```

### Formato del Archivo

```
Usuario: amadmin
Contraseña: Ab3$xYz...

IMPORTANTE: Este archivo contiene credenciales sensibles.
NO lo compartas ni lo subas al repositorio.
```

### Permisos del Archivo

El archivo se crea automáticamente con permisos restrictivos:
- **Permisos**: `600` (rw-------)
- **Propietario**: Solo el usuario que ejecutó el comando puede leer/escribir
- **Otros**: Sin acceso

### Seguridad

⚠️ **IMPORTANTE**: El archivo `.amadmin` está incluido en `.gitignore` para prevenir que se suba al repositorio.

## 🔒 Seguridad

### Protección del Archivo

1. **En .gitignore**: El archivo `.amadmin` está explícitamente excluido del control de versiones
2. **Permisos restrictivos**: Solo el propietario puede leer el archivo
3. **No compartir**: Nunca compartir este archivo por correo, chat, o servicios en la nube

### Buenas Prácticas

1. **Después de crear el usuario**:
   ```bash
   # Verificar que .amadmin está ignorado
   git status

   # No debe aparecer .amadmin en la lista
   ```

2. **Respaldar credenciales de forma segura**:
   - Usar un gestor de contraseñas (LastPass, 1Password, Bitwarden)
   - O guardar en un archivo cifrado externo

3. **Eliminar el archivo después de guardar las credenciales**:
   ```bash
   rm .amadmin
   ```

   O mantenerlo solo durante desarrollo local

4. **Cambiar la contraseña en producción**:
   ```bash
   python manage.py changepassword amadmin
   ```

## 📝 Salida del Comando

### Creación Exitosa

```
Creando usuario administrador "amadmin"...

✓ Usuario "amadmin" creado exitosamente!
✓ Credenciales guardadas en: /home/peter/projects/Toca3d/.amadmin

⚠ IMPORTANTE: Guarda estas credenciales en un lugar seguro.

Usuario: amadmin
Contraseña: Xk9$mPzL3@nRqW7vY2sA

⚠ El archivo .amadmin contiene credenciales sensibles.
⚠ NO lo subas al repositorio (verificar .gitignore)
```

### Usuario Ya Existe

```
El usuario "amadmin" ya existe. Usa --force para recrearlo.
```

### Con --force

```
Eliminando usuario existente "amadmin"...
Creando usuario administrador "amadmin"...

✓ Usuario "amadmin" creado exitosamente!
...
```

## 🛠️ Implementación Técnica

### Ubicación del Comando

```
OptsIO/management/commands/create_amadmin.py
```

### Estructura del Comando

```python
class Command(BaseCommand):
    help = 'Crea el usuario administrador por defecto "amadmin"'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--length', type=int, default=20)

    def generate_password(self, length=20):
        # Generación segura con secrets module

    def save_password_to_file(self, username, password):
        # Guardar en .amadmin con permisos restrictivos

    def handle(self, *args, **options):
        # Lógica principal del comando
```

### Módulos Utilizados

- `secrets`: Generación criptográficamente segura de contraseñas
- `string`: Conjunto de caracteres permitidos
- `pathlib.Path`: Manejo de rutas del sistema de archivos
- `os.chmod`: Establecer permisos del archivo
- `django.contrib.auth.models.User`: Modelo de usuario de Django

## 📊 Casos de Uso

### 1. Instalación Inicial

Después de clonar el proyecto y configurar la base de datos:

```bash
# Aplicar migraciones
python manage.py migrate

# Crear usuario administrador
python manage.py create_amadmin

# Iniciar servidor
python manage.py runserver

# Acceder al sistema
http://localhost:8000/io/glogin/
```

### 2. Resetear Contraseña de Administrador

Si olvidaste la contraseña:

```bash
# Recrear usuario con nueva contraseña
python manage.py create_amadmin --force

# Leer las nuevas credenciales
cat .amadmin
```

### 3. Crear Usuario para Nuevo Desarrollador

```bash
# Crear usuario amadmin para desarrollo local
python manage.py create_amadmin

# Enviar credenciales de forma segura
# (por ejemplo, a través de un gestor de contraseñas compartido)
```

### 4. Automatización en Scripts de Deployment

```bash
#!/bin/bash
# deploy.sh

# Crear base de datos
createdb toca3d

# Aplicar migraciones
python manage.py migrate

# Crear usuario admin
python manage.py create_amadmin

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

echo "Deployment completo. Credenciales en .amadmin"
```

## 🔄 Mantenimiento

### Ver Credenciales

```bash
cat .amadmin
```

### Eliminar Archivo de Credenciales

```bash
rm .amadmin
```

### Cambiar Contraseña Manualmente

```bash
python manage.py changepassword amadmin
```

### Verificar que el Usuario Existe

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Verificar existencia
User.objects.filter(username='amadmin').exists()
# True

# Ver detalles
user = User.objects.get(username='amadmin')
print(f"Usuario: {user.username}")
print(f"Email: {user.email}")
print(f"Es superusuario: {user.is_superuser}")
print(f"Es staff: {user.is_staff}")
```

## ⚠️ Problemas Comunes

### Error: Usuario ya existe

**Problema**:
```
El usuario "amadmin" ya existe. Usa --force para recrearlo.
```

**Solución**:
```bash
python manage.py create_amadmin --force
```

### Error: No se puede escribir .amadmin

**Problema**:
```
✗ Error al guardar credenciales: [Errno 13] Permission denied: '.amadmin'
```

**Solución**:
```bash
# Verificar permisos del directorio
ls -la /home/peter/projects/Toca3d/

# Cambiar propietario si es necesario
sudo chown peter:peter /home/peter/projects/Toca3d/

# Intentar de nuevo
python manage.py create_amadmin --force
```

### Archivo .amadmin aparece en git status

**Problema**:
```bash
git status
# Muestra: .amadmin
```

**Solución**:
```bash
# Verificar .gitignore
cat .gitignore | grep amadmin
# Debe mostrar: .amadmin

# Si no está, agregarlo
echo ".amadmin" >> .gitignore

# Si ya fue agregado al staging area
git rm --cached .amadmin

# Commit del .gitignore
git add .gitignore
git commit -m "Agregar .amadmin a .gitignore"
```

## 📚 Referencias

- [Django Management Commands](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)
- [Python secrets module](https://docs.python.org/3/library/secrets.html)
- [Django User Model](https://docs.djangoproject.com/en/stable/ref/contrib/auth/)
- [File Permissions in Linux](https://www.guru99.com/file-permissions.html)

---

**Fecha de creación**: 2025-11-12
**Comando**: `python manage.py create_amadmin`
**Ubicación**: `OptsIO/management/commands/create_amadmin.py`
**Archivo de credenciales**: `.amadmin` (en .gitignore)
