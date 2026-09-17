"""
Formatos de asiento por evento. Cada linea: (lado, rol, monto, glosa).
- `rol` se resuelve contra CuentaRol del negocio; si el handler informa una referencia para ese
  `monto` (ej: la cuenta bancaria del deposito) y existe un MapeoCuenta, gana la cuenta mapeada.
- `monto` es una clave del diccionario que arma el handler del evento (Contabilidad/handlers.py);
  las lineas cuyo monto es 0 no se asientan.
Se copian a FormatoAsiento/FormatoAsientoLinea del negocio, donde se pueden editar.
"""

FORMATOS = [
    {
        'evento': 'sifen.factura.emitida', 'nombre': 'Venta (factura)', 'concepto': 'Venta s/ factura {numero} - {cliente}',
        'lineas': [
            ('debe', 'clientes', 'total_credito', 'Venta a crédito'),
            ('debe', 'valores_a_depositar', 'total_contado', 'Venta al contado'),
            ('haber', 'ventas_10', 'neto_10', ''),
            ('haber', 'ventas_5', 'neto_5', ''),
            ('haber', 'ventas_exentas', 'exenta', ''),
            ('haber', 'iva_debito_10', 'iva_10', ''),
            ('haber', 'iva_debito_5', 'iva_5', ''),
        ],
    },
    {
        'evento': 'sifen.nc.emitida', 'nombre': 'Nota de crédito emitida', 'concepto': 'Nota de crédito {numero} - {cliente}',
        'lineas': [
            ('debe', 'devoluciones_ventas', 'neto', ''),
            ('debe', 'iva_debito_10', 'iva_10', ''),
            ('debe', 'iva_debito_5', 'iva_5', ''),
            ('haber', 'clientes', 'total', ''),
        ],
    },
    {
        'evento': 'cobro.recibo.aprobado', 'nombre': 'Cobro a clientes', 'concepto': 'Cobro s/ recibo {numero} - {cliente}',
        'lineas': [
            ('debe', 'valores_a_depositar', 'depositable', 'Efectivo, cheques, transferencias y tarjetas'),
            ('debe', 'retenciones', 'retencion', 'Retenciones sufridas'),
            ('haber', 'clientes', 'total', ''),
        ],
    },
    {
        'evento': 'deposito.deposito.aprobado', 'nombre': 'Depósito bancario', 'concepto': 'Depósito {numero} {origen}',
        'lineas': [
            ('debe', 'banco', 'monto', ''),
            ('haber', 'valores_a_depositar', 'monto_valores', ''),
        ],
    },
    {
        'evento': 'egreso.gasto.aprobado', 'nombre': 'Gasto', 'concepto': 'Gasto {numero} - {concepto}',
        'lineas': [
            ('debe', 'gasto_default', 'neto', ''),
            ('debe', 'iva_credito_10', 'iva_10', ''),
            ('debe', 'iva_credito_5', 'iva_5', ''),
            ('haber', 'proveedores', 'total_proveedor', ''),
            ('haber', 'caja_chica', 'total_caja_chica', 'Pagado por caja chica'),
        ],
    },
    {
        'evento': 'egreso.gasto.rendido', 'nombre': 'Rendición de gasto', 'concepto': 'Rendición gasto {numero} - {concepto}',
        'lineas': [
            ('debe', 'gasto_default', 'neto', ''),
            ('debe', 'iva_credito_10', 'iva_10', ''),
            ('debe', 'iva_credito_5', 'iva_5', ''),
            ('debe', 'banco', 'devolucion_banco', 'Devolución del sobrante'),
            ('debe', 'caja', 'devolucion_caja', 'Devolución del sobrante'),
            ('haber', 'anticipos_a_rendir', 'total_mas_devolucion', ''),
        ],
    },
    {
        'evento': 'egreso.pago.aprobado', 'nombre': 'Pago a proveedores', 'concepto': 'Pago {numero} a {beneficiario}',
        'lineas': [
            ('debe', 'proveedores', 'a_proveedores', ''),
            ('debe', 'anticipos_a_rendir', 'a_anticipos', 'Entrega de fondos a rendir'),
            ('haber', 'banco', 'total_banco', ''),
            ('haber', 'caja', 'total_caja', ''),
        ],
    },
    {
        'evento': 'egreso.transferencia.aprobado', 'nombre': 'Transferencia interna', 'concepto': 'Transferencia {numero}: {origen} -> {destino}',
        'lineas': [
            ('debe', 'banco', 'in_banco', ''),
            ('debe', 'caja', 'in_caja', ''),
            ('haber', 'banco', 'out_banco', ''),
            ('haber', 'caja', 'out_caja', ''),
        ],
    },
]

ROLES = {
    'caja': 'Caja general', 'caja_chica': 'Caja chica', 'valores_a_depositar': 'Valores cobrados pendientes de depósito',
    'banco': 'Bancos (si la cuenta bancaria no tiene mapeo propio)', 'clientes': 'Clientes',
    'anticipos_a_rendir': 'Fondos entregados a rendir', 'iva_credito_10': 'IVA crédito 10%', 'iva_credito_5': 'IVA crédito 5%',
    'retenciones': 'Retenciones sufridas', 'proveedores': 'Proveedores', 'iva_debito_10': 'IVA débito 10%',
    'iva_debito_5': 'IVA débito 5%', 'ventas_10': 'Ventas gravadas 10%', 'ventas_5': 'Ventas gravadas 5%',
    'ventas_exentas': 'Ventas exentas', 'devoluciones_ventas': 'Devoluciones/NC sobre ventas',
    'gasto_default': 'Gasto por defecto (si la categoría no tiene mapeo)', 'mercaderias': 'Mercaderías',
    'costo_ventas': 'Costo de ventas', 'pasarelas_a_cobrar': 'Pasarelas de pago a cobrar', 'ingresos_envios': 'Ingresos por envíos',
}
