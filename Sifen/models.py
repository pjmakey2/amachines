from itertools import zip_longest
import math
from django.db import models
from decimal import Decimal
from num2words import num2words
from OptsIO.io_serial import dict_int_none
from OptsIO.io_formats import IoF
import uuid
from django.db.models import Sum

iof = IoF()

# Create your models here.
class Geografias(models.Model):
    continente= models.CharField(max_length=500)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.continente

class AreasPoliticas(models.Model):
    geografia = models.ForeignKey(Geografias,on_delete=models.CASCADE)
    area_politica = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.area_politica

class Paises(models.Model):
    nombre_pais = models.CharField(max_length=500)
    codigo_pais = models.IntegerField(default=0)
    alfa_uno = models.CharField(max_length=6, default='ND')
    alfa_dos = models.CharField(max_length=6, default='ND')
    areapolitica = models.ForeignKey(AreasPoliticas,on_delete=models.CASCADE, null=True)
    adjetivo = models.CharField(max_length=500)
    nacionalidad = models.CharField(max_length=500)
    habitante = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)


    class Meta:
        ordering = ['nombre_pais']

    def __unicode__(self):
        return '%s - %s' % (self.nombre_pais, self.id)

class Departamentos(models.Model):
    fuente = models.CharField(max_length=6, default='ND')
    pais = models.ForeignKey(Paises,on_delete=models.CASCADE)
    codigo_departamento = models.IntegerField(default=0)
    nombre_departamento = models.CharField(max_length=500)
    habitante = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.nombre_departamento

class Distrito(models.Model):
    fuente = models.CharField(max_length=6, default='ND')    
    dptoobj = models.ForeignKey(Departamentos,on_delete=models.CASCADE)
    codigo_distrito = models.IntegerField(default=0)
    nombre_distrito = models.CharField(max_length=500)
    habitante = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.descripcion

class Ciudades(models.Model):
    fuente = models.CharField(max_length=6, default='ND')    
    distritoobj = models.ForeignKey(Distrito, null=True,on_delete=models.CASCADE)
    codigo_ciudad = models.IntegerField(default=0)
    nombre_ciudad= models.CharField(max_length=500)
    habitante = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.nombre_ciudad

class Barrios(models.Model):
    fuente = models.CharField(max_length=6, default='ND')    
    ciudad = models.ForeignKey(Ciudades,on_delete=models.CASCADE)
    codigo_barrio = models.IntegerField(default=0)
    nombre_barrio = models.CharField(max_length=500)
    habitante = models.CharField(max_length=500, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    comentarios = models.TextField(max_length=1500, null=True, blank=True)

    def __unicode__(self):
        return self.nombre_barrio


class ActividadEconomica(models.Model):
    codigo_actividad = models.CharField(max_length=120)
    nombre_actividad = models.CharField(max_length=200)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)    

class TipoContribuyente(models.Model):
    codigo = models.IntegerField(default=0)
    tipo = models.CharField(max_length=30)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)    


class Business(models.Model):
    name = models.CharField(max_length=120)
    abbr = models.CharField(max_length=60)
    ruc = models.CharField(max_length=60, unique=True)
    ruc_dv = models.IntegerField(default=0)
    contribuyenteobj = models.ForeignKey(TipoContribuyente, on_delete=models.CASCADE)
    nombrefactura = models.CharField(max_length=120)
    nombrefantasia = models.CharField(max_length=120)
    numero_casa = models.IntegerField(default=0)
    direccion = models.CharField(max_length=200, null=True)
    dir_comp_uno = models.CharField(max_length=200, null=True)
    dir_comp_dos = models.CharField(max_length=200, null=True)
    ciudadobj = models.ForeignKey(Ciudades, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=40,default=0)
    celular = models.CharField(max_length=40,default=0)
    correo = models.CharField(max_length=120)
    denominacion = models.CharField(max_length=120)
    logo = models.FileField(upload_to='business', max_length=500, null=True)
    favicon = models.FileField(upload_to='business/favicon', max_length=500, null=True, blank=True)
    logo_invoice = models.FileField(upload_to='business/invoice', max_length=500, null=True, blank=True)
    css_invoice = models.FileField(upload_to='business/css', max_length=500, null=True, blank=True)
    css_invoice_content = models.TextField(null=True, blank=True, help_text='Contenido CSS para facturas (se auto-genera del archivo)')
    actividadecoobj = models.ForeignKey(ActividadEconomica, on_delete=models.CASCADE)
    web = models.CharField(max_length=120, null=True)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)        

class Etimbrado(models.Model):
    ruc = models.CharField(max_length=120)
    dv = models.CharField(max_length=30)
    timbrado = models.CharField(max_length=120)
    inicio = models.DateField()
    serie = models.CharField(max_length=120)
    fcsc = models.CharField(max_length=120)
    scsc = models.CharField(max_length=120)    
    vencimiento = models.DateField(default='2029-01-01')
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)    

class Eestablecimiento(models.Model):
    timbradoobj = models.ForeignKey(Etimbrado, on_delete=models.CASCADE)
    establecimiento = models.IntegerField()
    expedicion = models.JSONField()
    direccion = models.CharField(max_length=200, null=True)
    numero_casa = models.IntegerField(default=0)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)

class Enumbers(models.Model):
    expobj = models.ForeignKey(Eestablecimiento, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=120)
    serie = models.CharField(max_length=20)
    numero = models.BigIntegerField()
    estado = models.CharField(max_length=120)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    aprobado_fecha = models.DateTimeField(null=True)
    aprobado_usuario = models.CharField(max_length=120, null=True)

class SendBulk(models.Model):
    zipfname =  models.TextField()
    xmlfname =  models.CharField(max_length=400)
    soapfname = models.CharField(max_length=400)
    cargado_fecha = models.DateTimeField(null=True)

class SendBulkDetail(models.Model):
    sendbulkobj = models.ForeignKey(SendBulk, on_delete=models.CASCADE)
    xmlfile = models.CharField(max_length=400)
    cargado_fecha = models.DateTimeField(null=True)

