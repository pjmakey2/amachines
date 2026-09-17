import json
from datetime import date
from decimal import Decimal

from django.test import TestCase

from Egreso.mng_egreso import MEgreso, fecha_aplicacion, sumar_meses
from Egreso.models import CategoriaGasto, Gasto, GastoRecurrente, PagoProveedor, Proveedor, TransferenciaInterna
from OptsIO.mng_workflow import MWorkflow
from OptsIO.models import BusinessEvent
from OptsIO.testing import check_ui, grid_records, make_business, make_user
from Tesoreria.models import Banco, Caja, Chequera, CuentaBancaria, MovimientoTesoreria


class EgresoBase(TestCase):
    def setUp(self):
        self.b = make_business()
        self.u = make_user('admin', self.b, superuser=True)
        self.prov = Proveedor.objects.create(businessobj=self.b, ruc='800', nombre='Proveedor SA')
        self.cat = CategoriaGasto.objects.create(businessobj=self.b, nombre='Servicios')
        banco = Banco.objects.create(businessobj=self.b, nombre='Banco A')
        self.cuenta = CuentaBancaria.objects.create(businessobj=self.b, bancoobj=banco, numero='1', saldo_inicial=10_000_000)
        self.chequera = Chequera.objects.create(businessobj=self.b, cuentaobj=self.cuenta, numero_desde=500,
                                                numero_hasta=510, proximo_numero=500)
        self.chica = Caja.objects.create(businessobj=self.b, nombre='Chica', tipo='chica', tope=1_000_000)
        self.me = MEgreso()

    def call(self, metodo, **fields):
        return metodo(userobj=self.u, qdict={'uc_fields': json.dumps(fields)})[0]

    def gasto(self, **f):
        base = dict(tipo='comun', fecha='2026-09-01', proveedorobj_id=self.prov.pk, categoriaobj_id=self.cat.pk,
                    concepto='Internet', gravada_10='1100000', factura_numero='001-001-0000001')
        base.update(f)
        rsp = self.call(self.me.create_gasto, **base)
        self.assertIn('success', rsp, rsp)
        return Gasto.objects.get(pk=rsp['record_id'])

    def aprobar(self, obj):
        obj.avanzar(self.u)
        obj.avanzar(self.u)
        return obj


class GastoPagoTest(EgresoBase):
    def test_gasto_comun_pago_con_cheque_y_anulacion(self):
        g = self.gasto()
        self.assertEqual((g.numero, g.estado, g.total, g.iva_10), (1, 'cargado', 1100000, Decimal('100000')))
        self.aprobar(g)
        self.assertTrue(BusinessEvent.objects.filter(event_type='egreso.gasto.aprobado', source_id=g.pk).exists())
        self.assertIn('error', self.call(self.me.create_gasto, id=g.pk, tipo='comun', fecha='2026-09-01',
                                         categoriaobj_id=self.cat.pk, proveedorobj_id=self.prov.pk, concepto='x', gravada_10='1'))

        rsp = self.call(self.me.create_pago, fecha='2026-09-05', medio='cheque', chequeraobj_id=self.chequera.pk,
                        detalles=[{'gasto_id': g.pk, 'monto': '600000'}])
        pago = PagoProveedor.objects.get(pk=rsp['record_id'])
        self.assertEqual(self.cuenta.get_saldo(), 10_000_000)  # cargado: todavia no mueve fondos
        self.aprobar(pago)
        g.refresh_from_db()
        self.assertEqual((pago.chequeobj.numero, g.pagado, g.saldo, g.estado_pago), (500, 600000, 500000, 'PARCIAL'))
        self.assertEqual(self.cuenta.get_saldo(), 9_400_000)
        self.assertIn('pagos aplicados', g.validar_anulacion(self.u))

        pago.anular(self.u, 'error de carga')
        g.refresh_from_db()
        pago.chequeobj.refresh_from_db()
        self.assertEqual((g.pagado, g.estado_pago, pago.chequeobj.estado), (0, 'PENDIENTE', 'anulado'))
        self.assertEqual(self.cuenta.get_saldo(), 10_000_000)

    def test_pago_no_supera_saldo_ni_mezcla_proveedores(self):
        g = self.aprobar(self.gasto())
        self.assertIn('error', self.call(self.me.create_pago, fecha='2026-09-05', medio='transferencia',
                                         cuentaobj_id=self.cuenta.pk, detalles=[{'gasto_id': g.pk, 'monto': '9999999'}]))
        otro = Proveedor.objects.create(businessobj=self.b, ruc='801', nombre='Otro')
        g2 = self.aprobar(self.gasto(proveedorobj_id=otro.pk, factura_numero='2'))
        self.assertIn('error', self.call(self.me.create_pago, fecha='2026-09-05', medio='transferencia', cuentaobj_id=self.cuenta.pk,
                                         detalles=[{'gasto_id': g.pk, 'monto': '1'}, {'gasto_id': g2.pk, 'monto': '1'}]))

    def test_gasto_comun_sin_factura_no_se_aprueba(self):
        g = self.gasto(factura_numero='')
        g.avanzar(self.u)
        self.assertIn('factura', g.validar_avance(self.u))


