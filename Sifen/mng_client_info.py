from tqdm import tqdm
import logging
import arrow
from etrans.models import RucQr
from sales_man.models import PedidosHeader
from finance_man.models import CPuntoventa
from etrans import rq_soap_handler, soap_schemas_xml
from datetime import datetime
rqsoap = rq_soap_handler.SoapSifen()

def daily_track_ruc_ui():
    now = arrow.get()
    lt = now.shift(weeks=-1).strftime('%Y-%m-%d')
    rucs = list(PedidosHeader.objects\
                             .filter(pedido_tipo='PD',cargado_010_fecha__range=(lt, now.strftime('%Y-%m-%d')), anulado_040=False, factura_numero__isnull=True)\
                             .values_list('puntoventaobj__rucydv', flat=True)\
                             .distinct('puntoventaobj__rucydv'))
    for ruc in rucs:
        print('Getting ruc info {}'.format(ruc.split('-')[0]))
        rsp = rqsoap.qr_ruc(ruc.split('-')[0])
    return {'exitos': 'Hecho'}    

def track_ruc_ui():
    now = arrow.get()
    lt = now.shift(weeks=-2).strftime('%Y-%m-%d')
    kps = {
        'aprobado_050':True, 
        'fake':False, 
        'extension__isnull':True
    }
    acli = list(CPuntoventa.objects.filter(pedido_tipo='PD',aprobado_050_fecha__gte=lt, **kps)\
                                    .exclude(ruc=0)\
                                    .values_list('clientecod', flat=True))
    lastsales = now.shift(years=-2).strftime('%Y-%m-%d')
    bcli = list(PedidosHeader.objects.filter(pedido_tipo='PD',aprobado_050_fecha__gte=lastsales, aprobado_050=True, anulado_040=False)\
                                .exclude(puntoventaobj__ruc='0')\
                                .distinct('puntoventaobj__ruc')\
                                .values_list('puntoventaobj__clientecod', flat=True))
    acli.extend(bcli)
    acli = set(acli)
    for pdvobj in tqdm(CPuntoventa.objects.filter(clientecod__in=acli)):
        rsp = rqsoap.qr_ruc(pdvobj.ruc, clientecod=pdvobj.clientecod)
    return {'exitos': 'Hecho'}


def update_status_ruc():
    now = datetime.now()
    tnow = now.strftime('%Y-%m-%d')
    for robj in  RucQr.objects.filter(process_date__icontains=tnow).exclude(druccons=0):
        CPuntoventa.objects.filter(ruc=robj.druccons.strip()).update(
            ruc_est= True if robj.dcodestcons == 'ACT' else False,
            ruc_est_mot = robj.ddesestcons
        )
    return {'exitos': 'Hecho'}

def clean_orders():
    now = datetime.now()
    lt = arrow.get().shift(weeks=-1).strftime('%Y-%m-%d')
    tnow = now.strftime('%Y-%m-%d')    
    for robj in  RucQr.objects.filter(process_date__icontains=tnow).exclude(druccons=0):                         
        if robj.dcodestcons  == 'ND': continue
        if robj.dcodestcons != 'ACT':
            PedidosHeader.objects.filter(
                        pedido_tipo='PD',
                        puntoventaobj__ruc=robj.druccons, 
                        aprobado_050=True, 
                        factura_numero__isnull=True, 
                        aprobado_050_fecha__gte=lt, 
                        anulado_040=False, 
                        bloqueobj__isnull=True)\
                            .update(
                                ruc_activo=False,
                                aprobado_050=False, 
                                aprobado_050_fecha=None, 
                                aprobado_050_por_gecos=None
                            )
    return {'exitos': 'Hecho'}