class CdcTrack(models.Model):
    cdc = models.CharField(max_length=500)
    metodo = models.CharField(max_length=60)
    header_msg = models.CharField(max_length=500)
    cod_rsp = models.IntegerField()
    state = models.CharField(max_length=500)
    dfecproc = models.DateTimeField()
    msg = models.CharField(max_length=500)
    transaccion = models.CharField(max_length=60)
    qr_link = models.TextField(default='ND')
    worker_done = models.BooleanField(default=False)

class RucQr(models.Model):
    dcodres = models.CharField(max_length=30)
    dmsgres = models.CharField(max_length=120)
    druccons = models.CharField(max_length=120)
    drazcons = models.CharField(max_length=400)
    dcodestcons = models.CharField(max_length=200)
    ddesestcons = models.CharField(max_length=200)
    drucfactelec = models.CharField(max_length=200)
    process_date = models.DateTimeField()

class TrackLote(models.Model):
    lote = models.CharField(max_length=120)
    estado = models.CharField(max_length=120)
    msge = models.CharField(max_length=120)
    dcodreslot = models.CharField(max_length=60)
    fecha = models.DateTimeField()

class SoapMsg(models.Model):
    method_name = models.CharField(max_length=120)
    url_send = models.CharField(max_length=200, default='http_null')
    headers = models.JSONField(default=dict)
    cookies = models.JSONField(default=dict)    
    elapsed = models.FloatField(default=0)
    xml_send = models.TextField()
    xml_rsp = models.TextField(null=True)
    json_rsp = models.JSONField(default=dict)
    msgres = models.CharField(max_length=500, default='ND')
    cdc = models.CharField(max_length=150, null=True)
    dprotaut = models.BigIntegerField(default=0)
    fproc = models.DateTimeField(auto_now=True)

    def get_last_state_lote(self):
        if self.method_name == 'SiRecepLoteDE' or self.method_name == 'SiResultLoteDE':
            lote = self.json_rsp.get('dprotconslote')
            loteobj = TrackLote.objects.filter(lote=lote).last()
            if loteobj:
                return {'lote': loteobj.estado, 'pk_lote': loteobj.id}
        return 'ND'


class CSeg(models.Model):
    codigo_seguridad = models.CharField(max_length=100)
    asignado_model = models.CharField(max_length=15, default='ND')
    asignado_doc = models.BigIntegerField(default=0)

