import arrow, copy, uuid, json, datetime, re
from django.db.models.fields.files import ImageFieldFile, FieldFile
from django.shortcuts import resolve_url
from django.utils.timezone import is_aware
from decimal import Decimal
from pprint import pprint
import copy
import inspect, importlib
from django.http import QueryDict
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
import json
import logging
from decimal import getcontext, ROUND_HALF_UP
from django.core.cache import caches
redisc = caches['default']
getcontext().prec = 10
getcontext().rounding = ROUND_HALF_UP
from OptsIO.io_construct import FConstruc


UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VENTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

MONEDAS = (
    {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
    {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES AMERICANOS', 'symbol': u'US$'},
    {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
    {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
    {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
    {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
)
# Para definir la moneda me estoy basando en los código que establece el ISO 4217
# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.

get_model = apps.get_model
class IoS(object):
    def __init__(self):
        self.stsconstruc = FConstruc()

    def seModel(self, 
                userobj: str | None = 'ND', 
                rq = None, 
                files = None, 
                qdict: QueryDict | dict = {}) -> dict:
        model_app_name: str = qdict.get("model_app_name", '')
        model_name: str = qdict.get("model_name", '')
        dbcon: str = qdict.get("dbcon", "default")
        appobj = apps.get_app_config(model_app_name)
        model_class = appobj.get_model(model_name)
        mquery = json.loads(qdict.get("mquery", "[]"))
        specific_search = json.loads(qdict.get("specific_search", "{}"))
        specific_populate = json.loads(qdict.get("specific_populate", "{}"))
        fake_values = json.loads(qdict.get("fakes", "[]"))
        only = json.loads(qdict.get("fields", "[]"))
        allfields = qdict.get("allfields", 0)
        detail_objs = json.loads(qdict.get("detail_objs", "[]"))


        methods = json.loads(qdict.get("methods", "[]"))
        r_form_k = qdict.get("r_form_k")
        exprs = json.loads(qdict.get("exprs", "[]"))
        qexc = json.loads(qdict.get("qexc", "{}"))
        distinct = json.loads(qdict.get("distinct", "[]"))
        values = json.loads(qdict.get("values", "[]"))
        pdopts = json.loads(qdict.get("pdopts", "{}"))
        # Grids
        pq_curpage = qdict.get("pq_curpage")
        pq_rpp = qdict.get("pq_rpp")
        pq_sort = json.loads(qdict.get("pq_sort", "[]"))
        pq_filter = json.loads(qdict.get("pq_filter", "{}"))
        startRow = int(qdict.get("startRow", 0))
        endRow = int(qdict.get("endRow", 100))
        check_cache = qdict.get('check_cache')
        if check_cache:
            caobj = redisc.get(check_cache)
            if caobj: return caobj
        if pq_rpp:
            pq_curpage = int(pq_curpage)
            if pq_curpage == 0:
                pq_curpage = 1
            endRow = pq_curpage * int(pq_rpp)
            startRow = 0
            if endRow > int(pq_rpp):
                startRow = endRow - int(pq_rpp)
            logging.info("Start = {} End = {}".format(startRow, endRow))
        sfields = self.structFields(only)
        if allfields:
            only = []
            for field in model_class._meta.fields:
                only.append(field.name)
        if methods:
            sfields.extend(methods)
        annotates = {}
        if exprs:
            annotates = self.constructExprs(exprs)
            sfields.extend(annotates.keys())
        fields = list(filter(lambda x: x.find("__") < 0, only))
        fields = list(filter(lambda x: x not in fake_values, fields))
        only = fields
        trows = 0
        rdf = {}
        qd = QueryDict(mutable=True)
        for q in mquery:
            qd.update({q.get("field"): q.get("value")})
        if pq_filter:
            logging.info("Build filter base on {}".format(pq_filter))
            qd = self.stsconstruc.pqueryfilter(qd, pq_filter)
        pq_sort_method = []
        if pq_sort:
            
            qd, pq_sort_method_construct = self.stsconstruc.pquerysort(qd, pq_sort, model_class=model_class)
            pq_sort_method = list(filter(lambda x: x.get("method"), pq_sort))
            if pq_sort_method_construct:
                pq_sort_method.extend(pq_sort_method_construct)
            logging.info("Build Sort base on {} result in qd {} pq_sort_method_construc {} extending {}".format(
                                                        pq_sort,
                                                        qd, pq_sort_method,
                                                        pq_sort_method
                    ))
        qp = list(qd.lists())
        order_field = qd.getlist("order_field", [])
        qf = self.stsconstruc.querydict_params(qp, [])
        qf_or = self.stsconstruc.querydict_args(qp)
        logging.info(
            f"""
            Set query
                dbcon = {dbcon}
                only = {only}
                fields = {fields}
                sfields = {sfields}
                qf_or = {qf_or}
                qf = {qf}
                values = {values}
                qexc = {qexc}
                order_field = {order_field}
                annotates = {annotates}
                distinct = {distinct}
                pdopts = {pdopts}
                pq_filter = {pq_filter}
                pq_sort = {pq_sort}
        """
        )
        if specific_search:
            module = specific_search.get('module')
            package = specific_search.get('package')
            attr = specific_search.get('attr')
            mname = specific_search.get('mname')
            action = specific_search.get('action')
            search_value = specific_search.get('search_value')
            dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
            cls = dobj()
            dobj = getattr(cls, mname)
            qs = dobj(dbcon, search_value, userobj=userobj, action=action, qf=qf)
        elif specific_populate:
            module = specific_populate.get('module')
            package = specific_populate.get('package')
            attr = specific_populate.get('attr')
            mname = specific_populate.get('mname')
            action = specific_populate.get('action')
            #print(specific_populate)
            dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
            cls = dobj()
            dobj = getattr(cls, mname)
            qs = dobj(rq=rq, qf_or=qf_or, qf=qf)
        elif annotates:
            qs = (
                model_class.objects.using(dbcon)
                .only(*only)
                .filter(*(qf_or,), **qf)
                .values(*values)
                .exclude(**qexc)
                .order_by(*order_field)
                .annotate(**annotates)
            )
            trows = qs.count()
        else:
            qs = (
                model_class.objects.using(dbcon)
                .only(*only)
                .filter(*(qf_or,), **qf)
                .exclude(**qexc)
                .order_by(*order_field)
                .distinct(*distinct)
            )
            trows = qs.count()
        qs = qs[startRow:endRow]
        qs = list(map(lambda x: self.stsconstruc.sfields(x, sfields, fields, detail_objs=detail_objs), qs))
        if pq_sort_method:
            if not pdopts: pdopts = {}
            pdopts['sort_values'] = []
            pdopts['sort_ascending'] = []
            for pqs in pq_sort_method:
                pdopts['sort_values'].append(
                    pqs.get('dataIndx')
                )
                pdopts['sort_ascending'].append(
                    False if pqs.get('dir') == 'down' else True
                )
        if pdopts and not r_form_k:
            #print(pdopts)
            rdf = self.stsconstruc.constructDf(qs, pdopts)
            df = rdf.pop("df")
            qs = df.to_dict(orient="records")
            
        if r_form_k:
            qs = self.convert_list_to_dict(qs, r_form_k)
        rsp = {"qs": qs, "rdf": rdf, "trows": trows, "page": pq_curpage}
        if check_cache:
            redisc.set(check_cache, rsp, 84600)
        return rsp
    
    def seModelForm(self, *args, **kwargs: dict):
        q: dict = kwargs.get('qdict', {}).copy()
        fields = set(json.loads(q.get('fields')))
        model_app_name: str = q.get("model_app_name", '')
        model_name: str = q.get("model_name", '')
        appobj = apps.get_app_config(model_app_name)
        model_class = appobj.get_model(model_name)
        fftmp = filter(lambda x: x.find('__') < 0, fields)
        ff = self.form_model_fields(fftmp, model_class._meta.fields)
        logging.info(f'Remove {ff} non used fields from {fields}')
        for rr in ff:
            fields.remove(rr)
        q['fields'] = json.dumps(list(fields))
        kwargs['qdict'] = q
        sem = self.seModel(*args, **kwargs)
        robj = sem.get('qs', [])[0]
        frepr = json.loads(q.get('frepr', "[]"))

        for f in filter(lambda x: x.get('type') == 'mapping', frepr):
            robj[f.get('idx')] = robj.get(f.get('m_from'))

        for f in filter(lambda x: x.get('type') == 'lselect', frepr):
            robj[f.get('idx')] = {
                'local_select': True,
                'set': robj[f.get('idx')]
            }

        for f in filter(lambda x: x.get('type') == 'rselect', frepr):
            ridx = f.get('ridx')
            fidx = f.get('fidx')
            sidx = robj.get(ridx)
            rget = f.get('rget')
            pps = { rget: sidx}
            vax = robj.get(f.get('vax'))
            djoin_id = f.get('djoin_id', '_')
            tm_app: str = f.get('app')
            tm_model: str = f.get('fmo')
            tm_appobj = apps.get_app_config(tm_app)
            tm_model = tm_appobj.get_model(tm_model)
            try:
                mobj = tm_model.objects.using(f.get('dbcon')).get(**pps)
                if isinstance(fidx, list):
                    sidx = []
                    for v in fidx:
                        attr = getattr(mobj,v)
                        if inspect.ismethod(v):
                            sidx.append(attr())
                        else:
                            sidx.append(attr)
                    sidx = map(str, sidx)
                    sidx = f'{djoin_id}'.join(sidx)
                else:
                    sidx = attr = getattr(mobj,fidx)
            except ObjectDoesNotExist:
                sidx = None
            if f.get('multi'):
                robj[f.get('idx')].append({
                    'idx': sidx,
                    'vax': vax
                })
            else:
                robj[f.get('idx')] = {
                    'idx': sidx,
                    'vax': vax
                }
        
        for f in filter(lambda x: x.get('type') == 'fselect', frepr):
            sidx = robj.get(f.get('idx'))
            vax = robj.get(f.get('vax'))
            fmo = f.get('fmo')
            djoin = f.get('djoin_id', '_')
            if fmo:
                tm_app: str = f.get('app')
                tm_model: str = f.get('fmo')
                tm_appobj = apps.get_app_config(tm_app)
                tm_model = tm_appobj.get_model(tm_model)
                try:
                    mobj = tm_model.objects.using(f.get('dbcon')).get(pk=sidx)
                    if isinstance(f.get('vax'), list):
                        vax = []
                        for v in f.get('vax'):
                            attr = getattr(mobj,v)
                            if inspect.ismethod(v):
                                vax.append(attr())
                            else:
                                vax.append(attr)
                        vax = map(str, vax)
                        vax = f'{djoin}'.join(vax)
                    else:
                        mobj = tm_model.objects.using(f.get('dbcon')).get(pk=sidx)
                        vax = getattr(mobj,f.get('vax'))
                        if inspect.ismethod(vax):
                            vax = vax()
                except ObjectDoesNotExist:
                    vax = None
            if f.get('multi'):
                robj[f.get('idx')].append({
                    'idx': sidx,
                    'vax': vax
                })
            else:
                robj[f.get('idx')] = {
                    'idx': sidx,
                    'vax': vax
                }
        return robj
    
    def structFields(self, only: list):
        sfields = []
        for f in only:
            if f.find('__') >= 0:
                sfields.append(f)
        return sfields
    
    def constructExprs(self, exprs: list):
        annotates = {}
        for expr in exprs:
            annotates[expr.get('name')] = eval(expr.get('expr'))
        return annotates
    
    def form_model_fields(self, form_fields: list, model_fields: list):
        mf = [ m.name for m in model_fields ]
        mf.append('pk')
        mr = list(filter(lambda x: x.is_relation, model_fields ))
        mr = list(map(lambda x: x.attname, mr))
        mf.extend(mr)
        mf = set(mf)
        ff = set(form_fields)
        return ff.difference(mf)
    
    def get_internal_types(self, mobj, model_field: str):
        return self.stsconstruc.get_modelfield_internal_type(mobj, model_field)
    
    def format_data_for_db(self, model_class, mvalues, update=False):
        rnorm = []
        rrm = []
        rbol = []
        for k, v in mvalues.items():
            finte = self.get_internal_types(model_class, k)
            if finte == 'BooleanField':
                if isinstance(v, bool):
                    rbol.append((k, v))
                elif v.strip() == '':
                    rbol.append((k, False))
                else:
                    rbol.append((k, True))
                continue
            if finte in ['IntegerField', 'BigIntegerField', 
                         'SmallIntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField', 
                         'AutoField', 'BigAutoField', 'SmallAuto', 'JoinField', 'ForeignKey']:
                if isinstance(v, str) or isinstance(v, bytes):
                    if v.strip() == '' or v.strip() == 'null' or v.strip() == 'undefined':
                        if update:
                            rnorm.append((k, None))
                        else:
                            rrm.append(k)
                        continue
                if isinstance(v, list):
                    v = list(map(lambda x: int(float(x)), v))
                    rnorm.append((k, v))
                    continue
                rnorm.append((k, int(float(v))))
                continue
            if finte in ['FloatField', 'DecimalField']:
                if isinstance(v, str) or isinstance(v, bytes):
                    if v.strip() == '' or v.strip() == 'null' or v.strip() == 'undefined':
                        if update:
                            rnorm.append((k, None))
                        else:
                            rrm.append(k)
                        continue
                rnorm.append((k, float(v)))
                continue

            if finte == 'TextField':
                if isinstance(v, str) or isinstance(v, bytes):
                    rnorm.append((k, v.strip()))
                    continue
            if isinstance(v, str) or isinstance(v, bytes):
                if v.strip() == '' or v.strip() == 'null' or v.strip() == 'undefined':
                    if update:
                        rnorm.append((k, None))
                    else:
                        rrm.append(k)
                    continue
                rnorm.append((k, v.strip()))
        return rnorm, rrm, rbol
    
    def get_differences_fields(self, mdict: dict, uc_fields: dict) -> dict:
        try:
            mm = set(mdict.items())
        except Exception as e:
            print(e)
            return True
        uc = set(uc_fields.items())
        dd = dict(uc - mm)
        return dd

    def convert_list_to_dict(self, input_list: list, key) -> dict:
        result_dict = {}
        for item in input_list:
            new_key = item.get(key)
            if new_key is not None:
                item.pop(key, None)  # Remove the specified key from the dictionary
                result_dict[new_key] = item
        return result_dict


def to_word(number, mi_moneda=None):
    try:
        number = int(number)
    except:
        return 'no es posible convertir el numero en letras'
    if mi_moneda != None:
        try:
            moneda = filter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
            if number < 2:
                moneda = moneda['singular']
            else:
                moneda = moneda['plural']
        except:
            return "Tipo de moneda inválida"
    else:
        moneda = ""
    """Converts a number into string representation"""
    converted = ''

    if not (0 < number < 999999999):
        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if(millones):
        if(millones == '001'):
            converted += 'UN MILLON '
        elif(int(millones) > 0):
            converted += '%sMILLONES ' % __convert_group(millones)

    if(miles):
        if(miles == '001'):
            converted += 'MIL '
        elif(int(miles) > 0):
            converted += '%sMIL ' % __convert_group(miles)

    if(cientos):
        if(cientos == '001'):
            converted += 'UN '
        elif(int(cientos) > 0):
            converted += '%s ' % __convert_group(cientos)

    converted += moneda

    return converted.title()

def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if(n == '100'):
        output = "CIEN "
    elif(n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if(k <= 20):
        output += UNIDADES[k]
    else:
        if((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output

def moneyfmt(value, places=2, curr='', sep=',', dp='.',
             pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    if isinstance(value, int):
        value = Decimal(value)
    if isinstance(value, float):
        value = Decimal(value)
    if value == 0: return '0'

    q = Decimal(10) ** -places      # 2 places --> '0.01'
    try:
        sign, digits, exp = value.quantize(q).as_tuple()
    except:
        return '{:,.0f}'.format(value).replace(',', '.')
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else '0')
    if places:
        build(dp)
    if not digits:
        build('0')
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return ''.join(reversed(result))

def url_viewfull(viewname, **kwargs):
    if kwargs.get('filename'):
        urlfull = resolve_url(viewname, kwargs.get('filename'))
    else:
        urlfull = resolve_url(viewname)
    return urlfull

def format_codigo_barra(codigo_barra):
    codigo_barra = re.sub('-[0-9]+$', '', str(codigo_barra))
    codigo_barra = codigo_barra.lstrip('0').strip()
    return codigo_barra

def mes_palabra(mes):
    if mes == 1:return 'ENERO'
    if mes == 2:return 'FEBRERO'
    if mes == 3:return 'MARZO'
    if mes == 4:return 'ABRIL'
    if mes == 5:return 'MAYO'
    if mes == 6:return 'JUNIO'
    if mes == 7:return 'JULIO'
    if mes == 8:return 'AGOSTO'
    if mes == 9:return 'SETIEMBRE'
    if mes == 10:return 'OCTUBRE'
    if mes == 11:return 'NOVIEMBRE'
    if mes == 12:return 'DICIEMBRE'
    return mes

def dict_int_none(data):
    t_data = copy.deepcopy(data)
    for k, v in t_data.items():
        if v == None:
            data[k] = 0
    return data



