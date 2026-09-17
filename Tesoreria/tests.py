import json
from datetime import date

from django.test import TestCase

from OptsIO.io_maction import IOMaction
from OptsIO.io_serial import IoS
from OptsIO.testing import check_ui, make_business, make_user
from Tesoreria.mng_tesoreria import MTesoreria
from Tesoreria.models import TesoreriaError
from Tesoreria.models import Banco, CuentaBancaria, Chequera, Caja, MovimientoTesoreria


class TesoreriaBase(TestCase):
    def setUp(self):
        self.b1 = make_business('80000001', 'Uno')
        self.b2 = make_business('80000002', 'Dos')
        self.u1 = make_user('u1', self.b1)
        self.u2 = make_user('u2', self.b2)
        self.banco = Banco.objects.create(businessobj=self.b1, nombre='Banco A')
        self.cuenta = CuentaBancaria.objects.create(
            businessobj=self.b1, bancoobj=self.banco, numero='001', saldo_inicial=1000)
        self.mt = MTesoreria()


class MovimientosTest(TesoreriaBase):
    def test_saldo_y_anulados(self):
        self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 500, 'dep', cuentaobj=self.cuenta)
        m = self.mt.registrar_movimiento(self.b1, date.today(), 'egreso', 200, 'pago', cuentaobj=self.cuenta)
        self.assertEqual(self.cuenta.get_saldo(), 1300)
        MovimientoTesoreria.objects.filter(pk=m.pk).update(anulado=True)
        self.assertEqual(self.cuenta.get_saldo(), 1500)

    def test_clave_idempotente(self):
        a = self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 500, 'dep', cuentaobj=self.cuenta, clave='k1')
        b = self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 500, 'dep', cuentaobj=self.cuenta, clave='k1')
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(self.cuenta.get_saldo(), 1500)

    def test_caja_chica_tope_y_saldo(self):
        caja = Caja.objects.create(businessobj=self.b1, nombre='Chica', tipo='chica', tope=1000)
        self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 800, 'reposicion', cajaobj=caja)
        with self.assertRaises(TesoreriaError):
            self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 300, 'reposicion', cajaobj=caja)
        with self.assertRaises(TesoreriaError):
            self.mt.registrar_movimiento(self.b1, date.today(), 'egreso', 900, 'gasto', cajaobj=caja)
        self.mt.registrar_movimiento(self.b1, date.today(), 'egreso', 300, 'gasto', cajaobj=caja)
        self.assertEqual(caja.get_saldo(), 500)

    def test_validaciones(self):
        caja = Caja.objects.create(businessobj=self.b2, nombre='Ajena')
        with self.assertRaises(TesoreriaError):
            self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 10, 'x', cajaobj=caja)
        with self.assertRaises(TesoreriaError):
            self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 10, 'x')
        with self.assertRaises(TesoreriaError):
            self.mt.registrar_movimiento(self.b1, date.today(), 'ingreso', 0, 'x', cuentaobj=self.cuenta)


class ChequesTest(TesoreriaBase):
    def _chequera(self, **f):
        fields = {'cuentaobj_id': self.cuenta.pk, 'numero_desde': 100, 'numero_hasta': 101, 'tipo': 'vista'}
        fields.update(f)
        return self.mt.create_chequera(userobj=self.u1, qdict={'uc_fields': json.dumps(fields)})[0]

    def test_numeracion_y_agotamiento(self):
        self.assertIn('success', self._chequera())
        ch = Chequera.objects.get()
        nums = [self.mt.emitir_cheque(ch, 'Prov', 50, date.today(), userobj=self.u1).numero for _ in range(2)]
        self.assertEqual(nums, [100, 101])
        with self.assertRaises(TesoreriaError):
            self.mt.emitir_cheque(ch, 'Prov', 50, date.today())

    def test_solapamiento_y_cuenta_ajena(self):
        self._chequera()
        self.assertIn('error', self._chequera(numero_desde=101, numero_hasta=200))
        r = self.mt.create_chequera(userobj=self.u2, qdict={'uc_fields': json.dumps(
            {'cuentaobj_id': self.cuenta.pk, 'numero_desde': 1, 'numero_hasta': 10})})[0]
        self.assertIn('error', r)


class TenantIsolationTest(TesoreriaBase):
    def _q(self, **extra):
        q = {'model_app_name': 'Tesoreria', 'model_name': 'Banco', 'dbcon': 'default'}
        q.update(extra)
        return q

    def test_lectura_solo_negocio_activo(self):
        Banco.objects.create(businessobj=self.b2, nombre='Banco B')
        q = self._q(fields=json.dumps(['id', 'nombre']))
        nombres = lambda u: [r['nombre'] for r in IoS().seModel(userobj=u, qdict=q)['qs']]
        self.assertEqual(nombres(self.u1), ['Banco A'])
        self.assertEqual(nombres(self.u2), ['Banco B'])
        self.assertEqual(nombres(make_user('sin_negocio')), [])

    def test_escritura_fija_negocio_y_bloquea_ajenos(self):
        uc = {'nombre': 'Nuevo', 'businessobj_id': self.b1.pk, 'activo': 'true'}
        rsp, _, _ = IOMaction().uc_record(userobj=self.u2, files=None, qdict=self._q(uc_fields=json.dumps(uc)))
        self.assertIn('success', rsp)
        self.assertEqual(Banco.objects.get(nombre='Nuevo').businessobj_id, self.b2.pk)

        uc = {'id': self.banco.pk, 'nombre': 'Hackeado'}
        rsp, _, _ = IOMaction().uc_record(userobj=self.u2, files=None, qdict=self._q(uc_fields=json.dumps(uc)))
        self.assertIn('error', rsp)
        self.banco.refresh_from_db()
        self.assertEqual(self.banco.nombre, 'Banco A')

    def test_dtmpl_no_abre_registro_ajeno(self):
        params = {'tmpl': 'Tesoreria/BancoCreateUi.html', 'raw': 'true', 'model_app_name': 'Tesoreria',
                  'model_name': 'Banco', 'pk': self.banco.pk, 'dattrs': json.dumps({'t_guid': 'x'})}
        self.client.force_login(self.u1)
        self.assertContains(self.client.get('/io/dtmpl/', params), 'Banco A')
        self.client.force_login(self.u2)
        self.assertEqual(self.client.get('/io/dtmpl/', params).status_code, 403)


class UiRenderTest(TesoreriaBase):
    def test_pantallas_renderizan_y_su_js_es_valido(self):
        self.u1.is_superuser = True
        self.u1.save()
        for t in ['SaldosUi', 'BancoUi', 'BancoCreateUi', 'CuentaBancariaUi', 'CuentaBancariaCreateUi', 'ChequeraUi',
                  'ChequeraCreateUi', 'CajaUi', 'CajaCreateUi', 'MovimientoTesoreriaUi', 'MovimientoTesoreriaCreateUi', 'ChequeUi']:
            check_ui(self, self.u1, f'Tesoreria/{t}.html')
        check_ui(self, self.u1, 'Tesoreria/CuentaBancariaCreateUi.html', ('Tesoreria', 'CuentaBancaria'), self.cuenta.pk)
