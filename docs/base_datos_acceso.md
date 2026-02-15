# Base de Datos - Configuración de Acceso PostgreSQL

## 📋 Creación de Usuario y Base de Datos

### 1. Conectarse a PostgreSQL como superusuario
```bash
sudo -u postgres psql
```

### 2. Crear el usuario `toca3d` con contraseña
```sql
CREATE USER toca3d WITH PASSWORD 'tu_contraseña_segura';
```

### 3. Crear la base de datos `toca3d` (si no existe)
```sql
CREATE DATABASE toca3d OWNER toca3d;
```

### 4. Conectarse a la base de datos `toca3d`
```sql
\c toca3d
```

### 5. Otorgar privilegios de conexión y creación de esquemas
```sql
GRANT CONNECT ON DATABASE toca3d TO toca3d;
GRANT USAGE, CREATE ON SCHEMA public TO toca3d;
```

### 6. Otorgar privilegios de lectura y escritura en todas las tablas existentes
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO toca3d;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO toca3d;
```

### 7. Configurar privilegios por defecto para tablas futuras
```sql
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toca3d;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO toca3d;
```

### 8. Verificar los permisos
```sql
\du toca3d
\l toca3d
```

### 9. Salir de PostgreSQL
```sql
\q
```

## 🔒 Script Completo (Copiar y Pegar)

```bash
# Conectarse a PostgreSQL
sudo -u postgres psql
```

```sql
-- Crear usuario
CREATE USER toca3d WITH PASSWORD 'tu_contraseña_segura';

-- Crear base de datos
CREATE DATABASE toca3d OWNER toca3d;

-- Conectarse a la base de datos
\c toca3d

-- Otorgar privilegios
GRANT CONNECT ON DATABASE toca3d TO toca3d;
GRANT USAGE, CREATE ON SCHEMA public TO toca3d;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO toca3d;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO toca3d;

-- Privilegios por defecto para tablas futuras
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO toca3d;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO toca3d;

-- Verificar
\du toca3d
\l toca3d

-- Salir
\q
```

## 🧪 Probar la Conexión

Desde la terminal, prueba conectarte con el nuevo usuario:

```bash
psql -U toca3d -d toca3d -h localhost
```

Ingresa la contraseña cuando te la solicite.

Comandos útiles dentro de psql:
```sql
-- Ver todas las tablas
\dt

-- Ver permisos en una tabla específica
\dp nombre_tabla

-- Ver información de la base de datos
\l+

