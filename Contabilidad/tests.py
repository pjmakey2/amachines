import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from Contabilidad.mng_contabilidad import MContabilidad
from Contabilidad.models import Asiento, CuentaRol, FormatoAsiento, MapeoCuenta, PlanCuenta
from Deposito.mng_deposito import MDeposito
from Deposito.models import Deposito
from Egreso.mng_egreso import MEgreso
from Egreso.models import CategoriaGasto, Gasto, PagoProveedor, Proveedor, TransferenciaInterna
from OptsIO import events
from OptsIO.models import BusinessEvent
from OptsIO.testing import make_business, make_user
from Tesoreria.models import Banco, Caja, CuentaBancaria


class ContaBase(TestCase):
    def setUp(self):
        self.b = make_business()
        self.u = make_user('admin', self.b, superuser=True)
        self.mc = MContabilidad()
        rsp = self.mc.aplicar_plantilla(userobj=self.u, qdict={'plantilla': 'comercial', 'fecha_inicio': '2026-01-01'})
        self.assertIn('success', rsp, rsp)
        banco = Banco.objects.create(businessobj=self.b, nombre='Banco A')
        self.cuenta = CuentaBancaria.objects.create(businessobj=self.b, bancoobj=banco, numero='1', saldo_inicial=50_000_000)
        self.chica = Caja.objects.create(businessobj=self.b, nombre='Chica', tipo='chica', tope=1_000_000)
        self.prov = Proveedor.objects.create(businessobj=self.b, ruc='800', nombre='Proveedor SA')
        self.cat = CategoriaGasto.objects.create(businessobj=self.b, nombre='Alquiler')

    def cta(self, codigo):
        return PlanCuenta.objects.get(businessobj=self.b, codigo=codigo)

    def procesar(self):
        for e in BusinessEvent.objects.exclude(status='done').order_by('pk'):
            r = events.process_event(e.pk)
            self.assertEqual(r['status'], 'done', r)

    def lineas(self, asiento):
        return sorted((d.cuentaobj.codigo, int(d.debe), int(d.haber)) for d in asiento.detalles.all())

    def asientos_de(self, obj):
        return list(Asiento.objects.filter(origen_model=obj._meta.model_name, origen_id=obj.pk).order_by('pk'))

    def call(self, metodo, **fields):
        rsp = metodo(userobj=self.u, qdict={'uc_fields': json.dumps(fields)})[0]
        self.assertIn('success', rsp, rsp)
        return rsp['record_id']

    def aprobar(self, obj):
        obj.avanzar(self.u)
        obj.avanzar(self.u)
        return obj


class PlantillaTest(ContaBase):
    def test_plantilla_idempotente_y_extensible(self):
        n = PlanCuenta.objects.filter(businessobj=self.b).count()
        self.assertFalse(self.cta('1.1.01').imputable)
        self.assertTrue(self.cta('1.1.01.04').imputable)
        self.assertEqual(self.cta('1.1.01.04').padreobj, self.cta('1.1.01'))
        self.assertEqual(CuentaRol.objects.get(businessobj=self.b, rol='clientes').cuentaobj.codigo, '1.1.02.01')
        self.mc.aplicar_plantilla(userobj=self.u, qdict={'plantilla': 'comercial'})
        self.assertEqual(PlanCuenta.objects.filter(businessobj=self.b).count(), n)
        self.mc.aplicar_plantilla(userobj=self.u, qdict={'plantilla': 'ecommerce'})
        self.assertEqual(PlanCuenta.objects.filter(businessobj=self.b).count(), n + 4)

        rsp = self.mc.create_cuenta(userobj=self.u, qdict={'uc_fields': json.dumps({'codigo': '6.1.13', 'nombre': 'Limpieza'})})[0]
        self.assertIn('success', rsp, rsp)
        self.assertEqual((self.cta('6.1.13').tipo, self.cta('6.1.13').nivel, self.cta('6.1.13').padreobj.codigo), ('gasto', 3, '6.1'))
        # abrir subcuentas de Bancos exige reasignar el rol primero
        rsp = self.mc.create_cuenta(userobj=self.u, qdict={'uc_fields': json.dumps({'codigo': '1.1.01.04.01', 'nombre': 'Banco A cta 1'})})[0]
        self.assertIn('rol', rsp['error'])


