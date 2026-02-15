from OptsIO.io_json import to_json, from_json
from datetime import datetime


class IoP(object):
    def validate_sysparams(self, *args, **kwargs) -> tuple:
        q: dict = kwargs.get('qdict').copy()
        uc_fields: dict = from_json(q.get('uc_fields', "{}"))
        tipo = uc_fields.get('tipo').strip()
        valor_s = uc_fields.get('valor_s').strip()
        valor_f = uc_fields.get('valor_f').strip()
        if tipo == 'str':
            if valor_s.strip() == '':
                return {'error': f'El valor {valor_s} es incorrecto para el tipo {tipo}'}, args, kwargs
            
        if tipo == 'int':
            try:
                float(valor_f)
            except:
                return {'error': f'El valor {valor_s} es incorrecto para el tipo {tipo}'}, args, kwargs
        if tipo == 'json':
            try:
                to_json(valor_s)
            except:
                return {'error': f'El valor {valor_s} es incorrecto para el tipo {tipo}'}, args, kwargs
        uc_fields['valor_s'] = valor_s
        uc_fields['valor_f'] = valor_f
        uc_fields['save_user'] = kwargs.get('userobj').username
        uc_fields['date_save'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kwargs['qdict']['uc_fields'] = to_json(uc_fields)
        return {'success': 'Parametro Valido'}, args, kwargs