class DocumentHeader(models.Model):
    cct = {'max_digits':19, 'decimal_places':6 }
    cd_char = {'max_length':120, 'null':True}
    prof_number = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    bs = models.CharField(max_length=60)
    source = models.CharField(max_length=120)
    ext_link = models.CharField(max_length=300, null=True)
    doc_moneda = models.CharField(max_length=10)
    doc_fecha = models.DateField()
    doc_tipo = models.CharField(max_length=10)
    doc_tipo_cod = models.CharField(max_length=10, null=True)
    doc_tipo_desc = models.CharField(max_length=60, null=True)
    doc_op = models.CharField(max_length=10)
    doc_numero = models.BigIntegerField(null=True)
    doc_estado = models.CharField(max_length=120)
    doc_motivo = models.CharField(max_length=120, default='VTA')
    doc_vencimiento = models.DateField(null=True)
    doc_total = models.DecimalField(**cct)
    doc_total_redondeo = models.DecimalField(default=0, **cct)
    doc_iva = models.DecimalField(**cct)
    doc_exenta = models.DecimalField(**cct)
    doc_g10 = models.DecimalField(**cct)
    doc_i10 = models.DecimalField(**cct)
    doc_g5 = models.DecimalField(**cct)
    doc_i5 = models.DecimalField(**cct)
    doc_descuento = models.DecimalField(**cct)
    doc_per_descuento = models.DecimalField(**cct)
    doc_descuento_global = models.DecimalField(**cct)
    doc_saldo = models.DecimalField(**cct)
    doc_pago = models.DecimalField(**cct)
    doc_costo = models.DecimalField(**cct)
    doc_redondeo = models.DecimalField(**cct, default=0)
    doc_establecimiento = models.IntegerField()
    doc_establecimiento_ciudad = models.CharField(max_length=130, default='ASUNCIÓN')
    doc_expedicion = models.IntegerField()
    doc_tipo_ope = models.IntegerField(default=0)
    doc_tipo_ope_desc = models.CharField(max_length=30, null=True)
    doc_tipo_imp = models.IntegerField(default=0, null=True)
    doc_tipo_imp_desc = models.CharField(max_length=30, null=True)
    doc_op_pres_cod = models.IntegerField(default=0)
    doc_op_pres = models.CharField(max_length=30, null=True)
    doc_cre_tipo_cod = models.IntegerField(default=0)
    doc_cre_tipo = models.CharField(max_length=30, null=True)
    doc_tipo_pago_cod = models.IntegerField(default=0)
    doc_tipo_pago = models.CharField(max_length=30, null=True)
    #Interno
    forma_pago_id = models.IntegerField(default=0, null=True)
    forma_pago = models.CharField(max_length=100, null=True)
    doc_cre_cond = models.IntegerField(default=0, null=True)
    doc_cre_cond_desc = models.CharField(max_length=30, null=True)
    doc_cre_plazo = models.CharField(max_length=30, null=True)
    doc_cre_cuota = models.IntegerField(default=0, null=True)
    doc_cre_entrega_inicial = models.FloatField(default=0, null=True)
    doc_entregado = models.DateTimeField(null=True)
    doc_entregado_usuario = models.CharField(**cd_char)
    doc_loop_link = models.UUIDField(null=True)
    doc_relacion_saldo = models.DecimalField(default=0, **cct)
    doc_relacion = models.CharField(**cd_char)
    doc_relacion_cod = models.IntegerField(default=0)
    doc_relacion_cdc = models.CharField(**cd_char)
    doc_relacion_timbrado = models.CharField(**cd_char)
    doc_relacion_establecimiento = models.IntegerField(default=0)    
    doc_relacion_numero = models.BigIntegerField(default=0)
    doc_relacion_expedicion = models.IntegerField(default=0)
    doc_relacion_tipo = models.CharField(**cd_char)
    doc_relacion_tipo_cod = models.IntegerField(default=0)
    doc_relacion_fecha = models.DateField(null=True)
    doc_relacion_monto = models.DecimalField(default=0, **cct)
    
    af_vendedor_cod = models.IntegerField(default=0)
    af_vendedor = models.CharField(max_length=120, null=True)
    af_tdoc_cod = models.IntegerField(default=0)
    af_tdoc = models.CharField(max_length=120, null=True)
    af_doc_id = models.CharField(max_length=120, null=True)
    af_nombrefantasia = models.CharField(max_length=120, null=True)
    af_direccion = models.CharField(max_length=120, null=True)
    af_nro_casa = models.IntegerField(default=0)
    af_dpto_cod = models.IntegerField(default=0)
    af_dpto_nombre = models.CharField(max_length=120, null=True)
    af_distrito_cod = models.IntegerField(default=0)
    af_distrito_nombre = models.CharField(max_length=120, null=True)
    af_ciudad_cod = models.IntegerField(default=0)
    af_ciudad_nombre = models.CharField(max_length=120, null=True)


    pdv_innominado = models.BooleanField(default=False)
    pdv_pais_cod = models.CharField(max_length=10, null=True)
    pdv_pais = models.CharField(max_length=10, null=True)
    pdv_tipocontribuyente = models.CharField(max_length=120, null=True)
    pdv_es_contribuyente = models.BooleanField(default=True)
    pdv_type_business = models.CharField(max_length=120, null=True, default='B2B')
    pdv_codigo = models.BigIntegerField(default=0) 
    pdv_ruc = models.CharField(max_length=120)
    pdv_ruc_dv = models.IntegerField(default=0)
    pdv_nombrefantasia = models.CharField(max_length=300)
    pdv_nombrefactura = models.CharField(max_length=300)
    pdv_direccion_entrega = models.CharField(max_length=200, null=True)
    pdv_dir_calle_sec = models.CharField(max_length=200, null=True)
    pdv_direccion_comple = models.CharField(max_length=200, null=True)
    pdv_numero_casa = models.IntegerField(default=0)
    pdv_numero_casa_entrega = models.IntegerField(default=0)
    pdv_dpto_cod = models.IntegerField(default=0)
    pdv_dpto_nombre = models.CharField(max_length=200, null=True)
    pdv_distrito_cod = models.IntegerField(default=0)
    pdv_distrito_nombre = models.CharField(max_length=200, null=True)
    pdv_ciudad_cod = models.IntegerField(default=0)
    pdv_ciudad_nombre = models.CharField(max_length=200, null=True)
    pdv_telefono = models.CharField(max_length=30, null=True)
    pdv_celular = models.CharField(max_length=30, null=True)
    pdv_email = models.CharField(max_length=120, null=True)

    ek_serie = models.CharField(max_length=10, null=True)
    ek_timbrado = models.BigIntegerField(null=True)
    ek_bs_ruc = models.CharField(max_length=120, null=True)
    ek_bs_ae = models.CharField(max_length=300, null=True)
    ek_bs_ae_cod = models.IntegerField(default=0)
    ek_idcsc = models.CharField(max_length=40, null=True)
    ek_idscsc = models.CharField(max_length=40, null=True)
    ek_timbrado_vigencia = models.DateField(null=True)
    ek_timbrado_vencimiento = models.DateField(null=True)
    ek_cod_seg = models.CharField(max_length=9, default='0')
    ek_cdc = models.CharField(max_length=120, null=True)
    ek_cdc_dv = models.IntegerField(default=0)
    ek_qr_link = models.TextField(null=True)
    ek_qr_img = models.FileField(upload_to='invoice', max_length=500, null=True)
    ek_transacion = models.CharField(max_length=300, null=True)
    # Se inutilizacion, pero si ya esta en la sifen se Cancelado, una NC por el mismo valor
    ek_estado = models.CharField(max_length=60, null=True) 
    ek_date = models.DateTimeField(null=True)
    ek_xml_ekua = models.BooleanField(default=False)
    ek_pdf_file = models.FileField(upload_to='invoice', max_length=500, null=True)
    ek_xml_file = models.FileField(upload_to='invoice', max_length=500, null=True)
    ek_xml_file_signed = models.FileField(upload_to='invoice', null=True)
    impx_tdoc_cod = models.IntegerField(default=0)
    impx_tdoc_nam = models.CharField(max_length=20, null=True)
    impx_doc_num = models.CharField(max_length=20, null=True)
    impx_nombre = models.CharField(max_length=120, null=True)
    impx_cargo = models.CharField(max_length=120, null=True)
    tasa_cambio = models.DecimalField(**cct)
    peso = models.DecimalField(**cct)
    volumen = models.DecimalField(**cct)
    retencionobj = models.ForeignKey('Retencion', null=True, on_delete=models.DO_NOTHING)
    observacion =  models.CharField(max_length=300)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(blank=True, null=True)
    anulado_tipo = models.CharField(max_length=30, null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(blank=True, null=True)
    enviado_cliente = models.BooleanField(default=False)
    enviado_cliente_fecha = models.DateTimeField(blank=True, null=True)
    lote = models.BigIntegerField(default=0)
    lote_estado = models.CharField(max_length=120, null=True)
    lote_msg = models.CharField(max_length=300, null=True)

    def get_timbrado_id(self):
        timbradoobj = Etimbrado.objects.get(timbrado=self.ek_timbrado)
        return timbradoobj.id

    def get_number_full(self):
        return '{}-{}-{}'.format(
            str(self.doc_establecimiento).zfill(3),
            str(self.doc_expedicion).zfill(3),
            str(self.doc_numero).zfill(7),
        )

    def get_doc_relacion(self):
        """Get related invoice number via doc_loop_link"""
        if self.doc_loop_link:
            try:
                related_doc = DocumentHeader.objects.get(prof_number=self.doc_loop_link)
                return '{}-{}-{}'.format(
                    str(related_doc.doc_establecimiento).zfill(3),
                    str(related_doc.doc_expedicion).zfill(3),
                    str(related_doc.doc_numero).zfill(7),
                )
            except DocumentHeader.DoesNotExist:
                return 'ND'
        return 'ND'

    def documentheader_urls(self):
        return {
            'ek_pdf_file': self.ek_pdf_file.url,
            'ek_pdf_file_full': self.ek_pdf_file.url

        }    
    
    def get_documentdetail(self):
        return self.documentdetail_set.filter(anulado=False, bonifica=False)

    def get_qr_full(self):
        return iof.url_viewfull(self.ek_qr_img)

    def get_base_gravada_master(self):
        mbg_5 = 0
        mbg_10 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            bg_5, bg_10 = p.get_base_gravada()
            mbg_5 += bg_5
            mbg_10 += bg_10
        return sum([mbg_5, mbg_10])
        
    def get_base_gravada_master_10(self):
        mbg_10 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            bg_5, bg_10 = p.get_base_gravada()
            mbg_10 += bg_10
        return mbg_10
        
    def get_base_gravada_master_5(self):
        mbg_5 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            bg_5, bg_10 = p.get_base_gravada()
            mbg_5 += bg_5
        return mbg_5        
        
    def get_ivas_10_master(self):
        miva_10 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            iva_5, iva_10 = p.get_ivas()
            miva_10 += iva_10
        return miva_10
        
    def get_ivas_5_master(self):
        miva_5 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            iva_5, iva_10 = p.get_ivas()
            miva_5 += iva_5
        return miva_5
        
    def get_ivas_master(self):
        miva_5 = 0
        miva_10 = 0
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        for p in self.documentdetail_set.filter(anulado=False, bonifica=False).exclude(prod_cod=ex):
            iva_5, iva_10 = p.get_ivas()
            miva_5 += iva_5
            miva_10 += iva_10
        return sum([miva_5, miva_10])
    
    def get_descuento(self):
        return sum(self.get_total_descuento())
        
    def get_total_descuento(self):
        descuento_exenta = 0
        descuento_gravada_5 = 0
        descuento_gravada_10 = 0
        # if self.documentdetail_set.filter(anulado=False, bonifica=True).exclude(prod_cod=90000):
        # if self.powerpack:
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9        
        total_venta = self.documentdetail_set.filter(anulado=False, bonifica=True).only('exenta', 'gravada_5', 'gravada_10')\
                                                        .exclude(prod_cod=ex).aggregate(
            exenta=models.Sum('exenta'),
            gravada_5=models.Sum('gravada_5'),
            gravada_10=models.Sum('gravada_10')
        )
        total_venta = dict_int_none(total_venta)
        descuento_exenta = total_venta.get('exenta')
        descuento_gravada_5 = total_venta.get('gravada_5')
        descuento_gravada_10 = total_venta.get('gravada_10')
            # totales  = (
            #     total_venta.get('exenta') + total_venta.get('gravada_5') + total_venta.get('gravada_10')
            # )
        return descuento_exenta, descuento_gravada_5, descuento_gravada_10
        
    def get_total_exenta(self):
        if self.doc_op == 'RS':
            exenta, gravada_5, gravada_10, iva_5, iva_10 = self.get_valor_nc_raw()
            return exenta
        totales = 0
        ex = 90000            
        if self.doc_op == 'GA':
            ex = -9        
        if self.documentdetail_set.filter(anulado=False, bonifica=False):
            total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False)\
                .exclude(prod_cod=ex)\
                .aggregate(
                exenta=models.Sum('exenta'),
            )
            totales  = total_venta.get('exenta')
        return totales

    def get_total_gravada_10(self):
        totales = 0
        
        if self.doc_op == 'RS':
            exenta, gravada_5, gravada_10, iva_5, iva_10 = self.get_valor_nc_raw()
            return gravada_10
        ex = 90000
        if self.doc_op == 'GA':
            ex = -9            
        if self.documentdetail_set.filter(anulado=False, bonifica=False):
            total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False) \
                .exclude(prod_cod=ex) \
                .aggregate(
                gravada_10=models.Sum('gravada_10'),
            )
            totales  = dict_int_none(total_venta).get('gravada_10')

        return totales
    
    def get_total_base_gravada_10(self):
        totales = 0
        if self.documentdetail_set.filter(anulado=False, bonifica=False):
            total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False) \
                .aggregate(
                base_gravada_10=models.Sum('base_gravada_10'),
            )
            totales  = dict_int_none(total_venta).get('base_gravada_10')

        return totales        
        
    def get_total_gravada_5(self):
        if self.doc_op == 'RS':
            exenta, gravada_5, gravada_10, iva_5, iva_10 = self.get_valor_nc_raw()
            return gravada_5
        ex = 90000            
        if self.doc_op == 'GA':
            ex = -9            
        totales = 0
        if self.documentdetail_set.filter(anulado=False, bonifica=False):
            total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False) \
                .exclude(prod_cod=ex) \
                .aggregate(
                gravada_5=models.Sum('gravada_5'),
            )
            totales  = dict_int_none(total_venta).get('gravada_5')

        return totales
    
    def get_total_base_gravada_5(self):
        totales = 0
        if self.documentdetail_set.filter(anulado=False, bonifica=False):
            total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False) \
                .aggregate(
                base_gravada_5=models.Sum('base_gravada_5'),
            )
            totales  = dict_int_none(total_venta).get('base_gravada_5')

        return totales
    
    def get_total_gravada(self):
        return self.get_total_gravada_10()+self.get_total_gravada_5()
    
    def get_sub_5(self):
        return self.get_total_base_gravada_5()+self.get_ivas_5_master()
    
    def get_sub_10(self):
        return self.get_total_base_gravada_10()+self.get_ivas_10_master()
    
    def get_total_operacion(self):
        exenta = self.get_total_exenta()
        sub_5 = self.get_sub_5()
        sub_10 = self.get_sub_10()
        return exenta+sub_5+sub_10
    
    def get_total_operacion_redondeo(self):
        totope = self.get_total_operacion() #exenta+sub_5+sub_10
        if abs(self.doc_redondeo):
            if self.doc_redondeo <= 0:
                return float(totope) + abs(float(self.doc_redondeo))
            else:
                return float(totope) - abs(float(self.doc_redondeo))
        return totope
    
    def get_total_venta_gs(self):
        if self.doc_moneda == 'USD':
            return self.get_total_venta() * self.tasa_cambio
        return self.get_total_venta()
        
    def get_total_venta(self, redondeo=False):
        if self.doc_op == 'RS':
            exenta, gravada_5, gravada_10, iva_5, iva_10 = self.get_valor_nc_raw()
            return sum([exenta, gravada_5, gravada_10])
        totales = 0
        exc = {'prod_cod':90000}
        if self.doc_op in ['GA', 'G']: exc = {}
        total_venta = self.documentdetail_set.filter(anulado=False, bonifica=False)\
            .only('exenta', 'gravada_5', 'gravada_10') \
            .exclude(**exc)\
            .aggregate(exenta=models.Sum('exenta'),
                 gravada_5=models.Sum('gravada_5'),
                 gravada_10=models.Sum('gravada_10')
            )
        total_venta = dict_int_none(total_venta)
        totales  = (float(total_venta.get('exenta')) +\
                    float(total_venta.get('gravada_5')) + 
                    float(total_venta.get('gravada_10')) )
        hdoc = abs(self.doc_redondeo)
        if hdoc and redondeo:
            if self.doc_redondeo > 0:
                return Decimal(totales)+abs(self.doc_redondeo)
            else:
                return Decimal(totales)-abs(self.doc_redondeo)
        return Decimal(totales)
    
    def get_valor_nc_raw(self, *args, **kwargs):
        texenta = 0
        tgravada_5 = 0
        tgravada_10 = 0
        tiva_5 = 0
        tiva_10 = 0
        for p in self.documentdetail_set.filter(anulado=False, cantidad_devolucion__gt=0):
            exenta, gravada_5, gravada_10, iva_5, iva_10 = p.get_valor_nc()
            texenta += exenta
            tgravada_5 += gravada_5
            tgravada_10 += gravada_10
            tiva_5 += iva_5
            tiva_10 += iva_10
        return [texenta, tgravada_5, tgravada_10, tiva_5, tiva_10, ]    

    def get_total_ventaword(self) -> str:
        if self.doc_moneda == 'GS':
            total_venta = int(self.get_total_venta())
            return num2words(total_venta, lang='es').upper()
        if self.doc_moneda == 'USD':
            total_venta = self.get_total_venta()
            return num2words(total_venta, lang='es', to='currency' ).upper().replace('EUROS', '')        
        return 'ND'
    
    def get_pagos(self) -> dict:
        return self.documentopagos_set.values('tipo').annotate(
            monto=models.Sum('monto')
        )

