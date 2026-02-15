from django.db import models
from django.utils import timezone
from datetime import timedelta


class ShopifyAccessToken(models.Model):
    """
    Almacena los access tokens de Shopify con su fecha de expiración
    """
    store_name = models.CharField(max_length=255, unique=True, help_text="Nombre de la tienda (ej: altamachines)")
    client_id = models.CharField(max_length=255, help_text="Client ID de la app")
    client_secret = models.CharField(max_length=255, help_text="Client Secret de la app")
    access_token = models.CharField(max_length=255, help_text="Access Token actual")
    scopes = models.TextField(blank=True, help_text="Scopes otorgados")
    expires_at = models.DateTimeField(help_text="Fecha y hora de expiración")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, help_text="Si esta tienda está activa")

    class Meta:
        verbose_name = "Shopify Access Token"
        verbose_name_plural = "Shopify Access Tokens"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.store_name} - {'Válido' if self.is_valid() else 'Expirado'}"

    def is_valid(self):
        """Verifica si el token aún es válido"""
        return self.expires_at > timezone.now()

    def is_expiring_soon(self, hours=2):
        """Verifica si el token expirará pronto"""
        threshold = timezone.now() + timedelta(hours=hours)
        return self.expires_at <= threshold

    def get_token_or_refresh(self):
        """Obtiene el token actual o lo renueva si ha expirado"""
        if not self.is_valid():
            from .services import ShopifyTokenService
            service = ShopifyTokenService()
            return service.refresh_token(self)
        return self.access_token


class ShopifyProduct(models.Model):
    """
    Almacena productos sincronizados con Shopify
    """
    shopify_id = models.BigIntegerField(unique=True, help_text="ID del producto en Shopify")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    product_type = models.CharField(max_length=255, blank=True)
    handle = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='active', help_text="active, draft, archived")
    
    # Precio
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventario
    inventory_quantity = models.IntegerField(default=0)
    sku = models.CharField(max_length=255, blank=True)
    barcode = models.CharField(max_length=255, blank=True)
    
    # Imágenes
    image_url = models.URLField(max_length=500, blank=True)
    
    # Fechas
    published_at = models.DateTimeField(null=True, blank=True)
    created_at_shopify = models.DateTimeField(null=True, blank=True)
    updated_at_shopify = models.DateTimeField(null=True, blank=True)
    
    # Control local
    synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto de Shopify"
        verbose_name_plural = "Productos de Shopify"
        ordering = ['-updated_at_shopify']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
            models.Index(fields=['handle']),
        ]

    def __str__(self):
        return f"{self.title} (#{self.shopify_id})"


class ShopifyOrder(models.Model):
    """
    Almacena órdenes sincronizadas con Shopify
    """
    FINANCIAL_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('authorized', 'Autorizado'),
        ('partially_paid', 'Parcialmente Pagado'),
        ('paid', 'Pagado'),
        ('partially_refunded', 'Parcialmente Reembolsado'),
        ('refunded', 'Reembolsado'),
        ('voided', 'Anulado'),
    ]

    FULFILLMENT_STATUS_CHOICES = [
        (None, 'Sin Enviar'),
        ('fulfilled', 'Enviado'),
        ('partial', 'Parcial'),
        ('restocked', 'Reabastecido'),
    ]

    shopify_id = models.BigIntegerField(unique=True, help_text="ID de la orden en Shopify")
    order_number = models.IntegerField(help_text="Número de orden visible")
    name = models.CharField(max_length=50, help_text="Nombre de la orden (ej: #1001)")
    
    # Cliente
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=50, blank=True)
    customer_first_name = models.CharField(max_length=255, blank=True)
    customer_last_name = models.CharField(max_length=255, blank=True)
    customer_tags = models.CharField(max_length=500, blank=True, help_text="Tags del cliente (contiene RUC)")

    # Montos
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_discounts = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='PYG')
    
    # Estados
    financial_status = models.CharField(max_length=50, choices=FINANCIAL_STATUS_CHOICES, default='pending')
    fulfillment_status = models.CharField(max_length=50, choices=FULFILLMENT_STATUS_CHOICES, null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    
    # Datos adicionales
    note = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)
    
    # Fechas
    created_at_shopify = models.DateTimeField()
    updated_at_shopify = models.DateTimeField()
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Control local
    synced_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Orden de Shopify"
        verbose_name_plural = "Órdenes de Shopify"
        ordering = ['-created_at_shopify']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['order_number']),
            models.Index(fields=['financial_status']),
            models.Index(fields=['customer_email']),
        ]

    def __str__(self):
        return f"Orden {self.name} - {self.get_financial_status_display()}"

    @property
    def is_paid(self):
        """Verifica si la orden está pagada"""
        return self.financial_status in ['paid', 'partially_refunded', 'refunded']

    @property
    def is_pending(self):
        """Verifica si la orden está pendiente de pago"""
        return self.financial_status == 'pending'

    @property
    def is_cancelled(self):
        """Verifica si la orden fue cancelada"""
        return self.cancelled_at is not None


