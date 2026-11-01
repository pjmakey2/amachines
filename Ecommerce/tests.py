import json
from decimal import Decimal
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from Almacen.models import Bodega, Ubicacion, mover_stock, stock_disponible, stock_en_ubicacion
from Deposito.models import Deposito
from Ecommerce.mng_ecommerce import MEcommerce
from Ecommerce.models import Coleccion, Pedido, ProductoTienda, PromoTienda, TemaTienda, Tienda
from OptsIO import events
from OptsIO.models import BusinessEvent
from OptsIO.testing import check_ui, grid_records, make_business, make_user
from Sifen.models import Producto


class EcommerceBase(TestCase):
    def setUp(self):
        self.b = make_business()
        self.u = make_user('admin', self.b, superuser=True)
        self.me = MEcommerce()
        bodega = Bodega.objects.create(businessobj=self.b, nombre='Central')
        self.ubi = Ubicacion.objects.create(businessobj=self.b, bodegaobj=bodega, codigo='PK-01', tipo='picking')
        self.prod = Producto.objects.create(prod_cod=2001, descripcion='Remera básica', precio=90000)
        mover_stock(self.b, self.prod, self.ubi, 5, 'ajuste', 'Stock inicial')
        tema = self.guardar(self.me.save_tema, nombre='Marca', preset='minimal', colores_propios='true', color_primario='#0f172a', color_acento='#e11d48',
                            color_fondo='#ffffff', color_texto='#111111', fuente='"Inter", sans-serif; } body { display:none',
                            css_extra='.tienda-banner { padding: 9rem; } </style><script>alert(1)</script>')
        tienda = self.guardar(self.me.save_tienda, nombre='Mi Tienda', temaobj_id=tema, costo_envio='25000', envio_gratis_desde='200000',
                              anuncio_texto='Envío gratis desde 200.000', banner_cta_texto='Ver remeras',
                              acepta_transferencia='true', acepta_contra_entrega='true', datos_transferencia='Banco A cta 123')
        self.tienda = Tienda.objects.get(pk=tienda)
        col = self.guardar(self.me.save_coleccion, tiendaobj_id=tienda, nombre='Remeras')
        self.pt = ProductoTienda.objects.get(pk=self.guardar(
            self.me.save_productotienda, tiendaobj_id=tienda, productoobj_id=self.prod.pk, coleccionobj_id=col,
            precio_online='80000', precio_comparacion='100000', destacado='true', descripcion_larga='Algodón peinado'))
        self.url = lambda nombre, *a: f"/tienda/{self.tienda.slug}/" + {'home': '', 'carrito': 'carrito/', 'agregar': 'carrito/agregar/',
                                                                       'actualizar': 'carrito/actualizar/', 'checkout': 'checkout/'}[nombre]

    def guardar(self, metodo, files=None, **fields):
        rsp = metodo(userobj=self.u, files=files or {}, qdict={'uc_fields': json.dumps(fields)})[0]
        self.assertIn('success', rsp, rsp)
        return rsp['record_id']

    def comprar(self, cantidad=2, **datos):
        self.client.post(self.url('agregar'), {'producto_id': self.pt.pk, 'cantidad': cantidad})
        base = {'cliente_nombre': 'Ana Gómez', 'cliente_email': 'ana@test.com', 'cliente_telefono': '0981', 'direccion': 'Calle 1',
                'metodo_pago': 'transferencia', 'cliente_documento': ''}
        base.update(datos)
        return self.client.post(self.url('checkout'), base)


