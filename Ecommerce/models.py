import re
import uuid
from datetime import datetime
from decimal import Decimal

from django.db import models

from Almacen.models import despachar, liberar_reservas, stock_disponible, stock_fisico_vendible
from Ecommerce.presets import PRESET_CHOICES, PRESET_DEFAULT, get_preset
from OptsIO.io_money import precision_monetaria
from OptsIO.workflow import WorkflowMixin

CCT = {'max_digits': 19, 'decimal_places': 6}
RE_COLOR = re.compile(r'^#[0-9a-fA-F]{3,8}$')


class EcomTrack(models.Model):
    cargado_fecha = models.DateTimeField(null=True, blank=True)
    cargado_usuario = models.CharField(max_length=120, null=True, blank=True)
    actualizado_fecha = models.DateTimeField(null=True, blank=True)
    actualizado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        abstract = True


class TemaTienda(EcomTrack):
    """
    Apariencia de una tienda: un preset (CSS listo por rubro) + colores propios opcionales + CSS propio.
    Orden de carga: tienda.css (base) -> temas/<preset>.css -> variables de color -> CSS del tema.
    """
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    preset = models.CharField(max_length=20, choices=PRESET_CHOICES, default=PRESET_DEFAULT)
    # False = colores y tipografia del preset; True = los de abajo
    colores_propios = models.BooleanField(default=False)
    color_primario = models.CharField(max_length=9, default='#111827')
    color_acento = models.CharField(max_length=9, default='#2563eb')
    color_fondo = models.CharField(max_length=9, default='#ffffff')
    color_texto = models.CharField(max_length=9, default='#1f2937')
    fuente = models.CharField(max_length=120, blank=True, default='', help_text='Familia tipográfica CSS, ej: "Inter", sans-serif')
    css_archivo = models.FileField(upload_to='ecommerce/temas', max_length=300, null=True, blank=True)
    css_extra = models.TextField(blank=True, default='')
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('businessobj', 'nombre')
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def get_preset(self) -> dict:
        return get_preset(self.preset)

    def get_preset_nombre(self):
        return self.get_preset()['nombre']

    def get_css_variables(self) -> str:
        """Variables CSS del tema. Solo salen valores validados: van dentro de un <style> publico."""
        if not self.colores_propios:
            return ''
        colores = {'--t-primario': self.color_primario, '--t-acento': self.color_acento,
                   '--t-fondo': self.color_fondo, '--t-texto': self.color_texto}
        partes = [f"{k}: {v};" for k, v in colores.items() if RE_COLOR.match(v or '')]
        fuente = re.sub(r'[^A-Za-z0-9 ,"\'\-]', '', self.fuente or '')
        if fuente:
            partes.append(f"--t-fuente: {fuente};")
        return ' '.join(partes)

    def get_css_extra(self) -> str:
        return (self.css_extra or '').replace('<', '')


class Tienda(EcomTrack):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=60, unique=True, help_text='Dirección pública: /tienda/<slug>/')
    descripcion = models.CharField(max_length=300, blank=True, default='')
    temaobj = models.ForeignKey(TemaTienda, on_delete=models.SET_NULL, null=True, blank=True)
    logo = models.ImageField(upload_to='ecommerce/tiendas', max_length=300, null=True, blank=True)
    banner = models.ImageField(upload_to='ecommerce/tiendas', max_length=300, null=True, blank=True)
    banner_titulo = models.CharField(max_length=120, blank=True, default='')
    banner_texto = models.CharField(max_length=300, blank=True, default='')
    banner_cta_texto = models.CharField(max_length=40, blank=True, default='', help_text='Texto del botón de la portada, ej: Ver ofertas')
    banner_cta_url = models.CharField(max_length=300, blank=True, default='', help_text='Destino del botón: /tienda/<slug>/coleccion/<slug>/ o una URL')
    anuncio_texto = models.CharField(max_length=160, blank=True, default='', help_text='Barra superior, ej: Envío gratis desde Gs 300.000')
    anuncio_url = models.CharField(max_length=300, blank=True, default='')
    email = models.CharField(max_length=120, blank=True, default='')
    whatsapp = models.CharField(max_length=30, blank=True, default='')
    moneda = models.CharField(max_length=4, default='PYG')
    costo_envio = models.DecimalField(**CCT, default=0)
    envio_gratis_desde = models.DecimalField(**CCT, default=0)
    acepta_transferencia = models.BooleanField(default=True)
    datos_transferencia = models.TextField(blank=True, default='', help_text='Banco, cuenta, titular y RUC que ve el cliente al pagar')
    acepta_contra_entrega = models.BooleanField(default=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def get_url(self):
        return f"/tienda/{self.slug}/"

    @precision_monetaria
    def calcular_envio(self, subtotal) -> Decimal:
        if self.envio_gratis_desde and subtotal >= self.envio_gratis_desde:
            return Decimal(0)
        return self.costo_envio


class Coleccion(EcomTrack):
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    tiendaobj = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80)
    descripcion = models.CharField(max_length=300, blank=True, default='')
    imagen = models.ImageField(upload_to='ecommerce/colecciones', max_length=300, null=True, blank=True)
    icono = models.CharField(max_length=60, blank=True, default='', help_text='Ícono Bootstrap Icons para el menú lateral, ej: bi-basket')
    orden = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        unique_together = ('tiendaobj', 'slug')
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre

    def get_descripcion(self):
        return f"{self.tiendaobj.nombre} / {self.nombre}"


