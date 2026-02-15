"""Handle of grid behaviours in the BE"""
import re
import inspect, importlib
import json
from django.apps import apps
from OptsIO.io_serial import IoS

get_model = apps.get_model
class IoG:
    def get_records(self, *args, **kwargs) -> dict:
        ios = IoS()
        qdict = kwargs.get('qdict').copy()
        if qdict.get('format') == 'datatables':
            ffq = self.datatables_parse_request(qdict)
            dsearch = qdict.get('search[value]', '')
            if dsearch:
                fse = self.datatables_parse_search(qdict)
                qdict.update({'mquery': json.dumps(fse)})
            qdict.update(ffq)
            if qdict.get('custom_module'):
                module = qdict.get('custom_module')
                package = qdict.get('custom_package')
                attr = qdict.get('custom_attr')
                mname = qdict.get('custom_mname')
                dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
                if inspect.isclass(dobj):
                    if not mname: 
                        return {'error': 'Falta proveer el metodo para la ejecucion'}
                    cls = dobj()
                    dobj = getattr(cls, mname)
                #converge mysql user with django user
                rq = kwargs.get('rq')
                records = dobj(userobj=kwargs.get('userobj'), 
                            rq=rq,
                            files=rq.FILES,
                            qdict=qdict, 
                            )
                
            else:
                records = ios.seModel(qdict=qdict)
            return self.datatables_records(qdict, records)
        
    def datatables_parse_search(self, dtr: dict) -> list:
        ios = IoS()
        always_initquery = json.loads(dtr.get('always_initquery'))
        mquery = []
        if always_initquery:
            mquery = json.loads(dtr.get('mquery'))
        search = dtr.get('search[value]', '')
        model_app_name: str = dtr.get("model_app_name", '')
        model_name: str = dtr.get("model_name", '')
        appobj = apps.get_app_config(model_app_name)
        model_class = appobj.get_model(model_name)
        cols_fields = filter(lambda x: x.startswith('columns['), dtr.keys())
        fields = set(json.loads(dtr.get('fields')))
        methods = set(json.loads(dtr.get('methods')))
        c_idx = set()
        [ c_idx.add(re.findall('\[[0-9]+\]', co)[0].strip('[]')) for co in cols_fields ]
        fsq = set()
        for co in c_idx:
            cda = dtr.get(f'columns[{co}][data]').strip()
            if cda == '': continue
            fsq.add(cda)
        fsq = fsq.difference(methods)
        fsq = fsq.intersection(fields)
        for f in fsq:
            finte = ios.get_internal_types(model_class, f)
            if finte in ['FloatField',
                         'IntegerField',
                         'DecimalField',
                         ]:
                try:
                    int(search)
                except:
                    continue
                else:
                    mquery.append({'field': f'or_{f}', 'value': int(search)})
            else:
                mquery.append({'field': f'or_{f}__icontains', 'value': search})
        return mquery

    def datatables_parse_request(self, dtr: dict) -> dict:
        c_query_r = {
            'pq_sort': "[]",
            'pq_filter': "[]",
            'pdopts': json.dumps({
                'fillna': 0
            }),
            'startRow': 0,
            'endRow': 0
        }
        pq_sort = []
        order_fields = filter(lambda x: x.startswith('order['), dtr.keys())
        o_index = set()
        [ o_index.add(re.findall('\[[0-9]+\]', oo)[0].strip('[]')) for oo in order_fields ]
        for oo in o_index:
            o_cl = dtr.get(f'order[{oo}][column]')
            c_name: str = dtr.get(f'columns[{o_cl}][data]', '').strip()
            orde = dtr.get(f'columns[{o_cl}][orderable]')
            i_name = dtr.get(f'columns[{o_cl}][name]')
            if orde != 'true': continue
            if c_name == '': continue
            dire = o_cl = dtr.get(f'order[{oo}][dir]')
            pq_sort.append({
                'dataIndx': c_name,
                'dir': 'down' if dire == 'desc' else '',
                'method': True if i_name.strip() != '' else False
            })
        length = int(dtr.get('length', 100))
        if (length < 0):
            length = 10
        c_query_r['pq_sort'] = json.dumps(pq_sort)
        c_query_r['startRow'] = int(dtr.get('start', 0))
        c_query_r['endRow'] = int(dtr.get('start', 0) ) + length
        return c_query_r
    
    def datatables_records(self, qdict: dict, records: dict) -> dict:
        trows: int = records.get('trows', 0)
        qs = records.get('qs', [])
        qsr = len(qs)
        if not qsr: qsr = 1
        return {
            "draw": int(qdict.get('draw', 1))+1,
            "recordsTotal": trows,
            "recordsFiltered": trows,
            'data': qs
        }
        