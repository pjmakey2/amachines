"""Administracion del Ecommerce: tiendas, temas, colecciones, productos publicados y pedidos."""
import os
import re
from datetime import datetime
from decimal import Decimal

from django.core.files import File
from django.core.files.images import get_image_dimensions
from django.utils.text import slugify

from Ecommerce import handlers
from Ecommerce.models import RE_COLOR, Coleccion, Pedido, ProductoTienda, TemaTienda, Tienda
from OptsIO.io_business import get_active_business, user_label
from OptsIO.io_json import from_json
from Sifen.models import Producto

RE_DECIMAL = re.compile(r'^\d+(\.\d+)?$')
MAX_CSS = 512 * 1024
MAX_IMAGEN = 5 * 1024 * 1024
CATALOGOS = {'Tienda': Tienda, 'TemaTienda': TemaTienda, 'Coleccion': Coleccion, 'ProductoTienda': ProductoTienda}
EN_USO = {
    'Tienda': lambda ids: Pedido.objects.filter(tiendaobj_id__in=ids).exists(),
    'TemaTienda': lambda ids: Tienda.objects.filter(temaobj_id__in=ids).exists(),
    'Coleccion': lambda ids: False,
    'ProductoTienda': lambda ids: ProductoTienda.objects.filter(pk__in=ids, pedidodetalle__isnull=False).exists(),
}


def _dec(value) -> Decimal:
    texto = str(value if value is not None else '').strip()
    return Decimal(texto) if RE_DECIMAL.match(texto) else Decimal(0)


def _bool(value) -> bool:
    return str(value).lower() in ('true', '1', 'on', 'si')


def _slug_unico(model, base: str, filtro: dict, pk=None) -> str:
    base = slugify(base)[:50] or 'item'
    slug, n = base, 1
    while model.objects.filter(slug=slug, **filtro).exclude(pk=pk or 0).exists():
        n += 1
        slug = f"{base}-{n}"
    return slug


def _error_imagen(archivo) -> str:
    if archivo.size > MAX_IMAGEN:
        return f'{archivo.name}: la imagen supera los 5 MB'
    if not get_image_dimensions(archivo)[0]:
        return f'{archivo.name}: no es una imagen válida'
    archivo.seek(0)
    return ''