class DocumentDetail(models.Model):
    cct = {'max_digits':19, 'decimal_places':6, 'default':0}
    documentheaderobj = models.ForeignKey(DocumentHeader, on_delete=models.CASCADE)
    prod_autocreado = models.BooleanField(default=False)
    prod_cod = models.IntegerField()
    prod_descripcion = models.CharField(max_length=500)
    prod_unidad_medida = models.IntegerField(default=77)
    prod_unidad_medida_desc = models.CharField(max_length=20, default='UNI')
    prod_pais_origen = models.CharField(max_length=60, null=True)
    prod_pais_origen_desc = models.CharField(max_length=60, null=True)
    prod_lote = models.CharField(max_length=80, null=True)
    prod_vencimiento = models.DateField(null=True)
    porcentaje_iva = models.IntegerField(default=10)
    precio_unitario_source = models.DecimalField(max_digits=19, decimal_places=6)
    precio_unitario = models.DecimalField(max_digits=19, decimal_places=6)
    precio_unitario_siniva = models.DecimalField(**cct)
    cantidad = models.DecimalField(max_digits=19, decimal_places=6)
    cantidad_devolucion = models.IntegerField(default=0)
    exenta_pct = models.DecimalField(**cct)
    g5_pct = models.DecimalField(**cct)
    g10_pct = models.DecimalField(**cct)
    exenta = models.DecimalField(**cct)
    iva_5 = models.DecimalField(**cct)
    gravada_5 = models.DecimalField(**cct)
    base_gravada_5 = models.DecimalField(**cct)
    iva_10 = models.DecimalField(**cct)
    gravada_10 = models.DecimalField(**cct)
    base_gravada_10 = models.DecimalField(**cct)
    afecto = models.DecimalField(**cct)
    per_tipo_iva = models.IntegerField(default=0)
    bonifica = models.BooleanField(default=False)
    descuento = models.DecimalField(**cct)
    per_descuento = models.DecimalField(**cct)
    volumen = models.DecimalField(**cct)
    peso = models.DecimalField(**cct)
    observacion = models.CharField(max_length=245, null=True)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)    
    anulado = models.BooleanField(default=False)
    anulado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(blank=True, null=True)
    actualizado = models.BooleanField(default=False)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(blank=True, null=True)
    pcalc_source = models.JSONField(default=dict)
    pcalc_result = models.JSONField(default=dict)
    
    def get_cantidad(self):
        if self.cantidad != math.floor(self.cantidad):
            return round(float(self.cantidad), 2)
        return int(self.cantidad)

    def get_ivas(self):
        return [self.iva_5, self.iva_10]
        # cantidad = self.cantidad
        # precio_unitario = self.precio_unitario
        # if self.documentheaderobj.doc_op == 'RS':
        #     cantidad = self.cantidad_devolucion
        # iva_5 = 0
        # iva_10 = 0
        # if self.bonifica: return [iva_5, iva_10]
        # if self.exenta and not self.gravada_10 and not self.gravada_5: return [iva_5, iva_10]
        # #E735 * (E734/100)
        # totopeitem = Decimal(precio_unitario*cantidad)
        # if self.iva_10:
        #     base_g_10 = totopeitem * Decimal(self.per_tipo_iva/100) / Decimal(1.1)   
        #     iva_10 = base_g_10*(Decimal(self.porcentaje_iva)/100)
        # if self.iva_5:
        #     base_g_5 = totopeitem * Decimal(self.per_tipo_iva/100) / Decimal(1.05)
        #     iva_5 = base_g_5*(Decimal(self.porcentaje_iva)/100)
        # return [self.iva_5, self.iva_10]

    def get_base_gravada(self):
        return [self.base_gravada_5, self.base_gravada_10]
        # base_g_5 = 0
        # base_g_10 = 0
        # cantidad = self.cantidad
        # precio_unitario = self.precio_unitario
        # if self.documentheaderobj.doc_op == 'RS':
        #     cantidad = self.cantidad_devolucion        
        # if self.exenta and not self.gravada_10 and not self.gravada_5: return [base_g_5, base_g_10]
        # if self.bonifica: return [base_g_5, base_g_10]
        # totopeitem = Decimal(precio_unitario*cantidad)
        # if self.gravada_5:
        #     #[EA008* (E733/100)] / 1,05 
        #     base_g_5 = totopeitem * Decimal(self.per_tipo_iva/100) / Decimal(1.05)

        # if self.gravada_10:
        #     #[EA008 * (E733/100)] / 1,1
        #     base_g_10 = totopeitem * Decimal(self.per_tipo_iva/100) / Decimal(1.1)
        # return [base_g_5, base_g_10]
    