class TiendaPublicaTest(EcommerceBase):
    def test_catalogo_tema_y_busqueda(self):
        self.assertEqual(self.tienda.slug, 'mi-tienda')
        html = self.client.get(self.url('home')).content.decode()
        self.assertIn('tienda-preset-minimal', html)
        self.assertIn('temas/minimal.css', html)
        self.assertIn('Envío gratis desde 200.000', html)
        self.assertIn('Ver remeras', html)
        self.assertIn('tienda-sidebar', html)
        self.assertIn('--t-acento: #e11d48;', html)
        self.assertNotIn('<script>alert(1)', html)      # el CSS del tema no puede inyectar HTML
        self.assertNotIn('display:none', html)          # ni romper la declaracion de la fuente
        self.assertIn('Remera básica', html)
        self.assertIn('80\xa0000', html)
        self.assertIn('Remeras', html)
        self.assertIn('20% OFF', html)  # 80.000 vs 100.000 tachado
        self.assertNotIn('Remera', self.client.get(self.url('home'), {'q': 'zapato'}).content.decode().split('<main>')[1].split('No encontramos')[0][-200:])
        # ?preset= solo cambia el estilo para usuarios logueados
        self.assertIn('tienda-preset-minimal', self.client.get(self.url('home'), {'preset': 'bazaar'}).content.decode())
        self.client.force_login(self.u)
        self.assertIn('tienda-preset-bazaar', self.client.get(self.url('home'), {'preset': 'bazaar'}).content.decode())
        self.client.logout()
        self.assertEqual(self.client.get(f"/tienda/{self.tienda.slug}/coleccion/remeras/").status_code, 200)
        det = self.client.get(f"/tienda/{self.tienda.slug}/producto/{self.pt.slug}/").content.decode()
        self.assertIn('Agregar al carrito', det)
        self.assertIn('Quedan solo 5', det)
        self.assertEqual(self.client.get('/tienda/no-existe/').status_code, 404)
        ProductoTienda.objects.filter(pk=self.pt.pk).update(publicado=False)
        self.assertEqual(self.client.get(f"/tienda/{self.tienda.slug}/producto/{self.pt.slug}/").status_code, 404)

    def test_checkout_valida_reserva_stock_y_no_sobrevende(self):
        rsp = self.comprar(2, cliente_email='malo', metodo_pago='bitcoin')
        self.assertEqual(rsp.status_code, 200)
        self.assertIn('Indique un email válido', rsp.content.decode())
        self.assertEqual(Pedido.objects.count(), 0)

        rsp = self.comprar(0)  # el carrito ya tenia 2
        pedido = Pedido.objects.get()
        self.assertRedirects(rsp, pedido.get_url())
        self.assertEqual((pedido.estado, pedido.subtotal, pedido.costo_envio, pedido.total), ('recibido', 160000, 25000, 185000))
        self.assertEqual(pedido.detalles.get().precio_unitario, 80000)  # precio del servidor, no del cliente
        self.assertEqual(stock_disponible(self.b, self.prod), 3)
        seguimiento = self.client.get(pedido.get_url()).content.decode()
        self.assertIn('Banco A cta 123', seguimiento)
        self.assertEqual(self.client.get(self.url('carrito')).content.decode().count('Tu carrito está vacío'), 1)

        otro = self.client_class()
        otro.post(self.url('agregar'), {'producto_id': self.pt.pk, 'cantidad': 4})
        self.assertIn('Solo quedan 3', otro.get(self.url('carrito')).content.decode())
        rsp = otro.post(self.url('checkout'), {'cliente_nombre': 'Luis', 'cliente_email': 'l@test.com', 'cliente_telefono': '1',
                                               'direccion': 'x', 'metodo_pago': 'contra_entrega'})
        self.assertIn('quedan 3 disponibles', rsp.content.decode())
        self.assertEqual(Pedido.objects.count(), 1)

    def test_envio_gratis_y_token_no_adivinable(self):
        self.comprar(3)
        pedido = Pedido.objects.get()
        self.assertEqual((pedido.subtotal, pedido.costo_envio), (240000, 0))
        self.assertEqual(self.client.get(f"/tienda/{self.tienda.slug}/pedido/00000000-0000-0000-0000-000000000000/").status_code, 404)


class PedidoWorkflowTest(EcommerceBase):
    def procesar(self):
        for e in BusinessEvent.objects.exclude(status='done').order_by('pk'):
            self.assertEqual(events.process_event(e.pk)['status'], 'done')

    def test_pago_factura_deposito_y_despacho(self):
        self.comprar(2, cliente_documento='1234567-8')
        pedido = Pedido.objects.get()
        self.me.set_pago_referencia(userobj=self.u, qdict={'id': pedido.pk, 'referencia': 'TRF-99'})
        pedido.refresh_from_db()
        pedido.avanzar(self.u)  # pagado
        doc = mock.Mock(pk=555, doc_numero=77)
        with mock.patch('Ecommerce.handlers.MSifen') as msifen, mock.patch('Ecommerce.handlers.DocumentHeader') as dh, \
                mock.patch('Ecommerce.handlers.mng_gmdata.Gdata') as gdata:
            gdata.return_value.calculate_dv.return_value = 8
            dh.objects.filter.return_value.first.return_value = None
            dh.objects.get.return_value = doc
            msifen.return_value.create_documentheader.return_value = ({'success': 'ok', 'record_id': 555}, [], {})
            self.procesar()
            uc = json.loads(msifen.return_value.create_documentheader.call_args.kwargs['qdict']['uc_fields'])
        self.assertEqual((uc['pdv_ruc'], uc['pdv_ruc_dv'], uc['pdv_innominado'], uc['doc_cre_tipo'], uc['doc_tipo_pago_cod']), ('1234567', 8, False, 1, 5))
        self.assertEqual([(d['prod_cod'], d['cantidad'], d['precio_unitario'], d['g10']) for d in uc['details']],
                         [(2001, 2.0, 80000.0, 100), (999999, 1, 25000.0, 100)])
        pedido.refresh_from_db()
        self.assertEqual(pedido.documentheader_id, 555)
        dep = Deposito.objects.get()
        self.assertEqual((dep.tipo, dep.monto, dep.boleta_numero, dep.estado), ('transferencia', Decimal('185000'), 'TRF-99', 'cargado'))
        self.assertIn('nota de crédito', pedido.validar_anulacion(self.u))

        pedido.avanzar(self.u)  # preparado
        self.assertEqual(stock_en_ubicacion(self.prod, self.ubi), 5)
        pedido.avanzar(self.u)  # despachado
        self.assertEqual((stock_en_ubicacion(self.prod, self.ubi), stock_disponible(self.b, self.prod)), (3, 3))

    def test_anular_antes_del_pago_libera_la_reserva(self):
        self.comprar(2)
        pedido = Pedido.objects.get()
        self.assertEqual(stock_disponible(self.b, self.prod), 3)
        pedido.anular(self.u, 'cliente desistió')
        self.assertEqual(stock_disponible(self.b, self.prod), 5)
        self.assertIn('anulado', self.client.get(pedido.get_url()).content.decode())