class ProductoTienda(EcomTrack):
    """Publicacion de un producto del maestro (Sifen.Producto) en una tienda."""
    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    tiendaobj = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    coleccionobj = models.ForeignKey(Coleccion, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(max_length=120)
    descripcion_larga = models.TextField(blank=True, default='')
    # 0 = usa el precio del maestro de productos
    precio_online = models.DecimalField(**CCT, default=0)
    precio_comparacion = models.DecimalField(**CCT, default=0, help_text='Precio tachado (antes)')
    imagen = models.ImageField(upload_to='ecommerce/productos', max_length=300, null=True, blank=True)
    imagen_2 = models.ImageField(upload_to='ecommerce/productos', max_length=300, null=True, blank=True)
    imagen_3 = models.ImageField(upload_to='ecommerce/productos', max_length=300, null=True, blank=True)
    etiqueta = models.CharField(max_length=30, blank=True, default='', help_text='Badge sobre la foto, ej: Nuevo, Más vendido')
    destacado = models.BooleanField(default=False)
    publicado = models.BooleanField(default=True)
    orden = models.IntegerField(default=0)

    class Meta:
        unique_together = [('tiendaobj', 'slug'), ('tiendaobj', 'productoobj')]
        ordering = ['orden', 'titulo']

    def __str__(self):
        return self.titulo

    @property
    def precio(self) -> Decimal:
        return self.precio_online if self.precio_online > 0 else self.productoobj.precio

    def get_precio(self):
        return float(self.precio)

    def get_disponible(self):
        return float(stock_disponible(self.businessobj, self.productoobj))

    def get_imagenes(self) -> list:
        urls = [f.url for f in (self.imagen, self.imagen_2, self.imagen_3) if f]
        if not urls and self.productoobj.photo:
            urls = [self.productoobj.photo.url]
        return urls

    def get_imagen(self) -> str:
        urls = self.get_imagenes()
        return urls[0] if urls else ''

    def get_descuento_pct(self) -> int:
        """Porcentaje de rebaja respecto del precio tachado (0 si no hay)."""
        if self.precio_comparacion and self.precio_comparacion > self.precio:
            return int(round((1 - self.precio / self.precio_comparacion) * 100))
        return 0


class PromoTienda(EcomTrack):
    """Bloques promocionales de la portada: tarjetas laterales del hero o carrusel de ofertas."""
    POSICIONES = [('lateral', 'Tarjeta lateral de la portada'), ('carrusel', 'Carrusel de promociones')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    tiendaobj = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    posicion = models.CharField(max_length=20, choices=POSICIONES, default='lateral')
    etiqueta = models.CharField(max_length=40, blank=True, default='', help_text='Texto chico arriba, ej: Novedades')
    titulo = models.CharField(max_length=80)
    subtitulo = models.CharField(max_length=120, blank=True, default='', help_text='Ej: 20% OFF')
    imagen = models.ImageField(upload_to='ecommerce/promos', max_length=300, null=True, blank=True)
    color_fondo = models.CharField(max_length=9, blank=True, default='', help_text='Fondo de la tarjeta (hex); vacío = del tema')
    url = models.CharField(max_length=300, blank=True, default='')
    orden = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['posicion', 'orden', 'id']

    def __str__(self):
        return self.titulo

    def get_color_fondo(self) -> str:
        return self.color_fondo if RE_COLOR.match(self.color_fondo or '') else ''


class Pedido(WorkflowMixin, EcomTrack):
    """
    Pedido online. recibido (stock reservado) -> pagado (se factura) -> preparado -> despachado (sale el stock).
    Se anula solo antes del pago; despues corresponde nota de credito y devolucion.
    """
    WORKFLOW_STATES = ['recibido', 'pagado', 'preparado', 'despachado']
    WORKFLOW_EVENT = 'ecommerce.pedido'
    METODOS = [('transferencia', 'Transferencia bancaria'), ('contra_entrega', 'Pago contra entrega')]

    businessobj = models.ForeignKey('Sifen.Business', on_delete=models.CASCADE)
    tiendaobj = models.ForeignKey(Tienda, on_delete=models.PROTECT)
    numero = models.BigIntegerField(default=0)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    fecha = models.DateTimeField(default=datetime.now, db_index=True)
    estado = models.CharField(max_length=30, default='recibido', db_index=True)
    cliente_nombre = models.CharField(max_length=200)
    cliente_documento = models.CharField(max_length=30, blank=True, default='', help_text='RUC o CI para la factura')
    cliente_email = models.CharField(max_length=120)
    cliente_telefono = models.CharField(max_length=40)
    direccion = models.CharField(max_length=300)
    ciudad = models.CharField(max_length=120, blank=True, default='')
    notas = models.CharField(max_length=300, blank=True, default='')
    metodo_pago = models.CharField(max_length=20, choices=METODOS)
    pago_referencia = models.CharField(max_length=120, blank=True, default='')
    moneda = models.CharField(max_length=4, default='PYG')
    subtotal = models.DecimalField(**CCT, default=0)
    costo_envio = models.DecimalField(**CCT, default=0)
    total = models.DecimalField(**CCT, default=0)
    documentheader_id = models.BigIntegerField(null=True, blank=True)
    pagado_fecha = models.DateTimeField(null=True, blank=True)
    pagado_usuario = models.CharField(max_length=120, null=True, blank=True)
    despachado_fecha = models.DateTimeField(null=True, blank=True)
    despachado_usuario = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        permissions = [('pedido_pagado', 'Confirmar pago de pedido'), ('pedido_preparado', 'Marcar pedido preparado'),
                       ('pedido_despachado', 'Despachar pedido'), ('pedido_anulado', 'Anular pedido')]
        constraints = [models.UniqueConstraint(fields=['businessobj', 'numero'], name='ecommerce_pedido_numero_unico')]

    def __str__(self):
        return f"Pedido {self.numero} - {self.cliente_nombre}"

    def get_numero_display(self):
        return str(self.numero).zfill(6)

    def get_tienda(self):
        return self.tiendaobj.nombre

    def get_url(self):
        return f"/tienda/{self.tiendaobj.slug}/pedido/{self.token}/"

    def get_workflow_payload(self):
        return {'numero': self.numero, 'fecha': self.fecha.strftime('%Y-%m-%d'), 'cliente': self.cliente_nombre,
                'metodo_pago': self.metodo_pago, 'moneda': self.moneda, 'total': str(self.total),
                'referencia': self.pago_referencia, 'documentheader_id': self.documentheader_id}

    def workflow_validar(self, estado):
        if estado == 'anulado' and self.estado != 'recibido':
            return "El pedido ya fue pagado/facturado: corresponde nota de crédito y devolución, no anulación"
        if estado == 'despachado':
            for d in self.detalles.select_related('productoobj'):
                if stock_fisico_vendible(self.businessobj, d.productoobj) < d.cantidad:
                    return f"Sin stock físico para despachar {d.titulo}"
        return ''

    def workflow_on_enter(self, estado, userobj):
        if estado == 'despachado':
            for d in self.detalles.select_related('productoobj'):
                despachar(self.businessobj, d.productoobj, d.cantidad, self, f"Pedido online {self.get_numero_display()}", userobj)
        if estado == 'anulado':
            liberar_reservas(self)


class PedidoDetalle(models.Model):
    pedidoobj = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    productotiendaobj = models.ForeignKey(ProductoTienda, on_delete=models.PROTECT)
    productoobj = models.ForeignKey('Sifen.Producto', on_delete=models.PROTECT)
    titulo = models.CharField(max_length=200)
    precio_unitario = models.DecimalField(**CCT)
    cantidad = models.DecimalField(**CCT)
    total = models.DecimalField(**CCT)
