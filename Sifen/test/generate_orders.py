from random import randint
import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen
importlib.reload(mng_sifen)
#Instancias la clase que genera la solicitud

msifen = mng_sifen.MSifen()

tnow = datetime.now()
#La mayoria de los campos son autexplicativos, no obstante en la firma del method hay una breve descripcion de parametros
clobj = Clientes.objects.using('fl').get(clientecodigo=11151)
doc_total = 175000
artobj = Producto.objects.all().last()
ext_link = 1900
#Prueba DLC
msifen.crear_proforma(
    **{
    "userobj": "admin",
    "clientecodigo": 23600,
    "expedicion": 1,
    "source": "DLC",
    "ext_link": 355,
    "doc_moneda": "GS",
    "doc_fecha": "2024-11-06",
    "doc_tipo": "FE",
    "doc_op": "VTA",
    "doc_estado": "CONCLUIDO",
    "doc_total": 288900.0,
    "details": [
        {
            "prod_cod": 5,
            "prod_descripcion": "SERVICIO DE FLETE AEREO INTERNACIONAL DDP",
            "prod_unidad_medida": 77,
            "prod_unidad_medida_desc": "UNI",
            "precio_unitario": 170662.5,
            "precio_unitario_siniva": 1,
            "cantidad_devolucion": 0,
            "cantidad": 1.7,
            "bonifica": False,
            "descuento": 0,
            "per_descuento": 0
        }
    ],
    "pagos": [
        {
            "tipo_cod": 1,
            "monto": 288900.0
        }
    ],
    "doc_redondeo": 13.0
}
)
#Factura
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="DLC",
    ext_link=ext_link,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='FE',
    doc_op='VTA',
    doc_estado='CONCLUIDO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link=None,
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ],
    pagos=[
        {
            'tipo_cod': 1,
            'monto': 120000
        },
        {
            'tipo_cod': 3,
            'tarjeta_denominacion_cod': 1,
            'tarjeta_procesadora': 'BANCARD',
            'tarjeta_procesadora_ruc': 80013884,
            'tarjeta_procesadora_ruc_dv': 8,
            'tarjeta_procesamiento': 1,
            'tarjeta_autorizacion_cod': 12345678910,
            'tarjeta_titular': 'PETER',
            'tarjeta_numero': 1234,
            'monto': 120000
        }
    ]
)

#NC
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="NC",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='NC',
    doc_op='NC',
    doc_estado='DESCUENTO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link='bb90bb2c-3d96-4ee7-911d-26ea0132abeb',
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)

#ND
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="ND",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='ND',
    doc_op='ND',
    doc_estado='Aumento',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link='bb90bb2c-3d96-4ee7-911d-26ea0132abeb',
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)
#Auto Factura
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="AF",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='AF',
    doc_op='VTA',
    doc_estado='CONCLUIDO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link=None,
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)

#Generar Factura con Voucher

#La mayoria de los campos son autexplicativos, no obstante en la firma del method hay una breve descripcion de parametros
from random import randint
import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen
importlib.reload(mng_sifen)
msifen = mng_sifen.MSifen()
tnow = datetime.now()
clobj = Clientes.objects.using('fl').get(clientecodigo=11151)
doc_total = 175000
artobj = Producto.objects.all().exclude(prod_cod=130).last()
ext_link = randint(2000, 3000)

msifen.crear_proforma(
    **{
        "userobj": User.objects.last(),
        "clientecodigo": 23600,
        "expedicion": 1,
        "source": "DLC",
        "ext_link": ext_link,
        "doc_moneda": "GS",
        "doc_fecha": "2024-10-01",
        "doc_tipo": "FE",
        "doc_op": "VTA",
        "doc_estado": "CONCLUIDO",
        "doc_total": 125200.0,
        "details": [
            {
                "prod_cod": 5,
                "prod_descripcion": "SERVICIO DE FLETE AEREO INTERNACIONAL DDP",
                "prod_unidad_medida": 77,
                "prod_unidad_medida_desc": "UNI",
                "precio_unitario": 158526.5,
                "precio_unitario_siniva": 1,
                "cantidad_devolucion": 0,
                "cantidad": 0.79,
                "bonifica": False,
                "descuento": 0,
                "per_descuento": 0
            }
        ],
        "pagos": [
            {
                "tipo_cod": 1,
                "monto": 125200.0
            }
        ],
        "doc_redondeo": 0.0,
        "doc_voucher": 37925.0
    }
)

