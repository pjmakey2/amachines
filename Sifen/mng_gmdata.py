import random, binascii
import qrcode
from Sifen.fl_sifen_conf import EVERSION, URL_Q, RFOLDER
from Sifen.models import DocumentHeader
from hashlib import sha256
import logging

class Gdata:
    def month_to_name(self,month):
        m =  {
            1: "ENERO",
            2: "FEBRERO",
            3: "MARZO",
            4: "ABRIL",
            5: "MAYO",
            6: "JUNIO",
            7: "JULIO",
            8: "AGOSTO",
            9: "SEPTIEMBRE",
            10: "OCTUBRE",
            11: "NOVIEMBRE",
            12: "DICIEMBRE"
        }
        return m[month]

    def calculate_dv(self, ruc, base_max=11):
        ruc_n = ''
        for v_char in ruc:
            v_nchar =  ord(v_char.upper())
            if not (v_nchar >= 48 and v_nchar <= 57):
                ruc_n += str(v_nchar)
            else:
                ruc_n += v_char
        ruc = ruc_n
        k = 2
        total = 0
        rucl = len(ruc)
        ruc = ruc[rucl::-1]
        for aux_num in ruc:
            if k > base_max: k = 2
            #aux_num = int(ruc[idx])
            aux_num = int(aux_num)
            total += (aux_num * k)
            k += 1
        rr = total % 11
        if (rr > 1):
            dv = 11 - rr
        else:
            dv = 0
        return dv

    def gen_codseg(self):
        a = random.randint(0, 999999999)
        b = random.randint(0, 999999999)
        if a > b:
           x = random.randrange(b, a)
        else:
           x = random.randrange(a, b)
        return str(x).zfill(9)

    def gen_cdc(self,
               tipo_doc, 
               ruc_empresa,
               ruc_dv,
               establecimiento,
               expedicion,
               doc_numero,
               tipo_contribuyente,
               doc_fecha,
               codseg):
        ruc_empresa = str(ruc_empresa).zfill(8)
        cdc = [
               str(tipo_doc).zfill(2), 
               ruc_empresa,
               ruc_dv,
               str(establecimiento).zfill(3),
               str(expedicion).zfill(3),
               str(doc_numero).zfill(7),
               tipo_contribuyente,
               doc_fecha.strftime('%Y%m%d'),
               1,
               str(codseg).zfill(9)
        ]
        cdc = map(lambda x: str(x), cdc)
        cdc = ''.join(cdc)
        cdc_dv = self.calculate_dv(cdc)
        cdc = "{}{}".format(cdc,cdc_dv)
        return cdc, cdc_dv

    def format_qr(self, digest, pedobj: DocumentHeader):
        qpd = 'nVersion={}&Id={}&dFeEmiDE={}&dRucRec={}&dTotGralOpe={}&dTotIVA={}&cItems={}&DigestValue={}&IdCSC={}'
        if not pedobj.pdv_es_contribuyente:
            qpd = 'nVersion={}&Id={}&dFeEmiDE={}&dNumIDRec={}&dTotGralOpe={}&dTotIVA={}&cItems={}&DigestValue={}&IdCSC={}'
        if pedobj.doc_tipo == 'AF':
            qpd = 'nVersion={}&Id={}&dFeEmiDE={}&dRucRec={}&dTotGralOpe={}&dTotIVA={}&cItems={}&DigestValue={}&IdCSC={}'
            pedobj.pdv_ruc = pedobj.ek_bs_ruc
        datf = str.encode(pedobj.doc_fecha.strftime('%Y-%m-%dT%H:%M:%S'))
        qpar = qpd.format(
            EVERSION, 
            pedobj.ek_cdc, 
            binascii.hexlify(datf).decode('utf-8'),
            pedobj.pdv_ruc,
            '{:.4f}'.format(pedobj.get_total_operacion()-abs(pedobj.doc_redondeo)),
            '{:.4f}'.format(pedobj.get_ivas_master()),
            pedobj.documentdetail_set.filter(anulado=False).exclude(prod_cod=90000).count(),
            binascii.hexlify(str.encode(digest)).decode('utf-8'),
            '1'.zfill(4),
        )
        qparsec = qpar + pedobj.ek_idcsc
        qpar = qpar + '&' + 'cHashQR={}'.format(sha256(qparsec.encode('utf-8')).hexdigest())
        qpar = '{}{}'.format(URL_Q, qpar).strip()
        logging.info('Format QR string {}'.format(qpar))
        qri = self.create_qr_image(pedobj.prof_number, qpar)
        qr_image = qri.get('qr_image')
        return {'qpar': qpar, 'qri': qr_image }

    def create_qr_image(self, pedido_numero, qpar):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=4,
        )
        qr.add_data(qpar)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qrpfile = '{}/qrs/qr_{}.png'.format(RFOLDER, pedido_numero)
        img.save(qrpfile)
        return {'exitos': 'Hecho', 'qr_image': qrpfile}