class MEcommerce:

    def _guardar(self, model, userobj, f, files, campos: dict, imagenes=(), filtro_negocio=None):
        """Crea o actualiza (por id dentro del negocio activo) y adjunta las imagenes ya validadas."""
        bobj = filtro_negocio
        obj = model.objects.filter(pk=f.get('id') or 0, businessobj=bobj).first() if f.get('id') else model(businessobj=bobj)
        if obj is None:
            return None
        for campo, valor in campos.items():
            setattr(obj, campo, valor)
        if obj.pk:
            obj.actualizado_fecha, obj.actualizado_usuario = datetime.now(), user_label(userobj)
        else:
            obj.cargado_fecha, obj.cargado_usuario = datetime.now(), user_label(userobj)
        for campo in imagenes:
            if files.get(campo):
                setattr(obj, campo, File(files.get(campo), name=os.path.basename(files.get(campo).name)))
        obj.save()
        return obj

    def save_tema(self, *args, **kwargs) -> tuple:
        """c_a de TemaTiendaCreateUi: colores validados y CSS propio (solo .css, hasta 512 KB)."""
        userobj, files = kwargs.get('userobj'), kwargs.get('files') or {}
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj or not (f.get('nombre') or '').strip():
            return {'error': 'El nombre del tema es obligatorio'}, args, kwargs
        colores = {c: (f.get(c) or '').strip() for c in ('color_primario', 'color_acento', 'color_fondo', 'color_texto')}
        for campo, valor in colores.items():
            if not RE_COLOR.match(valor):
                return {'error': f'{campo}: use un color hexadecimal (ej: #2563eb)'}, args, kwargs
        css = files.get('css_archivo')
        if css and (not css.name.lower().endswith('.css') or css.size > MAX_CSS):
            return {'error': 'El archivo del tema debe ser .css y pesar menos de 512 KB'}, args, kwargs
        if f.get('layout') not in dict(TemaTienda.LAYOUTS):
            return {'error': 'Layout inválido'}, args, kwargs
        if TemaTienda.objects.filter(businessobj=bobj, nombre=f.get('nombre').strip()).exclude(pk=f.get('id') or 0).exists():
            return {'error': 'Ya existe un tema con ese nombre'}, args, kwargs
        tema = self._guardar(TemaTienda, userobj, f, files, {
            'nombre': f.get('nombre').strip()[:120], 'layout': f.get('layout'), 'fuente': (f.get('fuente') or '').strip()[:120],
            'css_extra': f.get('css_extra') or '', 'activo': _bool(f.get('activo', 'true')), **colores}, imagenes=('css_archivo',), filtro_negocio=bobj)
        if not tema:
            return {'error': 'Tema inexistente'}, args, kwargs
        return {'success': f'Tema "{tema.nombre}" guardado', 'record_id': tema.pk}, args, kwargs

    def save_tienda(self, *args, **kwargs) -> tuple:
        userobj, files = kwargs.get('userobj'), kwargs.get('files') or {}
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj or not (f.get('nombre') or '').strip():
            return {'error': 'El nombre de la tienda es obligatorio'}, args, kwargs
        for campo in ('logo', 'banner'):
            if files.get(campo) and _error_imagen(files.get(campo)):
                return {'error': _error_imagen(files.get(campo))}, args, kwargs
        tema = TemaTienda.objects.filter(pk=f.get('temaobj_id') or 0, businessobj=bobj).first()
        if not _bool(f.get('acepta_transferencia')) and not _bool(f.get('acepta_contra_entrega')):
            return {'error': 'La tienda necesita al menos una forma de pago'}, args, kwargs
        tienda = self._guardar(Tienda, userobj, f, files, {
            'nombre': f.get('nombre').strip()[:120], 'slug': _slug_unico(Tienda, f.get('slug') or f.get('nombre'), {}, f.get('id')),
            'descripcion': (f.get('descripcion') or '').strip()[:300], 'temaobj': tema,
            'banner_titulo': (f.get('banner_titulo') or '').strip()[:120], 'banner_texto': (f.get('banner_texto') or '').strip()[:300],
            'email': (f.get('email') or '').strip()[:120], 'whatsapp': re.sub(r'\D', '', f.get('whatsapp') or '')[:30],
            'costo_envio': _dec(f.get('costo_envio')), 'envio_gratis_desde': _dec(f.get('envio_gratis_desde')),
            'acepta_transferencia': _bool(f.get('acepta_transferencia')), 'datos_transferencia': f.get('datos_transferencia') or '',
            'acepta_contra_entrega': _bool(f.get('acepta_contra_entrega')), 'activa': _bool(f.get('activa', 'true')),
        }, imagenes=('logo', 'banner'), filtro_negocio=bobj)
        if not tienda:
            return {'error': 'Tienda inexistente'}, args, kwargs
        return {'success': f'Tienda guardada. Dirección pública: {tienda.get_url()}', 'record_id': tienda.pk}, args, kwargs

    def save_coleccion(self, *args, **kwargs) -> tuple:
        userobj, files = kwargs.get('userobj'), kwargs.get('files') or {}
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        tienda = Tienda.objects.filter(pk=f.get('tiendaobj_id') or 0, businessobj=bobj).first()
        if not tienda or not (f.get('nombre') or '').strip():
            return {'error': 'Tienda y nombre son obligatorios'}, args, kwargs
        if files.get('imagen') and _error_imagen(files.get('imagen')):
            return {'error': _error_imagen(files.get('imagen'))}, args, kwargs
        col = self._guardar(Coleccion, userobj, f, files, {
            'tiendaobj': tienda, 'nombre': f.get('nombre').strip()[:120],
            'slug': _slug_unico(Coleccion, f.get('slug') or f.get('nombre'), {'tiendaobj': tienda}, f.get('id')),
            'descripcion': (f.get('descripcion') or '').strip()[:300], 'orden': int(_dec(f.get('orden'))), 'activa': _bool(f.get('activa', 'true')),
        }, imagenes=('imagen',), filtro_negocio=bobj)
        if not col:
            return {'error': 'Colección inexistente'}, args, kwargs
        return {'success': f'Colección "{col.nombre}" guardada', 'record_id': col.pk}, args, kwargs

    def save_productotienda(self, *args, **kwargs) -> tuple:
        userobj, files = kwargs.get('userobj'), kwargs.get('files') or {}
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        tienda = Tienda.objects.filter(pk=f.get('tiendaobj_id') or 0, businessobj=bobj).first()
        producto = Producto.objects.filter(pk=f.get('productoobj_id') or 0).first()
        if not tienda or not producto:
            return {'error': 'Tienda y producto son obligatorios'}, args, kwargs
        if ProductoTienda.objects.filter(tiendaobj=tienda, productoobj=producto).exclude(pk=f.get('id') or 0).exists():
            return {'error': 'Ese producto ya está publicado en la tienda'}, args, kwargs
        for campo in ('imagen', 'imagen_2', 'imagen_3'):
            if files.get(campo) and _error_imagen(files.get(campo)):
                return {'error': _error_imagen(files.get(campo))}, args, kwargs
        titulo = (f.get('titulo') or producto.descripcion).strip()[:200]
        pt = self._guardar(ProductoTienda, userobj, f, files, {
            'tiendaobj': tienda, 'productoobj': producto, 'titulo': titulo,
            'coleccionobj': Coleccion.objects.filter(pk=f.get('coleccionobj_id') or 0, tiendaobj=tienda).first(),
            'slug': _slug_unico(ProductoTienda, f.get('slug') or titulo, {'tiendaobj': tienda}, f.get('id')),
            'descripcion_larga': f.get('descripcion_larga') or '', 'precio_online': _dec(f.get('precio_online')),
            'precio_comparacion': _dec(f.get('precio_comparacion')), 'destacado': _bool(f.get('destacado')),
            'publicado': _bool(f.get('publicado', 'true')), 'orden': int(_dec(f.get('orden'))),
        }, imagenes=('imagen', 'imagen_2', 'imagen_3'), filtro_negocio=bobj)
        if not pt:
            return {'error': 'Publicación inexistente'}, args, kwargs
        return {'success': f'"{pt.titulo}" publicado en {tienda.nombre}', 'record_id': pt.pk}, args, kwargs

    def delete_catalogo(self, *args, **kwargs) -> dict:
        q = kwargs.get('qdict', {})
        model = CATALOGOS.get(q.get('model_name'))
        bobj = get_active_business(kwargs.get('userobj'))
        if not model or not bobj:
            return {'msgs': [{'error': 'Solicitud invalida'}]}
        ids = list(model.objects.filter(pk__in=from_json(q.get('ids', '[]')), businessobj=bobj).values_list('pk', flat=True))
        if EN_USO[q.get('model_name')](ids):
            return {'msgs': [{'error': 'El registro ya tiene pedidos o está en uso: desactívelo en lugar de borrarlo'}]}
        n, _ = model.objects.filter(pk__in=ids).delete()
        return {'msgs': [{'success': f'{n} registro(s) borrado(s)'}]}

    def get_pedido(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        pedido = Pedido.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not pedido:
            return {'error': 'Pedido inexistente'}
        return {'success': True, 'detalles': [{'titulo': d.titulo, 'cantidad': float(d.cantidad), 'precio': float(d.precio_unitario),
                                               'total': float(d.total), 'prod_cod': d.productoobj.prod_cod} for d in pedido.detalles.select_related('productoobj')]}

    def set_pago_referencia(self, *args, **kwargs) -> dict:
        """Guarda el comprobante de la transferencia antes de confirmar el pago (viaja al deposito y a la factura)."""
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        n = Pedido.objects.filter(pk=q.get('id') or 0, businessobj=bobj, estado='recibido', anulado=False).update(
            pago_referencia=(q.get('referencia') or '').strip()[:120])
        return {'success': 'Referencia guardada'} if n else {'error': 'Solo se edita la referencia de un pedido recibido'}

    def facturar_pedido(self, *args, **kwargs) -> dict:
        """Reintento manual de la factura de un pedido pagado (el camino normal es el evento por Celery)."""
        userobj = kwargs.get('userobj')
        bobj = get_active_business(userobj)
        pedido = Pedido.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not pedido or pedido.anulado or pedido.estado == 'recibido':
            return {'error': 'Solo se factura un pedido con el pago confirmado'}
        if pedido.documentheader_id:
            return {'info': f'El pedido ya tiene la factura {pedido.documentheader_id}'}
        doc = handlers.facturar(pedido, userobj)
        return {'success': f'Factura {doc.doc_numero} generada', 'documentheader_id': doc.pk}