class DocumentoPagos(models.Model):
    cct = {'max_digits':19, 'decimal_places':6 }
    documentheaderobj = models.ForeignKey(DocumentHeader, on_delete=models.CASCADE)
    source = models.CharField(max_length=120)
    ext_link = models.BigIntegerField(default=0)
    # 1= Efectivo
    # 2= Cheque
    # 3= Tarjeta de crédito
    # 4= Tarjeta de débito
    # 5= Transferencia
    # 6= Giro
    # 7= Billetera electrónica
    # 8= Tarjeta empresarial
    # 9= Vale
    # 10= Retención
    # 11= Pago por anticipo
    # 12= Valor fiscal
    # 13= Valor comercial
    # 14= Compensación
    # 15= Permuta
    # 16= Pago bancario (Informar solo
    # si E011=5)
    # 17 = Pago Móvil
    # 18 = Donación
    # 19 = Promoción
    # 20 = Consumo Interno
    # 21 = Pago Electrónico
    # 99 = Otro
    tipo_cod = models.IntegerField()
    tipo = models.CharField(max_length=120)
    #### BEGIN TARJETA #####
    # 1= Visa
    # 2= Mastercard
    # 3= American Express
    # 4= Maestro
    # 5= Panal
    # 6= Cabal
    # 99= Otro
    tarjeta_denominacion_cod = models.IntegerField(null=True)
    tarjeta_denominacion = models.CharField(max_length=120, null=True)
    tarjeta_procesadora = models.CharField(max_length=120, null=True)
    tarjeta_procesadora_ruc = models.CharField(max_length=120, null=True)
    tarjeta_procesadora_ruc_dv = models.IntegerField(null=True)
    # 1= POS
    # 2= Pago Electrónico (Ejemplo:
    # compras por Internet)
    # 9= Otro
    tarjeta_procesamiento = models.IntegerField(null=True)
    tarjeta_autorizacion_cod = models.BigIntegerField(null=True)
    tarjeta_titular = models.CharField(max_length=200, null=True)
    #Cuatro últimos dígitos de la tarjeta
    tarjeta_numero = models.IntegerField(null=True)
    #### END TARJETA #####
    #### BEGIN CHEQUE #####
    cheque_numero = models.CharField(max_length=12, null=True)
    cheque_emisor = models.CharField(max_length=200, null=True)
    #### END CHEQUE #####
    monto = models.DecimalField(**cct)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)