class ShopifyPayment(models.Model):
    """
    Almacena órdenes PAGADAS de Shopify para su conversión a facturas SIFEN.
    Este modelo sirve como punto intermedio entre Shopify y DocumentHeader
    para tener mejor control de duplicados y consistencia de datos.
    """
    CONVERSION_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('converted', 'Convertido'),
        ('error', 'Error'),
        ('skipped', 'Omitido'),
    ]

    # Identificadores Shopify
    shopify_order_id = models.BigIntegerField(unique=True, help_text="ID de la orden en Shopify")
    order_number = models.IntegerField(help_text="Número de orden visible (#1001)")
    order_name = models.CharField(max_length=50, help_text="Nombre de la orden (ej: #1001)")

    # Cliente (puede ser innominado si no hay datos)
    customer_email = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=50, blank=True, null=True)
    customer_first_name = models.CharField(max_length=255, blank=True, null=True)
    customer_last_name = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=500, blank=True, null=True, help_text="Nombre completo del cliente")
    customer_tags = models.CharField(max_length=500, blank=True, help_text="Tags del cliente (contiene RUC)")
    is_innominado = models.BooleanField(default=False, help_text="True si el cliente es innominado (sin datos)")

    # Montos
    total_price = models.DecimalField(max_digits=15, decimal_places=2, help_text="Total de la orden")
    subtotal_price = models.DecimalField(max_digits=15, decimal_places=2, help_text="Subtotal sin impuestos")
    total_tax = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_discounts = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_shipping = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Costo de envío")
    currency = models.CharField(max_length=3, default='PYG')

    # Información de pago
    payment_gateway = models.CharField(max_length=255, blank=True, help_text="Gateway de pago usado")
    payment_method = models.CharField(max_length=100, default='cash', help_text="Método de pago (cash, card, etc)")
    financial_status = models.CharField(max_length=50, default='paid')

    # Líneas de la orden (JSON)
    line_items = models.JSONField(default=list, help_text="Productos de la orden")

    # Direcciones (JSON)
    shipping_address = models.JSONField(default=dict, blank=True)
    billing_address = models.JSONField(default=dict, blank=True)

    # Notas y etiquetas
    note = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)

    # Fechas de Shopify
    order_created_at = models.DateTimeField(help_text="Fecha de creación en Shopify")
    order_processed_at = models.DateTimeField(null=True, blank=True)

    # Estado de conversión a SIFEN
    conversion_status = models.CharField(
        max_length=20,
        choices=CONVERSION_STATUS_CHOICES,
        default='pending'
    )
    conversion_error = models.TextField(blank=True, help_text="Mensaje de error si falló la conversión")
    document_header = models.ForeignKey(
        'Sifen.DocumentHeader',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shopify_payments',
        help_text='Factura SIFEN generada'
    )

    # Control local
    synced_at = models.DateTimeField(auto_now_add=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pago de Shopify"
        verbose_name_plural = "Pagos de Shopify"
        ordering = ['-order_created_at']
        indexes = [
            models.Index(fields=['shopify_order_id']),
            models.Index(fields=['order_number']),
            models.Index(fields=['conversion_status']),
            models.Index(fields=['customer_email']),
        ]

    def __str__(self):
        status = "Innominado" if self.is_innominado else self.customer_name or self.customer_email or "Sin cliente"
        return f"{self.order_name} - {status} - {self.get_conversion_status_display()}"

    @property
    def customer_full_name(self):
        """Retorna el nombre completo del cliente o 'Innominado'"""
        if self.is_innominado:
            return "Innominado"
        if self.customer_name:
            return self.customer_name
        parts = [self.customer_first_name, self.customer_last_name]
        name = " ".join(filter(None, parts)).strip()
        return name if name else "Innominado"

    @property
    def is_converted(self):
        #return self.conversion_status == 'converted' and self.document_header is not None
        return self.conversion_status == 'converted'


class ShopifyCustomer(models.Model):
    """
    Almacena clientes sincronizados de Shopify con TODOS sus datos.
    """
    STATE_CHOICES = [
        ('disabled', 'Deshabilitado'),
        ('invited', 'Invitado'),
        ('enabled', 'Habilitado'),
        ('declined', 'Rechazado'),
    ]

    # Identificadores
    shopify_id = models.BigIntegerField(unique=True, help_text="ID del cliente en Shopify")
    admin_graphql_api_id = models.CharField(max_length=255, blank=True, help_text="ID de GraphQL Admin API")

    # Datos básicos
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True, help_text="Email del cliente")
    phone = models.CharField(max_length=50, blank=True, null=True)

    # Estado y verificación
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default='disabled')
    verified_email = models.BooleanField(default=False, help_text="Si el email fue verificado")

    # Estadísticas de órdenes
    orders_count = models.IntegerField(default=0, help_text="Número de órdenes realizadas")
    total_spent = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Total gastado")
    currency = models.CharField(max_length=3, default='PYG', help_text="Moneda del cliente")

    # Última orden
    last_order_id = models.BigIntegerField(null=True, blank=True, help_text="ID de la última orden")
    last_order_name = models.CharField(max_length=50, blank=True, help_text="Nombre de la última orden (ej: #1025)")

    # Notas y etiquetas
    note = models.TextField(blank=True, null=True, help_text="Notas del cliente")
    tags = models.CharField(max_length=500, blank=True, help_text="Etiquetas del cliente")

    # Impuestos
    tax_exempt = models.BooleanField(default=False, help_text="Si está exento de impuestos")
    tax_exemptions = models.JSONField(default=list, blank=True, help_text="Lista de exenciones de impuestos")

    # Marketing - Email
    email_marketing_consent_state = models.CharField(max_length=50, blank=True, help_text="Estado de consentimiento de email marketing")
    email_marketing_consent_opt_in_level = models.CharField(max_length=50, blank=True, help_text="Nivel de opt-in de email")
    email_marketing_consent_updated_at = models.DateTimeField(null=True, blank=True)

    # Marketing - SMS
    sms_marketing_consent_state = models.CharField(max_length=50, blank=True, help_text="Estado de consentimiento de SMS marketing")
    sms_marketing_consent_opt_in_level = models.CharField(max_length=50, blank=True, help_text="Nivel de opt-in de SMS")
    sms_marketing_consent_updated_at = models.DateTimeField(null=True, blank=True)
    sms_marketing_consent_source = models.CharField(max_length=100, blank=True, help_text="Fuente del consentimiento SMS")

    # Multipass
    multipass_identifier = models.CharField(max_length=255, blank=True, null=True, help_text="Identificador de Multipass")

    # Direcciones (JSON completo)
    addresses = models.JSONField(default=list, blank=True, help_text="Lista de todas las direcciones")
    default_address = models.JSONField(default=dict, blank=True, help_text="Dirección por defecto")

    # Datos de la dirección por defecto (desnormalizados para búsqueda)
    default_address_id = models.BigIntegerField(null=True, blank=True)
    default_address_first_name = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_last_name = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_company = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_address1 = models.CharField(max_length=500, blank=True, null=True, default='')
    default_address_address2 = models.CharField(max_length=500, blank=True, null=True, default='')
    default_address_city = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_province = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_province_code = models.CharField(max_length=10, blank=True, null=True, default='')
    default_address_country = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_country_code = models.CharField(max_length=10, blank=True, null=True, default='')
    default_address_country_name = models.CharField(max_length=255, blank=True, null=True, default='')
    default_address_zip = models.CharField(max_length=50, blank=True, null=True, default='')
    default_address_phone = models.CharField(max_length=50, blank=True, null=True, default='')

    # Fechas de Shopify
    created_at_shopify = models.DateTimeField(null=True, blank=True, help_text="Fecha de creación en Shopify")
    updated_at_shopify = models.DateTimeField(null=True, blank=True, help_text="Fecha de actualización en Shopify")

    # Control local
    synced_at = models.DateTimeField(auto_now=True, help_text="Última sincronización")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente de Shopify"
        verbose_name_plural = "Clientes de Shopify"
        ordering = ['-updated_at_shopify']
        indexes = [
            models.Index(fields=['shopify_id']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['state']),
            models.Index(fields=['last_order_id']),
        ]

    def __str__(self):
        name = self.full_name or self.email or f"Cliente #{self.shopify_id}"
        return f"{name} ({self.orders_count} órdenes)"

    @property
    def full_name(self):
        """Retorna el nombre completo del cliente"""
        parts = [self.first_name, self.last_name]
        return " ".join(filter(None, parts)).strip() or None

    @property
    def has_orders(self):
        """Verifica si el cliente tiene órdenes"""
        return self.orders_count > 0

    @property
    def full_address(self):
        """Retorna la dirección completa formateada"""
        if not self.default_address:
            return None
        parts = [
            self.default_address_address1,
            self.default_address_address2,
            self.default_address_city,
            self.default_address_province,
            self.default_address_country,
            self.default_address_zip
        ]
        return ", ".join(filter(None, parts)) or None


