from django.contrib import admin
from django.utils.html import format_html
from .models import ShopifyAccessToken, ShopifyProduct, ShopifyOrder, ShopifySyncLog


@admin.register(ShopifyAccessToken)
class ShopifyAccessTokenAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'token_status', 'expires_at', 'is_active', 'updated_at']
    list_filter = ['is_active', 'expires_at']
    search_fields = ['store_name']
    readonly_fields = ['access_token', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Tienda', {
            'fields': ('store_name', 'client_id', 'client_secret', 'is_active')
        }),
        ('Token de Acceso', {
            'fields': ('access_token', 'scopes', 'expires_at')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def token_status(self, obj):
        if obj.is_valid():
            color = 'green'
            text = '✓ Válido'
        elif obj.is_expiring_soon():
            color = 'orange'
            text = '⚠ Expirando pronto'
        else:
            color = 'red'
            text = '✗ Expirado'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    token_status.short_description = 'Estado del Token'


@admin.register(ShopifyProduct)
class ShopifyProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'shopify_id', 'price', 'inventory_quantity', 'sku', 'status', 'synced_at']
    list_filter = ['status', 'vendor', 'product_type']
    search_fields = ['title', 'sku', 'barcode', 'shopify_id']
    readonly_fields = ['shopify_id', 'handle', 'created_at_shopify', 'updated_at_shopify', 'synced_at', 'created_at']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('shopify_id', 'title', 'description', 'vendor', 'product_type', 'status')
        }),
        ('Precio e Inventario', {
            'fields': ('price', 'compare_at_price', 'inventory_quantity')
        }),
        ('Identificadores', {
            'fields': ('sku', 'barcode', 'handle')
        }),
        ('Imagen', {
            'fields': ('image_url',)
        }),
        ('Fechas', {
            'fields': ('published_at', 'created_at_shopify', 'updated_at_shopify', 'synced_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['sync_selected_products']
    
    def sync_selected_products(self, request, queryset):
        from .managers import ProductManager
        manager = ProductManager()
        
        count = 0
        for product in queryset:
            try:
                response = manager.client.get_product(product.shopify_id)
                manager._sync_product(response['product'])
                count += 1
            except Exception as e:
                self.message_user(request, f'Error sincronizando {product.title}: {str(e)}', level='error')
        
        self.message_user(request, f'{count} producto(s) sincronizado(s) exitosamente.')
    
    sync_selected_products.short_description = "Sincronizar productos seleccionados desde Shopify"


@admin.register(ShopifyOrder)
class ShopifyOrderAdmin(admin.ModelAdmin):
    list_display = ['name', 'shopify_id', 'customer_email', 'total_price', 'currency', 'status_display', 'created_at_shopify']
    list_filter = ['financial_status', 'fulfillment_status', 'created_at_shopify']
    search_fields = ['name', 'order_number', 'customer_email', 'customer_phone', 'shopify_id']
    readonly_fields = ['shopify_id', 'order_number', 'name', 'created_at_shopify', 'updated_at_shopify', 'processed_at', 'synced_at', 'created_at']
    
    fieldsets = (
        ('Información de la Orden', {
            'fields': ('shopify_id', 'order_number', 'name')
        }),
        ('Cliente', {
            'fields': ('customer_email', 'customer_phone', 'customer_first_name', 'customer_last_name')
        }),
        ('Montos', {
            'fields': ('total_price', 'subtotal_price', 'total_tax', 'total_discounts', 'currency')
        }),
        ('Estados', {
            'fields': ('financial_status', 'fulfillment_status', 'cancelled_at', 'cancel_reason')
        }),
        ('Notas y Tags', {
            'fields': ('note', 'tags'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at_shopify', 'updated_at_shopify', 'processed_at', 'synced_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'paid': 'green',
            'pending': 'orange',
            'partially_paid': 'blue',
            'refunded': 'red',
            'voided': 'red',
        }
        color = colors.get(obj.financial_status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_financial_status_display()
        )
    status_display.short_description = 'Estado Financiero'


@admin.register(ShopifySyncLog)
class ShopifySyncLogAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status_display', 'items_processed', 'items_created', 'items_updated', 'items_failed', 'duration', 'started_at']
    list_filter = ['sync_type', 'status', 'started_at']
    readonly_fields = ['sync_type', 'status', 'items_processed', 'items_created', 'items_updated', 'items_failed', 'error_message', 'started_at', 'completed_at', 'duration_seconds']
    
    fieldsets = (
        ('Tipo de Sincronización', {
            'fields': ('sync_type', 'status')
        }),
        ('Estadísticas', {
            'fields': ('items_processed', 'items_created', 'items_updated', 'items_failed')
        }),
        ('Fechas', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        colors = {
            'success': 'green',
            'error': 'red',
            'partial': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Estado'
    
    def duration(self, obj):
        if obj.duration_seconds:
            return f"{obj.duration_seconds:.2f}s"
        return "-"
    duration.short_description = 'Duración'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