class DocumentRecibo(models.Model):
    cct = {'max_digits':19, 'decimal_places':6 }
    cd_char = {'max_length':120, 'null':True}
    prof_number = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    bs = models.CharField(max_length=60)
    source = models.CharField(max_length=120)
    ext_link = models.BigIntegerField(default=0)
    doc_moneda = models.CharField(max_length=10)
    doc_fecha = models.DateField()
    doc_tipo = models.CharField(max_length=10)
    doc_tipo_cod = models.CharField(max_length=10, null=True)
    doc_tipo_desc = models.CharField(max_length=60, null=True)
    doc_op = models.CharField(max_length=10)
    doc_numero = models.BigIntegerField(null=True)
    doc_expedicion = models.IntegerField(default=0)
    doc_establecimiento = models.IntegerField()
    doc_establecimiento_ciudad = models.CharField(max_length=130, default='ASUNCIÓN')
    doc_estado = models.CharField(max_length=120)
    doc_vencimiento = models.DateField(null=True)
    doc_total_factura = models.DecimalField(**cct)
    doc_total_nc = models.DecimalField(**cct)
    doc_cobrar = models.DecimalField(**cct)
    doc_retencion = models.DecimalField(**cct)
    doc_efectivo = models.DecimalField(**cct)
    doc_cheque = models.DecimalField(**cct)
    doc_cobrado = models.DecimalField(**cct)
    pdv_innominado = models.BooleanField(default=False)
    pdv_pais_cod = models.CharField(max_length=10, null=True)
    pdv_pais = models.CharField(max_length=10, null=True)
    pdv_tipocontribuyente = models.CharField(max_length=120, null=True)
    pdv_es_contribuyente = models.BooleanField(default=True)
    pdv_type_business = models.CharField(max_length=120, null=True, default='B2B')
    pdv_codigo = models.BigIntegerField(default=0) 
    pdv_ruc = models.CharField(max_length=120)
    pdv_ruc_dv = models.IntegerField(default=0)
    pdv_nombrefantasia = models.CharField(max_length=300)
    pdv_nombrefactura = models.CharField(max_length=300)
    pdv_direccion_entrega = models.CharField(max_length=200, null=True)
    pdv_dir_calle_sec = models.CharField(max_length=200, null=True)
    pdv_direccion_comple = models.CharField(max_length=200, null=True)
    pdv_numero_casa = models.IntegerField(default=0)
    pdv_numero_casa_entrega = models.IntegerField(default=0)
    pdv_dpto_cod = models.IntegerField(default=0)
    pdv_dpto_nombre = models.CharField(max_length=200, null=True)
    pdv_distrito_cod = models.IntegerField(default=0)
    pdv_distrito_nombre = models.CharField(max_length=200, null=True)
    pdv_ciudad_cod = models.IntegerField(default=0)
    pdv_ciudad_nombre = models.CharField(max_length=200, null=True)
    pdv_telefono = models.CharField(max_length=30, null=True)
    pdv_celular = models.CharField(max_length=30, null=True)
    pdv_email = models.CharField(max_length=120, null=True)
    impx_tdoc_cod = models.IntegerField(default=0)
    impx_tdoc_nam = models.CharField(max_length=20, null=True)
    impx_doc_num = models.CharField(max_length=20, null=True)
    impx_nombre = models.CharField(max_length=120, null=True)
    impx_cargo = models.CharField(max_length=120, null=True)
    tasa_cambio = models.DecimalField(**cct)
    observacion =  models.CharField(max_length=300)
    pdf_file = models.FileField(max_length=300, null=True)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(blank=True, null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(blank=True, null=True)
    enviado_cliente = models.BooleanField(default=False)
    enviado_cliente_fecha = models.DateTimeField(blank=True, null=True)

    def documentrecibo_urls(self):
        return {
            'recibo_pdf_file': self.pdf_file.url,
        }

    def get_total_cobrado(self) -> str:
        if self.doc_moneda == 'GS':
            total_venta = int(self.doc_cobrado)
            return num2words(total_venta, lang='es').upper()
        if self.doc_moneda == 'USD':
            total_venta = self.doc_cobrado
            return num2words(total_venta, lang='es', to='currency' ).upper().replace('EUROS', '')
        return 'ND'

    def get_total_fe(self):
        return self.documentrecibodetail_set.filter(tipo='FE').aggregate(
            total=Sum('total')
        ).get('total')
    
    def get_total_rt(self):
        return self.documentrecibodetail_set.filter(tipo='FE').aggregate(
            retencion=Sum('retencion')
        ).get('retencion')

    def get_total_nc(self):
        return self.documentrecibodetail_set.filter(tipo='NC').aggregate(
            total=Sum('total')
        ).get('total')
    
    def get_fes(self):
        return self.documentrecibodetail_set.filter(tipo='FE')

    def get_ncs(self):
        return self.documentrecibodetail_set.filter(tipo='NC')
    
    def get_fe_ncs(self):
        return zip_longest(self.get_fes(), self.get_ncs())
    
    def get_len_docs(self):
        return ['']*self.documentrecibodetail_set.filter(tipo__in=['NC', 'FE']).count()

class DocumentReciboDetail(models.Model):
    cct = {'max_digits':19, 'decimal_places':6 }
    recobj = models.ForeignKey(DocumentRecibo, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=60)
    prof_number = models.UUIDField(default=uuid.uuid4)
    establecimiento = models.IntegerField()
    expedicion = models.IntegerField()
    numero = models.BigIntegerField()
    cobrado = models.DecimalField(**cct)
    total = models.DecimalField(**cct)
    saldo = models.DecimalField(**cct)
    retencion_numero = models.CharField(max_length=120, null=True)
    retencion = models.DecimalField(**cct)
    observacion =  models.CharField(max_length=300)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(blank=True, null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(blank=True, null=True)
    enviado_cliente = models.BooleanField(default=False)
    enviado_cliente_fecha = models.DateTimeField(blank=True, null=True)

    def get_number_full(self):
        return '{}-{}-{}'.format(
            str(self.establecimiento).zfill(3),
            str(self.expedicion).zfill(3),
            str(self.numero).zfill(7),
        )
    
class Retencion(models.Model):
    cct = {'max_digits':19, 'decimal_places':6 }
    retencion_fecha = models.DateField()
    retencion_numero = models.BigIntegerField()
    doc_loop_link = models.IntegerField(null=True)
    doc_relacion_numero = models.BigIntegerField(default=0)
    doc_relacion_monto = models.DecimalField(default=0, **cct)
    pdv_codigo = models.BigIntegerField(default=0)
    pdv_ruc = models.CharField(max_length=120)
    pdv_ruc_dv = models.IntegerField(default=0)
    pdv_nombrefantasia = models.CharField(max_length=300)
    pdv_nombrefactura = models.CharField(max_length=300)
    retencion = models.DecimalField(**cct)
    cargado_fecha = models.DateTimeField(null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    anulado_usuario = models.CharField(max_length=120, null=True)
    anulado_fecha = models.DateTimeField(blank=True, null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(blank=True, null=True)

    def get_numero(self):
        retn = str(self.retencion_numero)
        esta = retn[0:3]
        expd = retn[3:6]
        numero = retn[-7:]
        return f'{esta}-{expd}-{numero}'


class Clientes(models.Model):
    pdv_innominado = models.BooleanField(default=False)
    pdv_pais_cod = models.CharField(max_length=10, null=True)
    pdv_pais = models.CharField(max_length=10, null=True)
    pdv_tipocontribuyente = models.CharField(max_length=120, null=True)
    pdv_es_contribuyente = models.BooleanField(default=True)
    pdv_type_business = models.CharField(max_length=120, null=True, default='B2C')
    pdv_codigo = models.BigIntegerField(default=0) 
    pdv_ruc = models.CharField(max_length=120)
    pdv_ruc_dv = models.IntegerField(default=0)
    pdv_ruc_estado = models.CharField(max_length=50, null=True)
    pdv_nombrefantasia = models.CharField(max_length=300)
    pdv_nombrefactura = models.CharField(max_length=300)
    pdv_direccion_entrega = models.CharField(max_length=200, null=True)
    pdv_dir_calle_sec = models.CharField(max_length=200, null=True)
    pdv_direccion_comple = models.CharField(max_length=200, null=True)
    pdv_numero_casa = models.IntegerField(default=0)
    pdv_numero_casa_entrega = models.IntegerField(default=0)
    pdv_dpto_cod = models.IntegerField(default=0)
    pdv_dpto_nombre = models.CharField(max_length=200, null=True)
    pdv_distrito_cod = models.IntegerField(default=0)
    pdv_distrito_nombre = models.CharField(max_length=200, null=True)
    pdv_ciudad_cod = models.IntegerField(default=0)
    pdv_ciudad_nombre = models.CharField(max_length=200, null=True)
    pdv_telefono = models.CharField(max_length=30, null=True)
    pdv_celular = models.CharField(max_length=30, null=True)
    pdv_email = models.CharField(max_length=120, null=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    cargado_fecha = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    anclaje_cliente = models.CharField(max_length=200, blank=True, null=True)



class Categoria(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Medida(models.Model):
    medida_cod = models.IntegerField()
    medida = models.CharField(max_length=200)
    medida_descripcion = models.CharField(max_length=200)

class PorcentajeIva(models.Model):
    porcentaje = models.IntegerField()
    descripcion = models.CharField(max_length=120)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.porcentaje}%"


class Producto(models.Model):
    cct = {'max_digits':19, 'decimal_places':6}
    prod_cod = models.BigIntegerField(unique=True)
    descripcion = models.CharField(max_length=300)
    ean = models.CharField(max_length=300, blank=True, null=True)
    moneda = models.CharField(max_length=4, default='PYG')
    categoriaobj = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True)
    marcaobj = models.ForeignKey(Marca, on_delete=models.CASCADE, null=True, blank=True)
    medidaobj = models.ForeignKey(Medida, on_delete=models.CASCADE, null=True, blank=True)
    porcentaje_iva = models.ForeignKey(PorcentajeIva, on_delete=models.CASCADE, null=True, blank=True)
    precio = models.DecimalField(**cct, default=0)
    exenta = models.DecimalField(**cct, default=0)
    g5 = models.DecimalField(**cct, default=0)
    g10 = models.DecimalField(**cct, default=0)
    costo = models.DecimalField(**cct, default=0)
    stock = models.DecimalField(**cct, default=0)
    photo = models.ImageField(upload_to='products/', max_length=300, null=True)
    activo = models.BooleanField(default=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    cargado_fecha = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['descripcion']

    def __str__(self):
        return f"{self.prod_cod} - {self.descripcion}"

    def get_photo_url(self):
        """Return photo URL if exists, otherwise None"""
        if self.photo:
            return self.photo.url
        return None

    def save(self, *args, **kwargs):
        if not self.prod_cod:
            last_codigo = Producto.objects.all().order_by('prod_cod').last()
            if last_codigo:
                self.prod_cod = last_codigo.prod_cod + 1
            else:
                self.prod_cod = 1
        super(Producto, self).save(*args, **kwargs)


class MetodosPago(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.CharField(max_length=300, blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Cotizacion(models.Model):
    cct = {'max_digits':19, 'decimal_places':6}
    origen = models.CharField(max_length=10, default='BCP')
    moneda = models.CharField(max_length=4, default='PYG')
    tasa_cambio = models.DecimalField(**cct, default=1)
    compra = models.DecimalField(**cct, default=1)
    venta = models.DecimalField(**cct, default=1)
    fecha = models.DateField(auto_now_add=True)


class Certificate(models.Model):
    """
    Modelo para gestionar certificados digitales SIFEN.

    Almacena el archivo PFX original y genera los archivos PEM y KEY
    necesarios para la firma digital de documentos electrónicos.
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de Procesar'),
        ('activo', 'Activo'),
        ('vencido', 'Vencido'),
        ('error', 'Error al Procesar'),
        ('revocado', 'Revocado'),
    ]

    businessobj = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='certificates',
        help_text='Empresa a la que pertenece el certificado'
    )
    nombre = models.CharField(
        max_length=200,
        help_text='Nombre descriptivo del certificado (ej: Certificado SIFEN 2024)'
    )
    pfx_file = models.FileField(
        upload_to='certificates/pfx/',
        max_length=500,
        help_text='Archivo de certificado PKCS#12 (.p12 o .pfx)'
    )
    # Password encriptado - se guarda hasheado para mayor seguridad
    pfx_password_encrypted = models.TextField(
        help_text='Contraseña del certificado PFX (encriptada)'
    )
    # Archivos generados
    pem_file = models.FileField(
        upload_to='certificates/pem/',
        max_length=500,
        null=True,
        blank=True,
        help_text='Archivo PEM generado (certificado)'
    )
    key_file = models.FileField(
        upload_to='certificates/key/',
        max_length=500,
        null=True,
        blank=True,
        help_text='Archivo KEY generado (clave privada)'
    )
    # Información del certificado (extraída del PFX)
    titular = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        help_text='Titular del certificado (CN del subject)'
    )
    emisor = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        help_text='Autoridad emisora del certificado'
    )
    numero_serie = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='Número de serie del certificado'
    )
    fecha_emision = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de emisión del certificado'
    )
    fecha_vencimiento = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Fecha de vencimiento del certificado'
    )
    # Estado y metadatos
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        help_text='Estado actual del certificado'
    )
    es_predeterminado = models.BooleanField(
        default=False,
        help_text='Indica si es el certificado predeterminado para la empresa'
    )
    ultimo_uso = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Última vez que se usó para firmar un documento'
    )
    documentos_firmados = models.IntegerField(
        default=0,
        help_text='Contador de documentos firmados con este certificado'
    )
    error_mensaje = models.TextField(
        null=True,
        blank=True,
        help_text='Mensaje de error si el procesamiento falló'
    )
    # Auditoría
    cargado_fecha = models.DateTimeField(auto_now_add=True)
    cargado_usuario = models.CharField(max_length=120, null=True)
    actualizado_fecha = models.DateTimeField(auto_now=True)
    actualizado_usuario = models.CharField(max_length=120, null=True)

    class Meta:
        verbose_name = "Certificado Digital"
        verbose_name_plural = "Certificados Digitales"
        ordering = ['-es_predeterminado', '-cargado_fecha']

    def __str__(self):
        return f"{self.nombre} - {self.businessobj.name}"

    def save(self, *args, **kwargs):
        # Si se marca como predeterminado, quitar de los demás
        if self.es_predeterminado:
            Certificate.objects.filter(
                businessobj=self.businessobj,
                es_predeterminado=True
            ).exclude(pk=self.pk).update(es_predeterminado=False)
        super().save(*args, **kwargs)

    def get_pem_path(self):
        """Retorna la ruta absoluta del archivo PEM."""
        if self.pem_file:
            return self.pem_file.path
        return None

    def get_key_path(self):
        """Retorna la ruta absoluta del archivo KEY."""
        if self.key_file:
            return self.key_file.path
        return None

    def is_valid(self):
        """Verifica si el certificado está vigente."""
        from django.utils import timezone
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento > timezone.now()

    def days_until_expiry(self):
        """Retorna los días restantes hasta el vencimiento."""
        from django.utils import timezone
        if not self.fecha_vencimiento:
            return None
        delta = self.fecha_vencimiento - timezone.now()
        return delta.days

