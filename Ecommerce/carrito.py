"""Carrito (en sesion) y checkout de la tienda publica. Precios y stock se validan siempre en el servidor."""
import re
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from Almacen.models import reservar, stock_disponible
from Ecommerce.models import Pedido, PedidoDetalle, ProductoTienda
from OptsIO.io_business import siguiente_numero
from OptsIO.io_money import precision_monetaria

RE_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MAX_POR_LINEA = 99


class Carrito:
    def __init__(self, request, tienda):
        self.session, self.tienda = request.session, tienda
        self.key = f"carrito_{tienda.pk}"
        self.items = dict(self.session.get(self.key, {}))

    def _guardar(self):
        self.session[self.key] = self.items
        self.session.modified = True

    def set(self, productotienda_id, cantidad: int):
        cantidad = max(0, min(int(cantidad), MAX_POR_LINEA))
        if cantidad:
            self.items[str(productotienda_id)] = cantidad
        else:
            self.items.pop(str(productotienda_id), None)
        self._guardar()

    def agregar(self, productotienda_id, cantidad: int = 1):
        self.set(productotienda_id, int(self.items.get(str(productotienda_id), 0)) + int(cantidad))

    def vaciar(self):
        self.items = {}
        self._guardar()

    @property
    def cantidad_total(self) -> int:
        return sum(int(c) for c in self.items.values())

    @precision_monetaria
    def lineas(self) -> list:
        """Lineas valorizadas con el precio y stock actuales; descarta lo que ya no esta publicado."""
        publicados = ProductoTienda.objects.filter(
            tiendaobj=self.tienda, publicado=True, productoobj__activo=True, pk__in=[int(k) for k in self.items]).select_related('productoobj')
        lineas = []
        for pt in publicados:
            cantidad = Decimal(int(self.items[str(pt.pk)]))
            disponible = stock_disponible(self.tienda.businessobj, pt.productoobj)
            lineas.append({'pt': pt, 'cantidad': int(cantidad), 'precio': pt.precio, 'total': pt.precio * cantidad,
                           'disponible': disponible, 'sin_stock': disponible < cantidad})
        return lineas

    @precision_monetaria
    def totales(self, lineas=None) -> dict:
        lineas = self.lineas() if lineas is None else lineas
        subtotal = sum((l['total'] for l in lineas), Decimal(0))
        envio = self.tienda.calcular_envio(subtotal) if lineas else Decimal(0)
        return {'subtotal': subtotal, 'envio': envio, 'total': subtotal + envio}


def validar_checkout(tienda, datos: dict) -> dict:
    """{campo: mensaje} con los errores del formulario de checkout."""
    errores = {}
    for campo, etiqueta in (('cliente_nombre', 'el nombre'), ('cliente_telefono', 'el teléfono'), ('direccion', 'la dirección de entrega')):
        if not (datos.get(campo) or '').strip():
            errores[campo] = f'Indique {etiqueta}'
    if not RE_EMAIL.match((datos.get('cliente_email') or '').strip()):
        errores['cliente_email'] = 'Indique un email válido'
    metodos = [m for m, ok in (('transferencia', tienda.acepta_transferencia), ('contra_entrega', tienda.acepta_contra_entrega)) if ok]
    if datos.get('metodo_pago') not in metodos:
        errores['metodo_pago'] = 'Elija una forma de pago'
    return errores


@precision_monetaria
def crear_pedido(tienda, carrito: Carrito, datos: dict):
    """
    Crea el pedido y reserva el stock de cada linea en una sola transaccion: si algo no alcanza
    no se crea nada. Devuelve (pedido, '') o (None, motivo).
    """
    lineas = carrito.lineas()
    if not lineas:
        return None, 'El carrito está vacío'
    totales = carrito.totales(lineas)
    limpio = lambda campo, largo: (datos.get(campo) or '').strip()[:largo]
    with transaction.atomic():
        pedido = Pedido(
            businessobj=tienda.businessobj, tiendaobj=tienda, numero=siguiente_numero(Pedido, tienda.businessobj),
            cliente_nombre=limpio('cliente_nombre', 200), cliente_documento=re.sub(r'[^0-9\-]', '', limpio('cliente_documento', 30)),
            cliente_email=limpio('cliente_email', 120), cliente_telefono=limpio('cliente_telefono', 40),
            direccion=limpio('direccion', 300), ciudad=limpio('ciudad', 120), notas=limpio('notas', 300),
            metodo_pago=datos.get('metodo_pago'), moneda=tienda.moneda, subtotal=totales['subtotal'],
            costo_envio=totales['envio'], total=totales['total'], cargado_fecha=datetime.now(), cargado_usuario='tienda online',
            workflow_log=[{'estado': 'recibido', 'username': '', 'usuario': 'tienda online',
                           'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'nota': ''}])
        pedido.save()
        for l in lineas:
            PedidoDetalle.objects.create(pedidoobj=pedido, productotiendaobj=l['pt'], productoobj=l['pt'].productoobj,
                                         titulo=l['pt'].titulo, precio_unitario=l['precio'], cantidad=l['cantidad'], total=l['total'])
        # La reserva es por (producto, pedido): un pedido con el mismo producto publicado dos veces no existe (unique tienda+producto)
        for l in lineas:
            motivo = reservar(tienda.businessobj, l['pt'].productoobj, l['cantidad'], pedido)
            if motivo:
                transaction.set_rollback(True)
                return None, motivo
    carrito.vaciar()
    return pedido, ''