class ShopifySyncLog(models.Model):
    """
    Log de sincronizaciones con Shopify
    """
    SYNC_TYPE_CHOICES = [
        ('products', 'Productos'),
        ('orders', 'Órdenes'),
        ('payments', 'Pagos'),
        ('customers', 'Clientes'),
        ('token_refresh', 'Renovación de Token'),
    ]

    STATUS_CHOICES = [
        ('success', 'Exitoso'),
        ('error', 'Error'),
        ('partial', 'Parcial'),
    ]

    sync_type = models.CharField(max_length=50, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    items_processed = models.IntegerField(default=0)
    items_created = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Log de Sincronización"
        verbose_name_plural = "Logs de Sincronización"
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.get_status_display()} ({self.started_at})"

    def complete(self, status='success', error_message=''):
        """Marca la sincronización como completada"""
        self.completed_at = timezone.now()
        self.status = status
        self.error_message = error_message
        if self.started_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = delta.total_seconds()
        self.save()


# Importar modelo de SIFEN para relación
try:
    from Sifen.models import DocumentHeader
    SIFEN_AVAILABLE = True
except ImportError:
    SIFEN_AVAILABLE = False


if SIFEN_AVAILABLE:
    # Agregar campo a ShopifyOrder para vincular con DocumentHeader
    ShopifyOrder.add_to_class(
        'document_header',
        models.ForeignKey(
            'Sifen.DocumentHeader',
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='shopify_orders',
            help_text='Factura SIFEN generada desde esta orden'
        )
    )
    
    ShopifyOrder.add_to_class(
        'converted_to_invoice',
        models.BooleanField(
            default=False,
            help_text='Si la orden ya fue convertida a factura SIFEN'
        )
    )
