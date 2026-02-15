from django.db import models
# Create your models here.

class SysParams(models.Model):
    valor = models.CharField(max_length=120)
    tipo = models.CharField(max_length=60)
    valor_s = models.TextField()
    valor_f = models.FloatField()
    valor_j = models.JSONField(default=dict)
    ruta_archivo = models.FileField(upload_to='opts', null=True)
    vigencia = models.DateField()
    save_user = models.CharField(max_length=120)
    date_save = models.DateTimeField()

class Printers(models.Model):
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=120)
    uri = models.CharField(max_length=120)
    port = models.CharField(max_length=120)
    user = models.CharField(max_length=120)
    password = models.CharField(max_length=120)
    save_user = models.CharField(max_length=120)
    date_save = models.DateTimeField()
    delete_user = models.CharField(max_length=120, null=True)
    date_delete = models.DateTimeField(null=True)


class TrackBtask(models.Model):
    task_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    username = models.CharField(max_length=80, null=True)
    module = models.CharField(max_length=80, null=True)
    package = models.CharField(max_length=80, null=True)
    attr = models.CharField(max_length=80, null=True)
    mname = models.CharField(max_length=80, null=True)
    args = models.TextField(null=True)
    kwargs = models.TextField(null=True)
    state = models.CharField(max_length=80, null=True)

    class Meta:
        ordering = ('-created_at',)

    def __unicode__(self):
        return f'{self.module} {self.package} {self.attr} {self.mname}'


class FailedTask(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=125)
    full_name = models.TextField()
    args = models.TextField(null=True, blank=True)
    kwargs = models.TextField(null=True, blank=True)
    exception_class = models.TextField()
    exception_msg = models.TextField()
    traceback = models.TextField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=36)
    failures = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('-updated_at',)

    def __unicode__(self):
        return '%s %s [%s]' % (self.name, self.args, self.exception_class)

class Menu(models.Model):
    prioridad = models.IntegerField(default=0)
    menu = models.CharField(max_length=80)
    friendly_name = models.CharField(max_length=120)
    icon = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    background = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

class Apps(models.Model):
    prioridad = models.IntegerField(default=0)
    menu = models.CharField(max_length=80)
    menu_icon = models.CharField(max_length=200, default='mdi mdi-folder-outline')
    app_name = models.CharField(max_length=80, unique=True)
    friendly_name = models.CharField(max_length=120)
    icon = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    version = models.CharField(max_length=20)
    background = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

class AppsBookMakrs(models.Model):
    prioridad = models.IntegerField(default=0)
    app = models.ForeignKey(Apps, on_delete=models.DO_NOTHING)
    username = models.CharField(max_length=80)

    class Meta:
        db_table = 'apps_man_appsbookmarks'
        unique_together = (('app', 'username'),)


class UserTask(models.Model):
    """
    Stores active tasks for users to persist across page refreshes.
    Used by the bell notification system in the header.
    """
    TASK_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ]

    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    username = models.CharField(max_length=80, db_index=True)
    name = models.CharField(max_length=255)  # Display name for UI
    message = models.TextField(default='Starting...')
    progress = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='processing')
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)  # User dismissed from notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username', 'status']),
        ]

    def __str__(self):
        return f"{self.username} - {self.name} ({self.status})"

    @classmethod
    def create_task(cls, task_id, username, name):
        """Create a new task entry."""
        return cls.objects.create(
            task_id=task_id,
            username=username,
            name=name
        )

    @classmethod
    def get_user_tasks(cls, username, include_completed=False):
        """Get all active tasks for a user."""
        qs = cls.objects.filter(username=username)
        if not include_completed:
            qs = qs.exclude(status='completed')
        return qs

    @classmethod
    def update_task_progress(cls, task_id, message, progress, status='processing'):
        """Update task progress."""
        cls.objects.filter(task_id=task_id).update(
            message=message,
            progress=progress,
            status=status,
            updated_at=models.functions.Now()
        )

    @classmethod
    def complete_task(cls, task_id, message, result=None):
        """Mark task as completed."""
        cls.objects.filter(task_id=task_id).update(
            message=message,
            progress=100,
            status='completed',
            result=result,
            updated_at=models.functions.Now()
        )

    @classmethod
    def fail_task(cls, task_id, message, error=None):
        """Mark task as failed."""
        cls.objects.filter(task_id=task_id).update(
            message=message,
            status='error',
            error=error,
            updated_at=models.functions.Now()
        )

    @classmethod
    def cleanup_old_tasks(cls, hours=24):
        """Remove completed/error tasks older than specified hours."""
        from datetime import timedelta
        from django.utils import timezone
        cutoff = timezone.now() - timedelta(hours=hours)
        cls.objects.filter(
            status__in=['completed', 'error'],
            updated_at__lt=cutoff
        ).delete()


class UserProfile(models.Model):
    username = models.CharField(max_length=80, unique=True)
    preferences = models.JSONField(default=dict)
    last_login = models.DateTimeField(null=True, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)
    last_change_password = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    def get_photo_url(self):
        """Return photo URL if exists, otherwise None"""
        if self.photo:
            return self.photo.url
        return None

class UserBusiness(models.Model):
    userprofileobj = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    active = models.BooleanField(default=True)


# ============================================================================
# SISTEMA DE ROLES Y PERMISOS
# ============================================================================

class Roles(models.Model):
    """
    Roles de usuario para control de permisos.
    Cada negocio puede tener sus propios roles.
    """
    name = models.CharField(max_length=100, help_text="Nombre del rol (ej: Administrador, Vendedor)")
    description = models.TextField(blank=True, help_text="Descripción del rol")
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE, related_name='roles')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'optsio_roles'
        unique_together = ('name', 'businessobj')
        ordering = ['businessobj', 'name']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return f"{self.name} ({self.businessobj.name})"