class CicloContableTest(ContaBase):
    def test_egresos_generan_asientos_y_reversos(self):
        MapeoCuenta.objects.create(businessobj=self.b, tipo='categoria_gasto', ref_id=self.cat.pk, cuentaobj=self.cta('6.1.04'))
        me = MEgreso()
        g = self.aprobar(Gasto.objects.get(pk=self.call(
            me.create_gasto, tipo='comun', fecha='2026-09-01', proveedorobj_id=self.prov.pk, categoriaobj_id=self.cat.pk,
            concepto='Alquiler setiembre', gravada_10='1100000', exenta='50000', factura_numero='001-001-0000009')))
        self.procesar()
        a, = self.asientos_de(g)
        self.assertEqual((a.estado, a.origen, a.concepto), ('aprobado', 'automatico', 'Gasto 1 - Alquiler setiembre'))
        self.assertEqual(self.lineas(a), [('1.1.02.03', 100000, 0), ('2.1.01.01', 0, 1150000), ('6.1.04', 1050000, 0)])

        pago = self.aprobar(PagoProveedor.objects.get(pk=self.call(
            me.create_pago, fecha='2026-09-05', medio='transferencia', cuentaobj_id=self.cuenta.pk,
            detalles=[{'gasto_id': g.pk, 'monto': '1150000'}])))
        self.procesar()
        self.assertEqual(self.lineas(self.asientos_de(pago)[0]), [('1.1.01.04', 0, 1150000), ('2.1.01.01', 1150000, 0)])

        pago.anular(self.u, 'error')
        self.procesar()
        self.procesar()
        original, rev = self.asientos_de(pago)
        self.assertEqual((rev.origen, rev.reversaobj_id), ('reverso', original.pk))
        self.assertEqual(self.lineas(rev), [('1.1.01.04', 1150000, 0), ('2.1.01.01', 0, 1150000)])

    def test_caja_chica_a_rendir_y_transferencia(self):
        me = MEgreso()
        tr = self.aprobar(TransferenciaInterna.objects.get(pk=self.call(
            me.create_transferencia, fecha='2026-09-01', monto='800000', origen_cuentaobj_id=self.cuenta.pk, destino_cajaobj_id=self.chica.pk)))
        MapeoCuenta.objects.create(businessobj=self.b, tipo='caja', ref_id=self.chica.pk, cuentaobj=self.cta('1.1.01.02'))
        chico = self.aprobar(Gasto.objects.get(pk=self.call(
            me.create_gasto, tipo='caja_chica', fecha='2026-09-02', cajaobj_id=self.chica.pk, beneficiario='Ferretería',
            categoriaobj_id=self.cat.pk, concepto='Focos', gravada_10='55000')))
        rendir = self.aprobar(Gasto.objects.get(pk=self.call(
            me.create_gasto, tipo='a_rendir', fecha='2026-09-03', beneficiario='Juan', categoriaobj_id=self.cat.pk,
            concepto='Viaje', presupuesto_monto='500000')))
        entrega = self.aprobar(PagoProveedor.objects.get(pk=self.call(
            me.create_pago, fecha='2026-09-03', medio='transferencia', cuentaobj_id=self.cuenta.pk,
            detalles=[{'gasto_id': rendir.pk, 'monto': '500000'}])))
        self.call(me.rendir_gasto, id=rendir.pk, factura_numero='001', gravada_10='440000', devolucion_cuentaobj_id=self.cuenta.pk)
        self.procesar()

        self.assertEqual(self.lineas(self.asientos_de(tr)[0]), [('1.1.01.02', 800000, 0), ('1.1.01.04', 0, 800000)])
        self.assertEqual(self.lineas(self.asientos_de(chico)[0]), [('1.1.01.02', 0, 55000), ('1.1.02.03', 5000, 0), ('6.1.99', 50000, 0)])
        self.assertEqual(self.lineas(self.asientos_de(entrega)[0]), [('1.1.01.04', 0, 500000), ('1.1.02.02', 500000, 0)])
        rendicion, = self.asientos_de(rendir)  # al aprobarse no se asienta; solo al rendirse
        self.assertEqual(self.lineas(rendicion), [('1.1.01.04', 60000, 0), ('1.1.02.02', 0, 500000), ('1.1.02.03', 40000, 0), ('6.1.99', 400000, 0)])

        # Reportes
        rpt = self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'resultados', 'desde': '2026-09-01', 'hasta': '2026-09-30'})
        self.assertEqual(rpt['resumen'], {'ingresos': 0.0, 'costos': 0.0, 'gastos': 450000.0, 'resultado': -450000.0})
        ss = self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'sumas_saldos', 'hasta': '2026-09-30'})
        self.assertEqual(ss['filas'][-1]['celdas'][2], ss['filas'][-1]['celdas'][3])
        mayor = self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'mayor', 'hasta': '2026-09-30', 'cuenta_id': self.cta('1.1.02.02').pk})
        self.assertEqual(mayor['filas'][-1]['celdas'][-1], 0.0)  # anticipos a rendir queda en cero
        for r in ('diario', 'balance'):
            self.assertTrue(self.mc.get_reporte(userobj=self.u, qdict={'reporte': r, 'hasta': '2026-09-30'})['filas'])
        self.assertIn('.xlsx', self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'diario', 'hasta': '2026-09-30', 'excel': '1'})['excel_file'])

    def test_cobro_deposito_y_venta(self):
        ev = events.emit('cobro.recibo.aprobado', User.objects.get(username='admin'), business=self.b, payload={
            'numero': 15, 'fecha': '2026-09-10', 'moneda': 'GS', 'cliente': 'Cliente SA', 'total': '1500000',
            'metodos': {'efectivo': '1400000', 'retencion': '100000'}})
        self.procesar()
        cobro = Asiento.objects.get(evento='cobro.recibo.aprobado')
        self.assertEqual(self.lineas(cobro), [('1.1.01.03', 1400000, 0), ('1.1.02.01', 0, 1500000), ('1.1.02.05', 100000, 0)])
        dep = Deposito.objects.get()
        self.call(MDeposito().create_deposito, id=dep.pk, fecha='2026-09-11', cuentaobj_id=self.cuenta.pk, boleta_numero='B1')
        self.aprobar(dep)
        self.procesar()
        self.assertEqual(self.lineas(self.asientos_de(dep)[0]), [('1.1.01.03', 0, 1400000), ('1.1.01.04', 1400000, 0)])

        doc = SimpleNamespace(doc_tipo='FE', doc_moneda='GS', doc_fecha=date(2026, 9, 12), tasa_cambio=1, doc_cre_tipo_cod=2,
                              doc_establecimiento=1, doc_expedicion=1, doc_numero=77, pdv_nombrefactura='Cliente SA',
                              get_total_gravada_10=lambda: Decimal('1100000'), get_total_gravada_5=lambda: Decimal('210000'),
                              get_total_exenta=lambda: Decimal('40000'), get_ivas_10_master=lambda: Decimal('100000'),
                              get_ivas_5_master=lambda: Decimal('10000'))
        venta_ev = events.emit('sifen.documento.aprobado', User.objects.get(username='admin'), business=self.b, key_suffix='venta')
        with mock.patch('Contabilidad.handlers.DocumentHeader.objects.get', return_value=doc):
            self.procesar()
        venta = Asiento.objects.get(evento='sifen.factura.emitida')
        self.assertEqual(venta.concepto, 'Venta s/ factura 001-001-0000077 - Cliente SA')
        self.assertEqual(self.lineas(venta), [('1.1.02.01', 1350000, 0), ('2.1.02.01', 0, 100000), ('2.1.02.02', 0, 10000),
                                             ('4.1.01.01', 0, 1000000), ('4.1.01.02', 0, 200000), ('4.1.01.03', 0, 40000)])

    def test_sin_configuracion_no_asienta_y_reproceso_recupera(self):
        FormatoAsiento.objects.filter(businessobj=self.b).update(activo=False)
        g = self.aprobar(Gasto.objects.get(pk=self.call(
            MEgreso().create_gasto, tipo='comun', fecha='2026-09-01', proveedorobj_id=self.prov.pk, categoriaobj_id=self.cat.pk,
            concepto='Internet', gravada_10='110000', factura_numero='1')))
        self.procesar()
        self.assertEqual(self.asientos_de(g), [])
        FormatoAsiento.objects.filter(businessobj=self.b).update(activo=True)
        rsp = self.mc.reprocesar_eventos(userobj=self.u, qdict={})
        self.assertIn('1 asiento(s) generado(s)', rsp['success'])
        self.assertEqual(len(self.asientos_de(g)), 1)
        self.assertIn('0 asiento(s)', self.mc.reprocesar_eventos(userobj=self.u, qdict={})['success'])

    def test_asiento_manual_balanceado(self):
        lineas = [{'cuenta_id': self.cta('1.1.01.04').pk, 'debe': '1000000'}, {'cuenta_id': self.cta('3.1.01').pk, 'haber': '900000'}]
        rsp = self.mc.create_asiento(userobj=self.u, qdict={'uc_fields': json.dumps({'fecha': '2026-09-01', 'concepto': 'Aporte', 'lineas': lineas})})[0]
        self.assertIn('no balancea', rsp['error'])
        lineas[1]['haber'] = '1000000'
        a = Asiento.objects.get(pk=self.call(self.mc.create_asiento, fecha='2026-09-01', concepto='Aporte de capital', lineas=lineas))
        self.assertEqual((a.origen, a.estado), ('manual', 'cargado'))
        self.assertEqual(self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'diario', 'hasta': '2026-12-31'})['filas'], [])
        self.aprobar(a)
        self.assertEqual(len(self.mc.get_reporte(userobj=self.u, qdict={'reporte': 'diario', 'hasta': '2026-12-31'})['filas']), 3)
