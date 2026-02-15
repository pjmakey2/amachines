import types
import numpy as np
import datetime, calendar, importlib, json, re
import pandas as pd
from django.forms import model_to_dict
from django.db.models import Q, F
import logging

class FConstruc:
    def __init__(self):
        pack_metrics = 'django.db.models'
        self.popts = [
			"model_app_name",
			"model_name",
			"app_name",
			"module_name",
			"class_name",
			"method_name",
			"groupby_a",
			"precision",
			"metrics_a",
			"metrics_total",
			"timefield",
			"rep_cols",
			"ag_values",
			"output",
			"fields",
			"qexc",
			"amounts",
            "__range"
        ]        
        self.summary_types = {
            'sum': getattr( importlib.import_module(pack_metrics), 'Sum'),
            'avg': getattr( importlib.import_module(pack_metrics), 'Avg'),
            'max': getattr( importlib.import_module(pack_metrics), 'Max'),
            'min': getattr( importlib.import_module(pack_metrics), 'Min'),
            'count': getattr( importlib.import_module(pack_metrics), 'Count'),
            'last': getattr( importlib.import_module(pack_metrics), 'Max'),
            'first': getattr( importlib.import_module(pack_metrics), 'Min'),
        }        
        self.f_types = {
            'float': getattr( importlib.import_module(pack_metrics), 'FloatField'),
            'integer': getattr( importlib.import_module(pack_metrics), 'IntegerField'),
            'binteger': getattr( importlib.import_module(pack_metrics), 'BigIntegerField'),
            'char': getattr( importlib.import_module(pack_metrics), 'CharField'),
        }        

    def querydict_params(self, q:list, exclude:list):
        lexc = ['columns', '^start$', 'draw', 'length', 'search','order',r'\b-\b', 'filtro', r'\b_\b',
                'from_palletl', 'interface', 'demo', 'key_name', 'app_name',
                'model_name', 'model_key', 'api_key', 'method_call', '^nor_', '^or_',
                'distinct_value', 'class_name', 'method_name', 'app_name', 'module_name', 'serial_model',
                'type_datatable', 'init', 'last', 'pq_datatype', 'pq_rpp', 'dparamquery', 'pq_curpage',
                'pq_filter', 'pq_sort', 'lookup','callback', 'jsonp', 'explicit_key', 'order_field',
                'mcache', 'sckey', 'clzs', 'qcache','type_datatable', 'init', 'last', 'pq_datatype',
                'pq_rpp', 'dparamquery', 'pq_curpage', 'pq_filter','pq_sort','callback', 'jsonp',
                'explicit_key', 'order_field','type_datatable', 'init', 'last', 'pq_datatype',
                'pq_rpp', 'dparamquery', 'pq_curpage', 'pq_filter','pq_sort', 'lookup',
                'app_name', 'model_name', 'module_name', 'class_name','method_name', 'pq_datatype', '^pk', 'model_app',
                'groupby_a', 'metrics_a', 'summary_a', 'timefield', 'metrics_total', 'precision', 'output','model_app_name',
                'rep_cols', 'percent_pergroup', 'ag_values', 'qex', 'skols', 'fields', 'sfields',
                'dif_query', 'amounts', 'agrq', 'grid_time_dimesion', 'package', 'module', 'attr', 'mname', 'dbcon','io_task',
                "torient", "sort_values", "pdopts", "dj_eval", 'detail_objs'
                ]
        lexc.extend(exclude)
        params = {}
        lexc = map(str, lexc)
        rsearch = '|'.join(lexc)
        for l in q:
            key = l[0].split('^')[-1]
            if re.search('startswith|endswith', key) and len(l[1]) > 1:
                continue
            if re.search(rsearch, key):
                continue
            if isinstance(key, str):
                if key.strip() == '':
                    continue
            key = key.replace('[]', '')
            if not l[1]:
                continue
            if len(l[1]) > 1:                                
                if re.search('__range', key):
                    params.update({key: l[1] })
                else:
                    params.update({'%s__in' % key: l[1] })
            else:
                
                if isinstance(l[1][0], bool):
                    params.update({key:  l[1][0] })
                    continue
                #if isinstance(l[1][0], str) or isinstance(l[1][0], unicode):
                if isinstance(l[1][0], str):
                    if len(l[1][0].split('|')) > 1 and not key.endswith('regex'):
                        params.update({'%s__in' % key: l[1][0].split('|') })
                        continue
                    if l[1][0].strip() == '':
                        continue
                    if l[1][0].strip() == 'on':
                        params.update({key: True })
                        continue
                # implements F queries
                if key.startswith('f__'):
                    params.update(self.setf_querie(key, l[1][0]))
                    continue
                vvf = l[1][0]
                try: vvf = int(vvf)
                except: 
                    if vvf is not None:
                        vvf = vvf.strip()
                params.update({key: vvf})
                # try:
                #     #if isinstance(l[1][0], str) or isinstance(l[1][0], unicode):
                #     if isinstance(l[1][0], str):
                #         params.update({key: int(l[1][0].strip())})
                #     else:
                #         params.update({key: int(l[1][0])})
                # except:
                #     params.update({key: l[1][0].strip()})
        return params        
    
    def sorted_fields(self, model_class, fields: list):
        # {'dataIndx': 'get_embarques', 'dir': 'down', 'method': False}]
        remove_idx = []
        pq_sort_method = []
        for idx, l in enumerate(fields):
            field = l.get('dataIndx')
            if not hasattr(model_class, field):
                continue
            fmodel = getattr(model_class, field)
            if isinstance(fmodel, types.FunctionType):
                remove_idx.append(idx)
                pq_sort_method.append({'dataIndx': field, 'dir': l.get('dir'), 'method': False})
        fields = [f for i, f in enumerate(fields) if i not in remove_idx]
        return fields, pq_sort_method


    def querydict_args(self, q: list):
        q_search = None
        for l in q:
            vv = l[0].split('^')
            if len(vv) > 1:
                operator, or_q =  vv
                operator = operator.replace('OPERATOR=', '').strip()
            else:
                or_q = vv[-1]
                operator = 'OR'
            if not l[1]:
                continue
            if re.search('startswith|endswith', or_q) and len(l[1]) > 1:
                for vv in l[1]:
                    key =  or_q.replace('or_', '')
                    tmp_p = {key: vv}                    
                    tmp_search = Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search
                    else:
                        q_search = tmp_search                    
                continue            
            if or_q.startswith('or_'):
                key =  or_q.replace('or_', '')
                if re.search('__range', key):
                    tmp_p = {key: l[1]}
                    tmp_search = Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search
                    else:
                        q_search = tmp_search
                    continue
                if re.search('__icontains', key):
                    for vv in l[1]:
                        tmp_p = {key: vv}                    
                        tmp_search = Q(**tmp_p)
                        if q_search:
                            if operator == 'AND':
                                q_search &= tmp_search
                            else:
                                q_search |= tmp_search
                        else:
                            q_search = tmp_search                    
                    continue                
                if len(l[1]) > 1:                    
                    tmp_p = {'{}__in'.format(key): l[1]}
                    tmp_search = Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search
                    else:
                        q_search = tmp_search                                        
                    continue
                else:
                    tmp_p = {'{}'.format(key): l[1][0]}
                    tmp_search = Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search                        
                    else:
                        q_search = tmp_search                                        
                    continue
            if or_q.startswith('nor_'):
                key =  or_q.replace('nor_', '')
                if re.search('__range', key):
                    tmp_p = {key: l[1]}
                    tmp_search = ~Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search                                                
                    else:
                        q_search = tmp_search
                    continue
                if re.search('__icontains', key):
                    for vv in l[1]:
                        tmp_p = {key: vv}                    
                        tmp_search = ~Q(**tmp_p)
                        if q_search:
                            if operator == 'AND':
                                q_search &= tmp_search
                            else:
                                q_search |= tmp_search                                                                            
                        else:
                            q_search = tmp_search                                        
                    continue                
                if len(l[1]) > 1:
                    tmp_p = {'{}__in'.format(key): l[1]}
                    tmp_search = ~Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search                                                                                                    
                    else:
                        q_search = tmp_search                                        
                    continue                
                else:
                    tmp_p = {'{}'.format(key): l[1][0]}
                    tmp_search = ~Q(**tmp_p)
                    if q_search:
                        if operator == 'AND':
                            q_search &= tmp_search
                        else:
                            q_search |= tmp_search                                                                                                                            
                    else:
                        q_search = tmp_search                                        
                    continue                                    

        if not q_search: return Q()
        return q_search        

    def setf_querie(self, key: str, field: str):
        t, con, kfield = key.split('__')
        comp_field = F(field)
        rdict = {}
        if con == 'equal':
            rdict[kfield] = comp_field
        if con == 'gt':
            rdict['{}__gt'.format(kfield)] = comp_field
        if con == 'lt':
            rdict['{}__lt'.format(kfield)] = comp_field
        if con == 'gte':
            rdict['{}__gte'.format(kfield)] = comp_field
        if con == 'lte':
            rdict['{}__lte'.format(kfield)] = comp_field
        return rdict        

    def structFields(self, only: list):
        sfields = []
        for f in only:
            if f.find('__') >= 0:
                sfields.append(f)
        return sfields        

    def constructFexpr(self, field_list: list, operator_list: list):
        """Fexpr = {'fields': ['precio_unitario', 'cantidad', 'cantidad_devoulucion', 1000],
         'operators': ['*', '-', '/'] } #a minus one because the first field is the base of the function
        """
        main_f = F(field_list.pop(0))
        for i, field in enumerate(field_list):
            if isinstance(field, int):
                if operator_list[i] == '+':
                    main_f = main_f + field
                if operator_list[i] == '-':
                    main_f = main_f - field                    
                if operator_list[i] == '*':
                    main_f = main_f * field                                        
                if operator_list[i] == '/':
                    main_f = main_f / field  
                continue
            if operator_list[i] == '+':
                main_f = main_f + F(field)
            if operator_list[i] == '-':
                main_f = main_f - F(field)
            if operator_list[i] == '*':
                main_f = main_f * F(field)
            if operator_list[i] == '/':
                main_f = main_f / F(field)
        return main_f                

    def pquerysort(self, qd: dict, pq_sort: list, model_class=None):
        # Even if the method is considered as ordering methods via pandas,
        # when using front-end tools like DataTables or PQGrid, the ordering
        # is applied according to the formatting rules of those libraries.
        # This is why this method can receive the model_class, to check
        # whether a field is a method or not.
        if model_class:
            pq_sort, pq_sort_method_construct = self.sorted_fields(model_class, pq_sort)
        for order in pq_sort:
            if order.get('method'): continue
            okey = order.get('dataIndx')
            direc = order.get('dir')
            if direc == 'down':
                okey = '-{}'.format(okey)
            qd.update({'order_field': okey})
            #order_by.append(okey.replace('__foreign', ''))
        if not model_class: return qd
        return qd, pq_sort_method_construct

    def pqueryfilter(self, qd: dict, pqfilter: dict):
        cond_search = {
            "begin": '__istartswith',
            "contain": '__icontains',
            "notcontain": '__icontains',
            "equal": '',
            "notequal": '',
            "empty": '__isnull',
            "notempty": '__isnull',
            "end": '__iendswith',
            "less":'__lte',
            "great": '__gte',
            "between": '__range',
            "range": '__in',
            "regexp": '__regex',
            "notbegin": '__istartswith',
            "notend": '__iendswith',
            "lte": '__lte',
            "gte": '__gte'
        }
        for pq in pqfilter.get('data', []):
            condition = pq.get('condition')
            csearch = cond_search.get(condition)
            field = pq.get('dataIndx')
            sfield = '{}{}'.format(field, csearch)
            if condition in ['notequal', 'equal']: sfield = field
            value = pq.get('value')
            value2 = pq.get('value2')
            if condition in ['contain'] and len(value.split(',')) > 1:
                sfield = '{}__in'.format(field)
                qd[sfield] = []
                for v in value.split(','):
                    qd[sfield].append(v)
                continue
            if condition in ['notcontain', 'notend', 'notbegin', 'notequal']:
                qd.update({'nor_{}'.format(sfield): value})
                continue
            if condition != 'between':
                qd[sfield] = value
            else:
                qd[sfield] = (value, value2)
        return qd

    def insertCast(self, fields: list, values: list, mobj):
        pps = {}
        for f, v in zip(fields, values):
            intert = mobj._meta.get_field(f).get_internal_type()
            if intert == 'JSONField':
                if isinstance(v, str) or isinstance(v, unicode):
                    pps[f] = json.loads(v)
        return pps

    def week_of_month(self, tgtdate):
        days_this_month = calendar.mdays[tgtdate.month]
        for i in range(1, days_this_month):
            d = datetime.datetime(tgtdate.year, tgtdate.month, i)
            if d.day - d.weekday() > 0:
                startdate = d
                break
        # now we canuse the modulo 7 appraoch
        return (tgtdate - startdate).days // 7 + 1        

    def constructDf(self, qs: list, pdopts: dict):
        rsp = {}
        replace_inf = pdopts.get('replace_inf', False)
        df = pd.DataFrame(qs)
        rsp['df'] = df
        cols = list(df.columns)
        rsp['cols'] = cols
        #TODO: Call the a method to construct the dataframe
        if pdopts.get('date_fields'):
            for f in pdopts.get('date_fields'):
                if f.get('field') not in cols: continue
                df[f.get('field')] = pd.to_datetime(df[f.get('field')], format=f.get('format'))
            rsp['df'] = df
        if pdopts.get('colorder'):
            df = df[pdopts.get('colorder')]
            rsp['df'] = df
        if pdopts.get('eval'):
            for ev in pdopts.get('eval'):
                df[ev.get('column')] = pd.eval(ev.get('expr'), target=df)
            rsp['df'] = df
        if pdopts.get('drop_zeros'):
            df = df.loc[~ (df.fillna(value=0).select_dtypes(include=['number']) == 0).all(axis='columns'), :]
            rsp['df'] = df
        if pdopts.get('time_dimension'):
            for t in pdopts.get('time_dimension'):
                field = t.get('field')
                if field not in cols: continue
                dim = t.get('dim')
                ncol = '{}__{}'.format(field, dim)
                cols.append(ncol)
                if dim == 'week_day':
                    df[ncol] = getattr(df[field].dt, 'weekday')
                    continue
                if dim == 'week_month':
                    df[ncol] = df[field].apply(self.week_of_month)
                    continue
                df[ncol] = getattr(df[field].dt, dim)
            rsp['df'] = df
            rsp['cols'] = cols
        if pdopts.get('drop_columns'):
            df = df.drop(columns=pdopts.get('drop_columns'))
            rsp['df'] = df
        if pdopts.get('pivot_structure'):
            pe = pdopts.get('pivot_structure')
            index = pe.get('index')
            columns = pe.get('columns')
            values = pe.get('values')
            aggfunc = pe.get('aggfunc')

            eopts = pe.get('eopts')
            
            dfp = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            )
            pivot_columns = dfp.columns.to_list()
            if eopts:
                if eopts.get('count_row_values'):
                    rcol = eopts.get('count_row_values')
                    dfp[rcol] = dfp.count(axis=1)
                    pivot_columns.append(('agg','', rcol))
            df = dfp.reset_index()
            cols = []
            for c in df.columns.to_list():
                if c[-1] == '':
                    cols.append(c[0])
                else:
                    cols.append(c[-1])
            df.columns = cols
            rsp['cols'] = cols
            rsp['df'] = df
            rsp['pivot_columns'] = pivot_columns
        #df.to_csv('/tmp/test.csv', sep='|', index=False, encoding='utf-8')
        if pdopts.get('sort_values') and df.shape[0] > 0:
            if pdopts.get('sort_ascending'):
                df.sort_values(
                            by=pdopts.get('sort_values'),
                            ascending=pdopts.get('sort_ascending'),
                            inplace=True
                )
            else:
                df.sort_values(by=pdopts.get('sort_values'), inplace=True)
            #rsp['df'] = df

        if replace_inf:
            df.replace([np.inf, -np.inf], 0, inplace=True)
            rsp['df'] = df
        if pdopts.get('fillna') or pdopts.get('fillna') == 0:
            df.fillna(pdopts.get('fillna'), inplace=True)
            rsp['df'] = df
        return rsp
    

    def sfields(self, mobj, efields: list, fields: list, allfields: bool = False, detail_objs: list = []):
        return self.rfields(mobj, efields, fields, allfields=allfields, detail_objs=detail_objs)
    
    def rfields(self, mobj, sfields: list, fields: list, normalize: list=[], allfields: bool = False, detail_objs: list = []):
        if fields:
            x = model_to_dict(mobj, fields=fields)
        elif allfields:
            x = model_to_dict(mobj)
        else:
            x = {}
            # x = model_to_dict(mobj)
        for hf in  filter(lambda x: x.endswith('_id'), fields):
            x[hf] = getattr(mobj, hf)
        x['pk'] = mobj.pk
        x['id'] = mobj.pk
        x['DT_RowId'] = f'{mobj._meta.model_name}{mobj.pk}'
        for ff in sfields:
            value = self.get_modelfield(mobj, ff)
            x[ff] = value
        if detail_objs:
            logging.info('Get detail objs from father')
            for deobj in detail_objs:
                dset = deobj.get('dset', '')
                x[dset] = []
                for do in getattr(mobj, dset).filter(**deobj.get('dfilter', {})).order_by(*deobj.get('order_by', [])):
                    dx = self.rfields(do, 
                            deobj.get('sfields', []),
                            deobj.get('fields', []),
                            deobj.get('normalize', []),
                            deobj.get('allfields', False),
                            deobj.get('detail_objs', []),
                        )
                    x[dset].append(dx)
        if normalize:
            return self.snormalize(x, sfields+fields, normalize)
        return x
    
    def get_modelfield(self, instance, field: str):
        field_path = field.split('__')
        lfp = len(field_path)
        if len(field_path) > 1:
            attr = field_path[-1]
            for idx, fattr in enumerate(field_path):
                if idx+1==lfp:
                    if not instance: return None
                    attr = getattr(instance, attr)
                    if getattr(attr, '__func__', None):
                        return attr()
                    return attr
                if not instance: return None
                instance = getattr(instance, fattr)
        attr = getattr(instance, field)
        if getattr(attr, '__func__', None):
            return attr()
        return attr
    
    def get_modelfield_internal_type(self, mobj, field: str):
        field_path = field.split('__')
        lfp = len(field_path)
        if len(field_path) > 1:
            for idx, fattr in enumerate(field_path):
                if idx+1==lfp:
                    if hasattr(mobj, 'get_internal_type'):
                        if mobj.get_internal_type() == 'JoinField':
                            mobj = mobj.related_model
                    return mobj._meta.get_field(fattr).get_internal_type()
                mobj = mobj._meta.get_field(fattr)
                if mobj.get_internal_type() == 'ForeignKey':
                    mobj = mobj.related_model
        if field == 'pk':
            return 'IntegerField'
        itype = mobj._meta.get_field(field).get_internal_type()
        return itype
    
    def snormalize(self, x: dict, keys: list, normalize: list):
        xt = {}
        for norm, k in zip(normalize, keys):
            xt[norm] = x[k]
        return xt
