import re
import urllib.parse
from django.conf import settings
from django.shortcuts import resolve_url

class IoF(object):
    def clean_phone_number(self, phone_number):
        """
        Convertimos el numero de celular a un formato internacional
        """
        # TODO: Ver cuando es un formato de celular del exterior
        if phone_number:
            # Dejamos solo numeros
            phone = re.sub('[^0-9]', '', phone_number)

            # Si el nro empieza con 0, lo convertimos a internacional
            if phone.startswith('0'):
                phone = f'+595{phone[1:]}'

            # Si el nro empieza con 9, lo convertimos a internacional
            if phone.startswith('9'):
                phone = f'+595{phone}'

            # Si el nro empieza con 5, agregamos un signo +
            if phone.startswith('5'):
                phone = f'+{phone}'

            # Si el nro tiene una longitud diferente a 13, retornamos error
            if len(phone) != 13:
                return {'error': 'Verifique el formato del nro de celular (resultado de formato automatico {phone}'}
            return phone
        else:
            return {'error': 'Nro de celular no valido'}
        
    def url_viewfull(self, fobj):
        gd = f'{settings.MEDIA_PROTOCOL}://{settings.MEDIA_DOMAIN}/'
        fp = resolve_url('show_media_file', fobj.path)
        return urllib.parse.urljoin(gd, fp).strip('/')

