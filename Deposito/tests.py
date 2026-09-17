import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from Deposito.handlers import generar_depositos_de_cobro
from Deposito.mng_deposito import MDeposito
from Deposito.models import Deposito
from OptsIO import events
from OptsIO.testing import check_ui, grid_records, make_business, make_user
from Tesoreria.models import Banco, CuentaBancaria


class DepositoTest(TestCase):
    def setUp(self):
        self.b = make_business()
        self.u = make_user('admin', self.b, superuser=True)
        banco = Banco.objects.create(businessobj=self.b, nombre='Banco A')
        self.cuenta = CuentaBancaria.objects.create(businessobj=self.b, bancoobj=banco, numero='1')

    def _evento_cobro(self):
        # El source real es Sifen.DocumentRecibo; para el handler solo importa el id y el payload
        return events.emit('cobro.recibo.aprobado', User.objects.get(username='admin'), business=self.b, payload={
            'numero': 15, 'fecha': '2026-09-10', 'moneda': 'GS', 'cliente': 'Cliente SA', 'total': '1500000',
            'metodos': {'efectivo': '1000000', 'cheque': '400000', 'transferencia': '0', 'tarjeta': '0', 'retencion': '100000'}})

    def test_cobro_genera_depositos_una_sola_vez(self):
        event = self._evento_cobro()
        self.assertEqual(events.get_handlers('cobro.recibo.aprobado'), ['Deposito.handlers.generar_depositos_de_cobro'])
        self.assertEqual(events.process_event(event.pk)['status'], 'done')
        generar_depositos_de_cobro(event)  # re-ejecucion directa: no duplica
        deps = list(Deposito.objects.order_by('tipo').values_list('tipo', 'monto', 'estado', 'automatico', 'cuentaobj_id'))
        self.assertEqual(deps, [('cheque', Decimal('400000'), 'cargado', True, self.cuenta.pk),
                                ('efectivo', Decimal('1000000'), 'cargado', True, self.cuenta.pk)])

    def test_acreditacion_al_aprobar_y_reverso(self):
        events.process_event(self._evento_cobro().pk)
        dep = Deposito.objects.get(tipo='efectivo')
        self.assertIn('boleta', dep.validar_avance(self.u))
        rsp = MDeposito().create_deposito(userobj=self.u, qdict={'uc_fields': json.dumps(
            {'id': dep.pk, 'fecha': '2026-09-11', 'cuentaobj_id': self.cuenta.pk, 'boleta_numero': 'B-77', 'monto': '5', 'tipo': 'cheque'})})[0]
        self.assertIn('success', rsp, rsp)
        dep.refresh_from_db()
        self.assertEqual((dep.monto, dep.tipo), (Decimal('1000000'), 'efectivo'))  # automatico: monto/tipo intactos
        dep.avanzar(self.u)
        self.assertEqual(self.cuenta.get_saldo(), 0)
        dep.avanzar(self.u)
        self.assertEqual(self.cuenta.get_saldo(), 1000000)
        dep.anular(self.u, 'boleta equivocada')
        self.assertEqual(self.cuenta.get_saldo(), 0)

    def test_deposito_manual_de_cheques_y_ui(self):
        datos = {'fecha': '2026-09-11', 'tipo': 'cheque', 'monto': '300000', 'cuentaobj_id': self.cuenta.pk, 'boleta_numero': 'B-1',
                 'cheques': [{'banco': 'X', 'numero': '1', 'monto': '100000'}, {'banco': 'Y', 'numero': '2', 'monto': '150000'}]}
        rsp = MDeposito().create_deposito(userobj=self.u, qdict={'uc_fields': json.dumps(datos)})[0]
        self.assertIn('no coincide', rsp['error'])
        datos['cheques'][1]['monto'] = '200000'
        rsp = MDeposito().create_deposito(userobj=self.u, qdict={'uc_fields': json.dumps(datos)})[0]
        dep = Deposito.objects.get(pk=rsp['record_id'])
        self.assertEqual(dep.cheques.count(), 2)
        check_ui(self, self.u, 'Deposito/DepositoUi.html')
        check_ui(self, self.u, 'Deposito/DepositoCreateUi.html')
        check_ui(self, self.u, 'Deposito/DepositoCreateUi.html', ('Deposito', 'Deposito'), dep.pk)
        filas = grid_records(self, self.u, 'Deposito', 'Deposito', ['id', 'estado'], methods=['get_cuenta'],
                             mquery=[{'field': 'estado', 'value': 'cargado|verificado'}, {'field': 'anulado', 'value': False}])
        self.assertEqual(len(filas), 1)