msifen.crear_proforma(
    User.objects.last(),
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="DLC",
    ext_link=ext_link,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    
    doc_tipo='FE',
    doc_op='VTA',
    doc_estado='CONCLUIDO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link=None,
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.prod_cod,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ],
    pagos=[
        {
            'tipo_cod': 1,
            'monto': 120000
        },
        {
            'tipo_cod': 3,
            'tarjeta_denominacion_cod': 1,
            'tarjeta_procesadora': 'BANCARD',
            'tarjeta_procesadora_ruc': 80013884,
            'tarjeta_procesadora_ruc_dv': 8,
            'tarjeta_procesamiento': 1,
            'tarjeta_autorizacion_cod': 12345678910,
            'tarjeta_titular': 'PETER',
            'tarjeta_numero': 1234,
            'monto': 120000
        }
    ],
    doc_redondeo=30,
    doc_voucher=10000
)


msifen.crear_proforma(
    **{
    "userobj": "admin",
    "clientecodigo": 23600,
    "expedicion": 1,
    "source": "DLC",
    "ext_link": 355,
    "doc_moneda": "GS",
    "doc_fecha": "2024-11-06",
    "doc_tipo": "FE",
    "doc_op": "VTA",
    "doc_estado": "CONCLUIDO",
    "doc_total": 288900.0,
    "details": [
        {
            "prod_cod": 5,
            "prod_descripcion": "SERVICIO DE FLETE AEREO INTERNACIONAL DDP",
            "prod_unidad_medida": 77,
            "prod_unidad_medida_desc": "UNI",
            "precio_unitario": 170662.5,
            "precio_unitario_siniva": 1,
            "cantidad_devolucion": 0,
            "cantidad": 1.7,
            "bonifica": False,
            "descuento": 0,
            "per_descuento": 0
        }
    ],
    "pagos": [
        {
            "tipo_cod": 1,
            "monto": 288900.0
        }
    ],
    "doc_redondeo": 13.0
}
)
#Factura
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="DLC",
    ext_link=ext_link,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='FE',
    doc_op='VTA',
    doc_estado='CONCLUIDO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link=None,
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ],
    pagos=[
        {
            'tipo_cod': 1,
            'monto': 120000
        },
        {
            'tipo_cod': 3,
            'tarjeta_denominacion_cod': 1,
            'tarjeta_procesadora': 'BANCARD',
            'tarjeta_procesadora_ruc': 80013884,
            'tarjeta_procesadora_ruc_dv': 8,
            'tarjeta_procesamiento': 1,
            'tarjeta_autorizacion_cod': 12345678910,
            'tarjeta_titular': 'PETER',
            'tarjeta_numero': 1234,
            'monto': 120000
        }
    ]
)

#NC
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="NC",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='NC',
    doc_op='NC',
    doc_estado='DESCUENTO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link='bb90bb2c-3d96-4ee7-911d-26ea0132abeb',
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)