class AdminTest(EcommerceBase):
    def test_validaciones_de_tema_y_aislamiento(self):
        rsp = self.me.save_tema(userobj=self.u, files={}, qdict={'uc_fields': json.dumps(
            {'nombre': 'X', 'preset': 'clasico', 'colores_propios': 'true', 'color_primario': 'red', 'color_acento': '#fff', 'color_fondo': '#fff', 'color_texto': '#000'})})[0]
        self.assertIn('hexadecimal', rsp['error'])
        self.assertIn('preset', self.me.save_tema(userobj=self.u, files={}, qdict={'uc_fields': json.dumps({'nombre': 'X', 'preset': 'zzz'})})[0]['error'])
        malo = SimpleUploadedFile('tema.js', b'alert(1)')
        rsp = self.me.save_tema(userobj=self.u, files={'css_archivo': malo}, qdict={'uc_fields': json.dumps(
            {'nombre': 'X', 'preset': 'clasico'})})[0]
        self.assertIn('.css', rsp['error'])
        css = SimpleUploadedFile('marca.css', b'.tienda-header { background: black; }')
        tema_id = self.guardar(self.me.save_tema, files={'css_archivo': css}, nombre='Con CSS', preset='clasico')
        Tienda.objects.filter(pk=self.tienda.pk).update(temaobj_id=tema_id)
        self.assertIn(TemaTienda.objects.get(pk=tema_id).css_archivo.url, self.client.get(self.url('home')).content.decode())

        ajeno = make_user('ajeno', make_business('80000077', 'Otro'), superuser=True)
        rsp = self.me.save_coleccion(userobj=ajeno, files={}, qdict={'uc_fields': json.dumps({'tiendaobj_id': self.tienda.pk, 'nombre': 'Intrusa'})})[0]
        self.assertIn('error', rsp)
        self.assertEqual(grid_records(self, ajeno, 'Ecommerce', 'Pedido', ['id']), [])

    def test_promos_y_presets(self):
        pid = self.guardar(self.me.save_promo, tiendaobj_id=self.tienda.pk, posicion='lateral', etiqueta='Novedades', titulo='Buzos de invierno', subtitulo='20% OFF', color_fondo='#fce7f3')
        self.assertIn('error', self.me.save_promo(userobj=self.u, files={}, qdict={'uc_fields': json.dumps({'tiendaobj_id': self.tienda.pk, 'titulo': 'x', 'posicion': 'lateral', 'color_fondo': 'rosa'})})[0])
        TemaTienda.objects.filter(pk=self.tienda.temaobj_id).update(preset='bazaar')
        html = self.client.get(self.url('home')).content.decode()
        self.assertIn('hero-split', html)
        self.assertIn('Buzos de invierno', html)
        self.assertIn('background-color: #fce7f3', html)
        TemaTienda.objects.filter(pk=self.tienda.temaobj_id).update(preset='fresco')
        PromoTienda.objects.filter(pk=pid).update(posicion='carrusel')
        self.assertIn('promo-carrusel', self.client.get(self.url('home')).content.decode())
        presets = self.me.get_presets(userobj=self.u, qdict={})
        self.assertEqual([p['clave'] for p in presets['presets']], ['clasico', 'minimal', 'bazaar', 'fresco', 'hogar'])
        self.assertEqual(presets['tienda_url'], self.tienda.get_url())

    def test_pantallas_de_administracion(self):
        self.comprar(1)
        pedido = Pedido.objects.get()
        for t in ['TiendaUi', 'TiendaCreateUi', 'TemaTiendaUi', 'TemaTiendaCreateUi', 'ColeccionUi', 'ColeccionCreateUi', 'PromoTiendaUi', 'PromoTiendaCreateUi',
                  'ProductoTiendaUi', 'ProductoTiendaCreateUi', 'PedidoUi']:
            check_ui(self, self.u, f'Ecommerce/{t}.html')
        check_ui(self, self.u, 'Ecommerce/PedidoCreateUi.html', ('Ecommerce', 'Pedido'), pedido.pk)
        check_ui(self, self.u, 'Ecommerce/ProductoTiendaCreateUi.html', ('Ecommerce', 'ProductoTienda'), self.pt.pk)
        check_ui(self, self.u, 'Ecommerce/TiendaCreateUi.html', ('Ecommerce', 'Tienda'), self.tienda.pk)
        filas = grid_records(self, self.u, 'Ecommerce', 'ProductoTienda', ['id', 'titulo'], methods=['get_precio', 'get_disponible', 'get_imagen'])
        self.assertEqual((filas[0]['get_precio'], filas[0]['get_disponible']), (80000.0, 4.0))