class CajaChicaYRendirTest(EgresoBase):
    def _reponer(self, monto):
        rsp = self.call(self.me.create_transferencia, fecha='2026-09-01', monto=str(monto),
                        origen_cuentaobj_id=self.cuenta.pk, destino_cajaobj_id=self.chica.pk, concepto='Reposición')
        return rsp

    def test_reposicion_respeta_tope_y_gasto_se_paga_solo(self):
        self.assertIn('tope', self._reponer(1_500_000)['error'])
        tr = TransferenciaInterna.objects.get(pk=self._reponer(800_000)['record_id'])
        self.aprobar(tr)
        self.assertEqual((self.chica.get_saldo(), self.cuenta.get_saldo()), (800_000, 9_200_000))

        g = self.gasto(tipo='caja_chica', cajaobj_id=self.chica.pk, proveedorobj_id='', beneficiario='Ferretería',
                       gravada_10='50000', factura_numero='')
        self.aprobar(g)
        self.assertEqual((g.estado_pago, self.chica.get_saldo()), ('PAGADO', 750_000))
        g.anular(self.u)
        self.assertEqual(self.chica.get_saldo(), 800_000)

        caro = self.gasto(tipo='caja_chica', cajaobj_id=self.chica.pk, gravada_10='900000')
        caro.avanzar(self.u)
        self.assertIn('Saldo insuficiente', caro.validar_avance(self.u))

    def test_gasto_a_rendir_con_devolucion(self):
        g = self.gasto(tipo='a_rendir', presupuesto_monto='500000', gravada_10='', factura_numero='', responsable='Juan')
        self.aprobar(g)
        self.assertEqual(g.saldo, 500000)
        pago = PagoProveedor.objects.get(pk=self.call(
            self.me.create_pago, fecha='2026-09-02', medio='transferencia', cuentaobj_id=self.cuenta.pk,
            detalles=[{'gasto_id': g.pk, 'monto': '500000'}])['record_id'])
        self.aprobar(pago)
        sin_destino = self.call(self.me.rendir_gasto, id=g.pk, factura_numero='001', gravada_10='440000')
        self.assertIn('Sobran 60,000', sin_destino['error'])
        rsp = self.call(self.me.rendir_gasto, id=g.pk, factura_numero='001', gravada_10='440000',
                        devolucion_cuentaobj_id=self.cuenta.pk)
        self.assertIn('success', rsp, rsp)
        g.refresh_from_db()
        self.assertEqual((g.rendido, g.total, g.pagado, g.saldo, g.estado_pago), (True, 440000, 440000, 0, 'PAGADO'))
        self.assertEqual(self.cuenta.get_saldo(), 10_000_000 - 440_000)
        self.assertIn('info', self.call(self.me.rendir_gasto, id=g.pk, factura_numero='001', gravada_10='440000'))


class RecurrentesTest(EgresoBase):
    def test_fechas(self):
        self.assertEqual(fecha_aplicacion(2026, 2, 31), date(2026, 2, 28))
        self.assertEqual(sumar_meses(date(2026, 12, 31), 2, 31), date(2027, 2, 28))

    def test_generacion_idempotente_y_avance(self):
        rsp = self.call(self.me.create_recurrente, proveedorobj_id=self.prov.pk, categoriaobj_id=self.cat.pk,
                        concepto='Alquiler', monto='3000000', frecuencia='mensual', dia_aplicacion='5', fecha_inicio='2026-07-01')
        rec = GastoRecurrente.objects.get(pk=rsp['record_id'])
        self.assertEqual(rec.proxima_fecha, date(2026, 7, 5))
        self.assertEqual(self.me.generar_recurrentes(date(2026, 9, 10))['generados'], 3)
        self.assertEqual(self.me.generar_recurrentes(date(2026, 9, 10))['generados'], 0)
        rec.refresh_from_db()
        self.assertEqual(rec.proxima_fecha, date(2026, 10, 5))
        self.assertEqual(list(Gasto.objects.order_by('fecha').values_list('periodo', flat=True)),
                         ['2026-07-05', '2026-08-05', '2026-09-05'])