-- Salir
\q
```

## ⚙️ Configuración en Django (settings.py)

### Opción 1: Configuración Directa
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'toca3d',
        'USER': 'toca3d',
        'PASSWORD': 'tu_contraseña_segura',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Opción 2: Usando Variables de Entorno (Recomendado)
```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'toca3d'),
        'USER': os.environ.get('DB_USER', 'toca3d'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

Crear archivo `.env` en la raíz del proyecto:
```bash
DB_NAME=toca3d
DB_USER=toca3d
DB_PASSWORD=tu_contraseña_segura
DB_HOST=localhost
DB_PORT=5432
```

**Nota**: Asegúrate de agregar `.env` al archivo `.gitignore` para no subir credenciales al repositorio.

## 🔐 Permisos Otorgados

El usuario `toca3d` tiene los siguientes permisos:

### ✅ Puede hacer:
- **SELECT**: Leer datos de las tablas
- **INSERT**: Insertar nuevos registros
- **UPDATE**: Actualizar registros existentes
- **DELETE**: Eliminar registros
- **USAGE en sequences**: Usar secuencias para auto-incrementos
- **SELECT en sequences**: Leer valores de secuencias
- **CREATE en schema public**: Crear objetos en el esquema público (necesario para migraciones de Django)

### ❌ NO puede hacer:
- **DROP DATABASE**: Eliminar la base de datos
- **DROP TABLE**: Eliminar tablas (a menos que las haya creado)
- **ALTER SYSTEM**: Modificar configuración del sistema
- **CREATE DATABASE**: Crear otras bases de datos
- **CREATE USER/ROLE**: Crear usuarios o roles
- **Acceder a otras bases de datos**: Solo tiene acceso a `toca3d`

## 🔄 Comandos Útiles de Administración

### Cambiar la contraseña del usuario
```sql
ALTER USER toca3d WITH PASSWORD 'nueva_contraseña';
```

### Revocar todos los privilegios (si es necesario)
```sql
REVOKE ALL PRIVILEGES ON DATABASE toca3d FROM toca3d;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM toca3d;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM toca3d;
```

### Eliminar el usuario (primero eliminar la base de datos)
```sql
DROP DATABASE toca3d;
DROP USER toca3d;
```

### Ver conexiones activas a la base de datos
```sql
SELECT * FROM pg_stat_activity WHERE datname = 'toca3d';
```

### Terminar conexiones activas (si necesitas eliminar la BD)
```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'toca3d' AND pid <> pg_backend_pid();
```

## 🛠️ Troubleshooting

### Error: "FATAL: Peer authentication failed for user toca3d"
Edita el archivo `pg_hba.conf`:
```bash
sudo nano /etc/postgresql/[version]/main/pg_hba.conf
```

Cambia la línea:
```
local   all             all                                     peer
```

Por:
```
local   all             all                                     md5
```

Reinicia PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Error: "FATAL: password authentication failed for user toca3d"
Verifica que la contraseña sea correcta o cámbiala:
```sql
ALTER USER toca3d WITH PASSWORD 'nueva_contraseña';
```

### Error: "permission denied for table"
Asegúrate de haber ejecutado todos los GRANT correctamente:
```sql
\c toca3d
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO toca3d;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO toca3d;
```

### Django no puede crear tablas durante migraciones
Verifica que el usuario tenga permisos de CREATE:
```sql
GRANT CREATE ON SCHEMA public TO toca3d;
```

## 📊 Verificación de Permisos

### Ver todos los permisos del usuario
```sql
\du+ toca3d
```

### Ver permisos en la base de datos
```sql
\l+ toca3d
```

### Ver permisos en las tablas
```sql
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'toca3d' AND table_schema = 'public';
```

### Ver permisos en secuencias
```sql
SELECT grantee, privilege_type
FROM information_schema.role_usage_grants
WHERE grantee = 'toca3d' AND object_schema = 'public';
```

## 🔄 Migraciones de Django

Después de configurar la base de datos, ejecuta las migraciones:

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Verificar conexión
python manage.py dbshell
```

## 📝 Notas Importantes

1. **Seguridad**:
   - Usa contraseñas seguras (mínimo 12 caracteres, combinando letras, números y símbolos)
   - No compartas las credenciales en el código fuente
   - Usa variables de entorno o archivos .env

2. **Backup**:
   - Realiza backups regulares de la base de datos
   ```bash
   pg_dump -U toca3d -d toca3d -F c -f toca3d_backup.dump
   ```
   - Restaurar backup:
   ```bash
   pg_restore -U toca3d -d toca3d -v toca3d_backup.dump
   ```

3. **Producción**:
   - En producción, considera usar un usuario diferente para cada ambiente (dev, staging, prod)
   - Implementa políticas de rotación de contraseñas
   - Limita las conexiones por IP en `pg_hba.conf`

4. **Monitoreo**:
   - Monitorea las conexiones activas
   - Revisa los logs de PostgreSQL regularmente
   - Implementa alertas para errores de autenticación

## 🔗 Referencias

- [PostgreSQL Documentation - GRANT](https://www.postgresql.org/docs/current/sql-grant.html)
- [PostgreSQL Documentation - CREATE USER](https://www.postgresql.org/docs/current/sql-createuser.html)
- [Django PostgreSQL Notes](https://docs.djangoproject.com/en/stable/ref/databases/#postgresql-notes)

---

**Fecha de creación**: 2025-11-12
**Usuario de BD**: toca3d
**Base de Datos**: toca3d
**Tipo de Permisos**: Lectura/Escritura (SELECT, INSERT, UPDATE, DELETE)
