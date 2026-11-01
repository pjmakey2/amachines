"""Tienda publica: /tienda/<slug>/. Sin login; el carrito vive en la sesion."""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from Ecommerce.carrito import Carrito, crear_pedido, validar_checkout
from Ecommerce.models import Coleccion, Pedido, ProductoTienda, PromoTienda, Tienda
from Ecommerce.presets import PRESETS, get_preset

POR_PAGINA = 24


def _contexto(request, slug):
    tienda = get_object_or_404(Tienda.objects.select_related('temaobj', 'businessobj'), slug=slug, activa=True)
    carrito = Carrito(request, tienda)
    tema = tienda.temaobj if tienda.temaobj_id and tienda.temaobj.activo else None
    clave = tema.preset if tema else 'clasico'
    # ?preset=<clave>: vista previa de otro estilo, solo para usuarios del sistema (no cambia nada)
    if request.user.is_authenticated and request.GET.get('preset') in PRESETS:
        clave = request.GET['preset']
    preset = get_preset(clave)
    colecciones = (Coleccion.objects.filter(tiendaobj=tienda, activa=True)
                   .annotate(cantidad=Count('productotienda', filter=Q(productotienda__publicado=True, productotienda__productoobj__activo=True))))
    return tienda, carrito, {
        'tienda': tienda, 'tema': tema, 'preset': preset, 'preset_clave': clave, 'carrito_cantidad': carrito.cantidad_total,
        'colecciones': colecciones, 'total_publicados': _publicados(tienda).count(),
    }


def _publicados(tienda):
    return ProductoTienda.objects.filter(tiendaobj=tienda, publicado=True, productoobj__activo=True).select_related('productoobj')


def home(request, slug):
    tienda, _, ctx = _contexto(request, slug)
    q = (request.GET.get('q') or '').strip()[:80]
    productos = _publicados(tienda)
    if q:
        productos = productos.filter(Q(titulo__icontains=q) | Q(descripcion_larga__icontains=q))
    promos = PromoTienda.objects.filter(tiendaobj=tienda, activa=True)
    ctx.update({'q': q, 'destacados': [] if q else productos.filter(destacado=True)[:8],
                'pagina': Paginator(productos, POR_PAGINA).get_page(request.GET.get('p')),
                'promos_laterales': [] if q else promos.filter(posicion='lateral')[:2],
                'promos_carrusel': [] if q else promos.filter(posicion='carrusel')[:8]})
    return render(request, 'Ecommerce/tienda/home.html', ctx)


def coleccion(request, slug, coleccion_slug):
    tienda, _, ctx = _contexto(request, slug)
    col = get_object_or_404(Coleccion, tiendaobj=tienda, slug=coleccion_slug, activa=True)
    ctx.update({'coleccion': col, 'pagina': Paginator(_publicados(tienda).filter(coleccionobj=col), POR_PAGINA).get_page(request.GET.get('p'))})
    return render(request, 'Ecommerce/tienda/coleccion.html', ctx)


def producto(request, slug, producto_slug):
    tienda, _, ctx = _contexto(request, slug)
    pt = get_object_or_404(_publicados(tienda), slug=producto_slug)
    ctx.update({'pt': pt, 'disponible': pt.get_disponible(),
                'relacionados': _publicados(tienda).filter(coleccionobj=pt.coleccionobj).exclude(pk=pt.pk)[:4] if pt.coleccionobj_id else []})
    return render(request, 'Ecommerce/tienda/producto.html', ctx)


@require_POST
def carrito_agregar(request, slug):
    tienda, carrito, _ = _contexto(request, slug)
    pt = get_object_or_404(_publicados(tienda), pk=request.POST.get('producto_id') or 0)
    cantidad = request.POST.get('cantidad') or '1'
    carrito.agregar(pt.pk, int(cantidad) if cantidad.isdigit() else 1)
    return redirect('ecommerce_carrito', slug=slug)


@require_POST
def carrito_actualizar(request, slug):
    _, carrito, _ = _contexto(request, slug)
    for clave, valor in request.POST.items():
        if clave.startswith('cantidad_') and clave[9:].isdigit() and valor.isdigit():
            carrito.set(clave[9:], int(valor))
    return redirect('ecommerce_carrito', slug=slug)


def carrito_ver(request, slug):
    _, carrito, ctx = _contexto(request, slug)
    lineas = carrito.lineas()
    ctx.update({'lineas': lineas, 'totales': carrito.totales(lineas), 'hay_faltantes': any(l['sin_stock'] for l in lineas)})
    return render(request, 'Ecommerce/tienda/carrito.html', ctx)


def checkout(request, slug):
    tienda, carrito, ctx = _contexto(request, slug)
    lineas = carrito.lineas()
    if not lineas:
        return redirect('ecommerce_carrito', slug=slug)
    errores, datos = {}, {}
    if request.method == 'POST':
        datos = request.POST
        errores = validar_checkout(tienda, datos)
        if not errores:
            pedido, motivo = crear_pedido(tienda, carrito, datos)
            if pedido:
                return redirect('ecommerce_pedido', slug=slug, token=pedido.token)
            errores['general'] = f'No pudimos tomar tu pedido: {motivo}'
    ctx.update({'lineas': lineas, 'totales': carrito.totales(lineas), 'errores': errores, 'datos': datos})
    return render(request, 'Ecommerce/tienda/checkout.html', ctx)


def pedido(request, slug, token):
    """Seguimiento del pedido. El token (uuid) es la unica credencial: no exponer el numero correlativo en la URL."""
    tienda, _, ctx = _contexto(request, slug)
    ped = Pedido.objects.filter(tiendaobj=tienda, token=token).prefetch_related('detalles').first()
    if not ped:
        raise Http404
    ctx.update({'pedido': ped, 'pasos': Pedido.WORKFLOW_STATES, 'paso_actual': Pedido.WORKFLOW_STATES.index(ped.estado)})
    return render(request, 'Ecommerce/tienda/pedido.html', ctx)