class RolesUser(models.Model):
    """
    Relación entre usuarios y roles.
    Un usuario puede tener múltiples roles en un negocio.
    """
    userprofileobj = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='user_roles')
    rolesobj = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name='role_users')
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE, related_name='business_user_roles')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'optsio_roles_user'
        unique_together = ('userprofileobj', 'rolesobj', 'businessobj')
        ordering = ['businessobj', 'userprofileobj']
        verbose_name = 'Rol de Usuario'
        verbose_name_plural = 'Roles de Usuarios'

    def __str__(self):
        return f"{self.userprofileobj.username} - {self.rolesobj.name} ({self.businessobj.name})"


class RolesApps(models.Model):
    """
    Relación entre roles y aplicaciones.
    Controla qué aplicaciones puede ver cada rol.
    """
    rolesobj = models.ForeignKey(Roles, on_delete=models.CASCADE, related_name='role_apps')
    appsobj = models.ForeignKey(Apps, on_delete=models.CASCADE, related_name='app_roles')
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE, related_name='business_role_apps')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'optsio_roles_apps'
        unique_together = ('rolesobj', 'appsobj', 'businessobj')
        ordering = ['businessobj', 'rolesobj', 'appsobj']
        verbose_name = 'Rol de Aplicación'
        verbose_name_plural = 'Roles de Aplicaciones'

    def __str__(self):
        return f"{self.rolesobj.name} - {self.appsobj.friendly_name} ({self.businessobj.name})"


# ============================================================================
# SISTEMA DE PLUGINS
# ============================================================================

class Plugin(models.Model):
    """
    Registro de plugins disponibles en el sistema.
    Los plugins se autodescubren al iniciar Django.
    """
    PLUGIN_STATUS_CHOICES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
        ('error', 'Error'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Nombre único del plugin")
    display_name = models.CharField(max_length=200, help_text="Nombre para mostrar")
    description = models.TextField(blank=True, help_text="Descripción del plugin")
    version = models.CharField(max_length=20, default='1.0.0')
    author = models.CharField(max_length=100, blank=True)

    # Configuración
    app_name = models.CharField(max_length=100, help_text="Nombre de la app Django asociada")
    module_path = models.CharField(max_length=200, help_text="Path al módulo del plugin")

    # Estado
    status = models.CharField(max_length=20, choices=PLUGIN_STATUS_CHOICES, default='inactive')
    is_core = models.BooleanField(default=False, help_text="Si es un plugin core (no se puede desactivar)")

    # Dependencias (JSON array de nombres de plugins)
    dependencies = models.JSONField(default=list, blank=True)

    # Metadatos
    icon = models.CharField(max_length=100, default='mdi mdi-puzzle')
    category = models.CharField(max_length=50, default='general')

    # Auditoría
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.display_name} ({self.version})"


class BusinessPlugin(models.Model):
    """
    Relación entre Business y Plugin.
    Permite activar/desactivar plugins por negocio.
    """
    business = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE)

    # Estado por negocio
    enabled = models.BooleanField(default=True)

    # Configuración específica del plugin para este negocio
    config = models.JSONField(default=dict, blank=True)

    # Auditoría
    enabled_at = models.DateTimeField(auto_now_add=True)
    enabled_by = models.CharField(max_length=80, blank=True)

    class Meta:
        unique_together = ('business', 'plugin')
        ordering = ['plugin__category', 'plugin__name']

    def __str__(self):
        return f"{self.business.name} - {self.plugin.display_name}"


class SetupStep(models.Model):
    """
    Pasos de setup ejecutados.
    Permite rastrear qué pasos se han completado.
    """
    STEP_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('error', 'Error'),
        ('skipped', 'Omitido'),
    ]

    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Orden de ejecución
    order = models.IntegerField(default=0)

    # Estado
    status = models.CharField(max_length=20, choices=STEP_STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)

    # Para steps que dependen de un negocio específico
    business = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE, null=True, blank=True)

    # Metadatos de ejecución
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    executed_by = models.CharField(max_length=80, blank=True)

    # Datos adicionales
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['order', 'name']
        unique_together = ('name', 'business')

    def __str__(self):
        return f"{self.display_name} - {self.status}"


class ReferenceDataLoad(models.Model):
    """
    Registro de datos de referencia cargados.
    Evita recargar datos innecesariamente.
    """
    DATA_TYPE_CHOICES = [
        ('geografias', 'Geografías'),
        ('actividades', 'Actividades Económicas'),
        ('medidas', 'Unidades de Medida'),
        ('tipo_contribuyente', 'Tipos de Contribuyente'),
        ('porcentaje_iva', 'Porcentajes IVA'),
        ('metodos_pago', 'Métodos de Pago'),
        ('custom', 'Personalizado'),
    ]

    data_type = models.CharField(max_length=50, choices=DATA_TYPE_CHOICES)
    source_file = models.CharField(max_length=255, blank=True)
    source_hash = models.CharField(max_length=64, blank=True, help_text="Hash del archivo fuente")

    # Estadísticas
    records_loaded = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_skipped = models.IntegerField(default=0)

    # Estado
    loaded_at = models.DateTimeField(auto_now_add=True)
    loaded_by = models.CharField(max_length=80, blank=True)

    # Metadatos
    version = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-loaded_at']

    def __str__(self):
        return f"{self.get_data_type_display()} - {self.loaded_at}"