#ND
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="ND",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='ND',
    doc_op='ND',
    doc_estado='Aumento',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link='bb90bb2c-3d96-4ee7-911d-26ea0132abeb',
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)
#Auto Factura
msifen.crear_proforma(
    clientecodigo=clobj.clientecodigo,
    expedicion=1, #La caja donde se imprimi
    source="AF",
    ext_link=1298,
    doc_moneda='GS',
    doc_fecha=tnow.strftime('%Y-%m-%d'),
    doc_tipo='AF',
    doc_op='VTA',
    doc_estado='CONCLUIDO',
    doc_vencimiento=arrow.get(tnow).shift(days=16).strftime('%Y-%m-%d'),
    doc_total=doc_total,
    doc_iva=doc_total - (doc_total / 1.1),
    doc_exenta=0,
    doc_g10=doc_total,
    doc_i10=doc_total - (doc_total / 1.1),
    doc_g5=0,
    doc_i5=0,
    doc_descuento=0,
    doc_per_descuento=0,
    doc_tipo_ope=1, #iTipTra 1 = Venta de mercaderia
    doc_tipo_imp=1,  #iTImp Tipo de impuesto 1 = IVA
    op_pres_cod=1, #iIndPres como y donde se vendio
    cre_tipo_cod=1, #iCondOpe condicion de la operacion Contado 2 = Credito
    doc_tipo_pago_cod=1, #iTiPago Efectivo, Cheque, TC, TD, VALE ...etc
    #SOLO EN OPERACIONES DE CREDITO E640-E649
    #doc_cre_cond=1 #iCondCred 1= Plazo 2 = Cuota
    #doc_cre_plazo='30 dias' # dPlazoCre
    #doc_cre_cuota='12' #dCuotas
    #doc_cre_entrega_inicial=1200000 #dMonEnt
    pdv_pais_cod='PRY',
    pdv_pais='Paraguay',
    #No es obligatorio, pero si hay enviar, segun los modelos en la APP Sifen
    pdv_direccion_entrega=None,
    pdv_dir_calle_sec=None,
    pdv_direccion_comple=None,
    pdv_numero_casa=0,
    pdv_numero_casa_entrega=0,
    pdv_dpto_cod=0,
    pdv_dpto_nombre=None,
    pdv_distrito_cod=0,
    pdv_distrito_nombre=None,
    pdv_ciudad_cod=0,
    pdv_ciudad_nombre=None,
    #Solo en caso de operaciones que requieren un documento asociado
    doc_loop_link=None,
    details=[
        {
            #Referencia SOFT a la table Producto de FL_Masters
            'prod_cod': artobj.pk,
            'prod_descripcion': artobj.descripcion,
            'prod_unidad_medida': artobj.medidaobj.medida_cod,
            'prod_unidad_medida_desc': artobj.medidaobj.medida,
            'prod_pais_origen': 0,
            'prod_pais_origen_desc': None,
            'prod_lote': None,
            'prod_vencimiento': None,
            'porcentaje_iva': 10,
            'precio_unitario': doc_total,
            'precio_unitario_siniva': doc_total / 1.1,
            'cantidad': 1,
            'cantidad_devolucion': 0,
            'exenta': 0,
            'iva_5': 0,
            'gravada_5': 0,
            'iva_10': doc_total - (doc_total / 1.1),
            'gravada_10': doc_total,
            'afecto': doc_total,
            'per_tipo_iva': 0, #dPropIVA Porcentaje del gravado, cuando en un mismo ite existe g5 y exenta o g10 y exenta
            'bonifica': False, #Si es un descuento
            'descuento': 0,
            'per_descuento': 0,
            'volumen': 0,
            'peso': 0,
            'observacion': 'TEST'
        }
    ]
)

#Generar Factura con Voucher

#La mayoria de los campos son autexplicativos, no obstante en la firma del method hay una breve descripcion de parametros
from random import randint
import importlib
import arrow
from datetime import datetime
from apps.FL_Structure.models import Clientes
from apps.FL_Masters.models import Producto
from Sifen import mng_sifen
importlib.reload(mng_sifen)
msifen = mng_sifen.MSifen()
tnow = datetime.now()
clobj = Clientes.objects.using('fl').get(clientecodigo=11151)
doc_total = 175000
artobj = Producto.objects.all().exclude(prod_cod=130).last()
ext_link = randint(2000, 3000)

msifen.crear_proforma(
    **{
        "userobj": User.objects.last(),
        'clientecodigo': 23600, 
        'expedicion': 1, 
        'source': 'PRESENCIAL', 
        'ext_link': 654, 
        'doc_moneda': 'GS', 
        'doc_fecha': '2025-05-12', 
        'doc_tipo': 'FE', 
        'doc_op': 'VTA', 
        'doc_estado': 'CONCLUIDO', 
        'doc_total': 18191.0, 
        "details": [
            { 'prod_cod': 5, 
              'prod_descripcion': 'SERVICIO DE FLETE AEREO INTERNACIONAL DDP', 
              'prod_unidad_medida': 77, 
              'prod_unidad_medida_desc': 'UNI', 
              'precio_unitario': 18200, 
              'cantidad': 1, 
              'peso': 0.1, 
              'bonifica': False, 
              'descuento': 0, 
              'per_descuento': 0, 
              'not_recal': True 
              }
        ],
        "pagos": [
            {
                "tipo_cod": 1,
                "monto": 125200.0
            }
        ],
        "doc_redondeo": -9,
        'cre_tipo_cod': 1
    }
)