class WorkflowEndpointTest(EgresoBase):
    def test_permisos_y_aislamiento(self):
        g = self.gasto()
        q = {'model_app_name': 'Egreso', 'model_name': 'Gasto', 'id': g.pk}
        sin_permiso = make_user('cajero', self.b)
        self.assertIn('permiso', MWorkflow().avanzar(userobj=sin_permiso, qdict=q)['error'])
        ajeno = make_user('ajeno', make_business('80000009', 'Otro'), superuser=True)
        self.assertEqual(MWorkflow().avanzar(userobj=ajeno, qdict=q)['error'], 'Registro inexistente')
        self.assertEqual(MWorkflow().avanzar(userobj=self.u, qdict=q)['estado'], 'verificado')


class UiRenderTest(EgresoBase):
    def test_pantallas_renderizan_y_su_js_es_valido(self):
        for t in ['ProveedorUi', 'ProveedorCreateUi', 'CategoriaGastoUi', 'CategoriaGastoCreateUi', 'GastoRecurrenteUi',
                  'GastoRecurrenteCreateUi', 'GastoUi', 'GastoCreateUi', 'PagoProveedorUi', 'PagoProveedorCreateUi',
                  'TransferenciaInternaUi', 'TransferenciaInternaCreateUi']:
            check_ui(self, self.u, f'Egreso/{t}.html')
        check_ui(self, self.u, 'Egreso/GastoRecurrenteCreateUi.html', dattrs={'en_modal': True, 'proveedor_id': self.prov.pk})
        html = check_ui(self, self.u, 'Egreso/ProveedorCreateUi.html', ('Egreso', 'Proveedor'), self.prov.pk)
        self.assertIn('Gastos recurrentes del proveedor', html)

        g = self.aprobar(self.gasto(tipo='a_rendir', presupuesto_monto='500000', gravada_10='', factura_numero=''))
        self.assertIn('solo lectura', check_ui(self, self.u, 'Egreso/GastoCreateUi.html', ('Egreso', 'Gasto'), g.pk))
        check_ui(self, self.u, 'Egreso/GastoRendirUi.html', ('Egreso', 'Gasto'), g.pk)
        pago = PagoProveedor.objects.get(pk=self.call(
            self.me.create_pago, fecha='2026-09-02', medio='cheque', chequeraobj_id=self.chequera.pk,
            detalles=[{'gasto_id': g.pk, 'monto': '500000'}])['record_id'])
        check_ui(self, self.u, 'Egreso/PagoProveedorCreateUi.html', ('Egreso', 'PagoProveedor'), pago.pk)
        self.aprobar(pago)
        check_ui(self, self.u, 'Egreso/PagoProveedorCreateUi.html', ('Egreso', 'PagoProveedor'), pago.pk)
        html = check_ui(self, self.u, 'Egreso/ChequeRptUi.html', ('Egreso', 'PagoProveedor'), pago.pk)
        self.assertIn('QUINIENTOS MIL GUARANIES', html)
        self.assertIn('PROVEEDOR SA', html)

    def test_grillas_devuelven_campos_relacionados_y_metodos(self):
        g = self.gasto()
        filas = grid_records(self, self.u, 'Egreso', 'Gasto',
                             ['id', 'numero', 'fecha', 'tipo', 'categoriaobj__nombre', 'total', 'estado', 'anulado'],
                             methods=['get_beneficiario'])
        self.assertEqual(len(filas), 1)
        self.assertEqual((filas[0]['categoriaobj__nombre'], filas[0]['get_beneficiario'], filas[0]['estado']),
                         ('Servicios', 'Proveedor SA', 'cargado'))
        self.assertEqual(float(filas[0]['total']), 1100000.0)
        filas = grid_records(self, self.u, 'Egreso', 'Proveedor', ['id', 'nombre'], methods=['get_saldo_pendiente'])
        self.assertEqual(filas[0]['nombre'], 'Proveedor SA')
        ajeno = make_user('ajeno2', make_business('80000010', 'Otro'), superuser=True)
        self.assertEqual(grid_records(self, ajeno, 'Egreso', 'Gasto', ['id']), [])
