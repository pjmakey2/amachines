import json
from decimal import Decimal

from django.test import TestCase

from Almacen.mng_almacen import MAlmacen
from Almacen.models import (
    AjusteStock, AlmacenError, Bodega, MovimientoStock, Recepcion, Ubicacion,
    despachar, liberar_reservas, reservar, stock_disponible, stock_en_ubicacion,
)
from OptsIO.testing import check_ui, grid_records, make_business, make_user
from Sifen.models import Producto


class AlmacenBase(TestCase):
    def setUp(self):
        self.b = make_business()
        self.u = make_user('admin', self.b, superuser=True)
        self.bodega = Bodega.objects.create(businessobj=self.b, nombre='Central')
        mk = lambda codigo, tipo: Ubicacion.objects.create(businessobj=self.b, bodegaobj=self.bodega, codigo=codigo, tipo=tipo)
        self.muelle, self.estante, self.picking, self.averiados = mk('REC-01', 'recepcion'), mk('A-01-01', 'almacenaje'), mk('PK-01', 'picking'), mk('AV-01', 'averiados')
        self.prod = Producto.objects.create(prod_cod=1001, descripcion='Remera')
        self.ma = MAlmacen()

    def recepcion(self, cantidad=10, ubicacion=None, costo='25000'):
        rsp = self.ma.create_recepcion(userobj=self.u, qdict={'uc_fields': json.dumps({
            'fecha': '2026-09-01', 'bodegaobj_id': self.bodega.pk, 'proveedor': 'Textil SA', 'documento_ref': 'REM-1',
            'detalles': [{'producto_id': self.prod.pk, 'ubicacion_id': (ubicacion or self.muelle).pk, 'cantidad_esperada': '10',
                          'cantidad_recibida': str(cantidad), 'costo_unitario': costo}]})})[0]
        self.assertIn('success', rsp, rsp)
        return Recepcion.objects.get(pk=rsp['record_id'])

    def aprobar(self, obj):
        obj.avanzar(self.u)
        obj.avanzar(self.u)
        return obj


class RecepcionAlmacenajeTest(AlmacenBase):
    def test_stock_entra_al_aprobar_y_se_almacena(self):
        rec = self.recepcion()
        self.assertEqual(stock_en_ubicacion(self.prod, self.muelle), 0)
        self.aprobar(rec)
        self.prod.refresh_from_db()
        self.assertEqual((stock_en_ubicacion(self.prod, self.muelle), self.prod.stock, self.prod.costo), (10, 10, 25000))

        rsp = self.ma.trasladar(userobj=self.u, qdict={'producto_id': self.prod.pk, 'origen_id': self.muelle.pk,
                                                       'destino_id': self.estante.pk, 'cantidad': '7'})
        self.assertIn('success', rsp, rsp)
        self.assertIn('error', self.ma.trasladar(userobj=self.u, qdict={'producto_id': self.prod.pk, 'origen_id': self.muelle.pk,
                                                                        'destino_id': self.estante.pk, 'cantidad': '4'}))
        self.assertEqual((stock_en_ubicacion(self.prod, self.muelle), stock_en_ubicacion(self.prod, self.estante)), (3, 7))
        # ya se movio mercaderia: no se puede anular hasta devolverla al muelle
        self.assertIn('trasládela', rec.validar_anulacion(self.u))
        self.ma.trasladar(userobj=self.u, qdict={'producto_id': self.prod.pk, 'origen_id': self.estante.pk, 'destino_id': self.muelle.pk, 'cantidad': '7'})
        rec.anular(self.u, 'remisión equivocada')
        self.prod.refresh_from_db()
        self.assertEqual((stock_en_ubicacion(self.prod, self.muelle), self.prod.stock), (0, 0))

    def test_reserva_despacho_y_no_vendible(self):
        self.aprobar(self.recepcion(6, self.estante))
        self.aprobar(self.recepcion(4, self.picking))
        self.aprobar(self.recepcion(5, self.averiados))
        self.assertEqual(stock_disponible(self.b, self.prod), 10)  # averiados no cuenta
        pedido, otro = self.u, self.bodega  # cualquier modelo sirve de origen
        self.assertEqual(reservar(self.b, self.prod, 8, pedido), '')
        self.assertEqual(reservar(self.b, self.prod, 8, pedido), '')  # idempotente
        self.assertEqual(stock_disponible(self.b, self.prod), 2)
        self.assertIn('quedan 2', reservar(self.b, self.prod, 3, otro))

        movs = despachar(self.b, self.prod, 8, pedido, 'Pedido 1', self.u)
        self.assertEqual([(m.ubicacionobj.codigo, m.cantidad) for m in movs], [('PK-01', Decimal(-4)), ('A-01-01', Decimal(-4))])
        self.assertEqual(despachar(self.b, self.prod, 8, pedido, 'Pedido 1', self.u), [])  # no descuenta dos veces
        self.assertEqual(stock_disponible(self.b, self.prod), 2)
        with self.assertRaises(AlmacenError):
            despachar(self.b, self.prod, 3, otro, 'Pedido 2', self.u)
        reservar(self.b, self.prod, 2, otro)
        liberar_reservas(otro)
        self.assertEqual(stock_disponible(self.b, self.prod), 2)

    def test_ajuste_de_inventario(self):
        self.aprobar(self.recepcion(10, self.estante))
        rsp = self.ma.create_ajuste(userobj=self.u, qdict={'uc_fields': json.dumps({
            'productoobj_id': self.prod.pk, 'ubicacionobj_id': self.estante.pk, 'cantidad_contada': '8', 'motivo': 'Conteo mensual'})})[0]
        ajuste = AjusteStock.objects.get(pk=rsp['record_id'])
        self.assertEqual(ajuste.cantidad_sistema, 10)
        self.aprobar(ajuste)
        self.assertEqual(stock_en_ubicacion(self.prod, self.estante), 8)
        self.assertEqual(MovimientoStock.objects.filter(tipo='ajuste').get().cantidad, -2)

    def test_ui_y_grillas(self):
        rec = self.aprobar(self.recepcion())
        for t in ['BodegaUi', 'BodegaCreateUi', 'UbicacionUi', 'UbicacionCreateUi', 'RecepcionUi', 'RecepcionCreateUi',
                  'StockUbicacionUi', 'MovimientoStockUi', 'AjusteStockUi', 'AjusteStockCreateUi']:
            check_ui(self, self.u, f'Almacen/{t}.html')
        check_ui(self, self.u, 'Almacen/RecepcionCreateUi.html', ('Almacen', 'Recepcion'), rec.pk)
        filas = grid_records(self, self.u, 'Almacen', 'StockUbicacion', ['id', 'cantidad', 'productoobj__descripcion', 'productoobj_id', 'ubicacionobj_id'], methods=['get_ubicacion'])
        self.assertEqual((filas[0]['productoobj__descripcion'], filas[0]['get_ubicacion']), ('Remera', 'Central / REC-01'))
