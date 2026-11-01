from django.test import SimpleTestCase

from Contabilidad import codigos


class CodigosTest(SimpleTestCase):
    def test_normalizar_padre_nivel_y_corto(self):
        f = '3.3.3.3.3.3'
        self.assertEqual(codigos.normalizar('3', f), '003.000.000.000.000.000')
        self.assertEqual(codigos.normalizar('3.1.3', f), '003.001.003.000.000.000')
        self.assertEqual(codigos.normalizar('003.001.003.000.000.000', f), '003.001.003.000.000.000')
        self.assertEqual(codigos.normalizar('1.01', '1.2.2.2.2.3'), '1.01.00.00.00.000')
        self.assertEqual(codigos.nivel('003.001.003.000.000.000'), 3)
        self.assertEqual(codigos.padre('003.001.003.000.000.000'), '003.001.000.000.000.000')
        self.assertIsNone(codigos.padre('003.000.000.000.000.000'))
        self.assertEqual(codigos.corto('003.001.003.000.000.000'), '3.1.3')
        for malo in ('', 'a.b', '0.1', '3.0.1', '3.1.1.1.1.1.1', '3.1000'):
            with self.assertRaises(ValueError, msg=malo):
                codigos.normalizar(malo, f)
        self.assertEqual(codigos.validar_formato('3.3.3.3.3.3'), '')
        self.assertTrue(codigos.validar_formato('3'))
        self.assertTrue(codigos.validar_formato('3.x'))
