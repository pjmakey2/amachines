"""Basic META CRUD Actions given a model and it's attributes"""
import traceback
from django.conf import settings
from datetime import datetime
import logging
import json, inspect, importlib
from django.apps import apps
from django.forms import model_to_dict
from OptsIO.io_serial import IoS
from OptsIO.io_json import to_json, from_json
from django.core.files import File
from sentry_sdk import capture_exception

get_model = apps.get_model
class IOMaction:
    def process_record(self, *args, **kwargs) -> dict:
        q: dict = kwargs.get('qdict').copy()
        kwargs['qdict'] = q
        logging.info('Proccess record')
        rsps = []
        b_vals = json.loads(q.get('b_vals', "[]"))
        if b_vals:
            e_rsp, args, kwargs = self.execute_validations(b_vals, *args, **kwargs)
            rsps.extend(e_rsp)
            if rsps[-1].get('error'): return {'msgs': rsps, 'qdict': kwargs.get('qdict')}
        #save/update record
        c_a = json.loads(q.get('c_a', "[]"))
        if c_a:
            rsp, args, kwargs = self.execute_validations(c_a, *args, **kwargs)
            rsps.extend(rsp)
            if rsps[-1].get('error'): return {'msgs': rsps, 'qdict': kwargs.get('qdict')}
        else:
            rsp, args, kwargs = self.uc_record(*args, **kwargs)
            rsps.append(rsp)
        a_vals = json.loads(q.get('a_vals', "[]"))
        if a_vals:
            e_rsp, args, kwargs = self.execute_validations(a_vals, *args, **kwargs)
            rsps.extend(e_rsp)
        return { 'msgs': rsps, 'qdict': kwargs.get('qdict') }
    
    def uc_record(self, *args, **kwargs) -> tuple:
        userobj = kwargs.get('userobj')
        ios = IoS()
        rsp = {'success': 'Done!!!'}
        q: dict = kwargs.get('qdict')
        files: dict = kwargs.get('files')
        dbcon: str = q.get('dbcon', 'default')
        model_app_name: str = q.get("model_app_name", '')
        model_name: str = q.get("model_name", '')
        uc_fields: dict = from_json(q.get('uc_fields', "{}"))
        appobj = apps.get_app_config(model_app_name)
        model_class = appobj.get_model(model_name)
        record_delete = uc_fields.pop('record_delete', False)
        state_field = uc_fields.pop('state_field', None)
        ff = ios.form_model_fields(uc_fields, model_class._meta.fields)
        logging.info(f'Keep just fields of the db from the model {ff} and values {uc_fields}')
        for rr in ff:
            uc_fields.pop(rr)
        logging.info(f'Format or Remove {model_class} non used fields from {uc_fields}')
        rnorm, rrm, rbol = ios.format_data_for_db(model_class, uc_fields)
        for c in rrm: uc_fields.pop(c)
        for f, fv in rbol: uc_fields[f] = fv
        for f, fv in rnorm: uc_fields[f] = fv
        pk_field = model_class._meta.pk.name
        logging.info(f'The primary key of the model {model_name} is {pk_field}')
        pk = uc_fields.pop(pk_field, [])
        
        if pk and pk != '':
            logging.info('Set attribute pk to uc_fields')
            uc_fields['pk'] = pk
        logging.info(f'record delete {record_delete} state_field {state_field}')
        if uc_fields.get('pk'):
            logging.info('Beginning update process')
            pk = uc_fields.pop('pk')
            if record_delete and not state_field:
                logging.info('The record is marked for delete')
                if hasattr(model_class, 'anulado_fecha') and hasattr(model_class, 'anulado_usuario'):
                    tnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    logging.info(f'Mark record with pk {pk} with params anulado_fecha = {tnow} and anulado_usuario = {userobj.first_name}')
                    model_class.objects.using(dbcon)\
                        .filter(pk__in=pk).update(
                            anulado_fecha=tnow,
                            anulado_usuario=userobj.first_name
                        )
                else:
                    logging.info(f'Delete record with pk {pk} with params {uc_fields}')
                    model_class.objects.using(dbcon)\
                        .filter(pk__in=pk).delete()
                rsp['success'] = 'Records deleted'
            elif not record_delete and state_field:
                for mobj in model_class.objects.using(dbcon)\
                    .filter(pk__in=pk):
                    vf = getattr(mobj, state_field.get('field'))
                    if vf == state_field.get('as'):
                        setattr(mobj, state_field.get('field'), state_field.get('ds'))
                        logging.info(f'Change state record with pk {mobj.pk} set field {state_field.get("field")} with value {state_field.get("ds")}')
                    elif vf == state_field.get('ds'):
                        setattr(mobj, state_field.get('field'), state_field.get('as'))
                        logging.info(f'Change state record with pk {mobj.pk} set field {state_field.get("field")} with value {state_field.get("as")}')
                    else:
                        setattr(mobj, state_field.get('field'), state_field.get('as'))
                        logging.info(f'Change state record with pk {mobj.pk} set field {state_field.get("field")} with value {state_field.get("as")}')
                    for user_field in ['actualizado_usuario', 'update_user']:
                        if hasattr(model_class, user_field):
                            setattr(mobj, user_field, userobj.first_name)
                    for date_field in ['actualizado_fecha', 'date_update']:
                        if hasattr(model_class, date_field):
                            setattr(mobj, date_field, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    mobj.save()
                rsp['success'] = 'Registro estado actualizado'
            else:
                mobj = model_class.objects.using(dbcon).get(pk=pk)
                u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)
                logging.info('This are the fields to change {u_fields}')
                if not u_fields and not files:
                    return {'info': f'Nada que actualizar'}, args, kwargs
                logging.info(f'Update record with pk {pk} with params {uc_fields}')
                model_class.objects.using(dbcon)\
                    .filter(pk=pk)\
                    .update(
                        **uc_fields)
                logging.info('Set tracking records')
                mobj = model_class.objects.using(dbcon).get(pk=pk)
                for user_field in ['actualizado_usuario', 'update_user']:
                    if hasattr(model_class, user_field):
                        setattr(mobj, user_field, userobj.first_name)
                for date_field in ['actualizado_fecha', 'date_update']:
                    if hasattr(model_class, date_field):
                        setattr(mobj, date_field, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                mobj.save()
                if files:
                    mobj = model_class.objects.using(dbcon).get(pk=pk)
                    for name, fobj in files.items():
                        fname = f'{model_name}_{mobj.pk}_{fobj.name}'
                        dfobj = File(fobj, name=fname)
                        setattr(mobj, name, dfobj)
                    mobj.save()
                rsp['success'] = f'Registro  {pk} actualizado'
        else:
            logging.info(f'Create record with params {uc_fields}')
            if q.get("get_last_pk", ''):
                logging.info('The primary key of the database is not normalized, so we need to get the last ID of the primary key')
                lr = model_class.objects.using(dbcon).only(pk_field).all().order_by(pk_field).last()
                if lr:
                    lpk = getattr(lr, pk_field)+1
                    uc_fields[pk_field] = lpk
            for user_field in ['cargado_usuario', 'save_user']:
                if hasattr(model_class, user_field):
                    uc_fields[user_field] = userobj.first_name
            for date_field in ['cargado_fecha', 'date_save']:
                if hasattr(model_class, date_field):
                    uc_fields[date_field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mobj = model_class.objects.using(dbcon).create(
                **uc_fields
            )
            if files:
                mobj = model_class.objects.using(dbcon).get(pk=pk)
                for name, fobj in files.items():
                    fname = f'{model_name}_{mobj.pk}_{fobj.name}'
                    dfobj = File(fobj, name=fname)
                    setattr(mobj, name, dfobj)
                    mobj.save()
            rsp['success'] = f'Registro {mobj.pk} creado'
        kwargs['qdict']['uc_fields'] = to_json(uc_fields)
        return rsp, args, kwargs

    def execute_validations(self, e_vals, *args, **kwargs) -> tuple:
        rsps = []
        for e_val in e_vals:
            logging.info(f'Running validation {e_val}')
            module = e_val.get('module')
            package = e_val.get('package')
            attr = e_val.get('attr')
            mname = e_val.get('mname')
            cont = e_val.get('cont')
            show_success = e_val.get('show_success')
            dobj = getattr(importlib.import_module(f'{module}.{package}'), attr)
            if inspect.isclass(dobj):
                cls = dobj()
                dobj = getattr(cls, mname)
                try:
                    rsp, args, kwargs = dobj(*args, **kwargs)
                except Exception as e:
                    capture_exception()
                    msg_e = f'{traceback.format_exc()}'
                    # if settings.DEBUG:
                    #     msg_e += f"""
                    #     <div class="">
                    #         <h3>TRACKING SYSTEM</h3>
                    #         <ul>
                    #         <li>module = {module}</li>
                    #         <li>package = {package}</li>
                    #         <li>attr = {attr}</li>
                    #         <li>mname = {mname}</li>
                    #         <li>con = {cont}</li>
                    #         </ul>
                    #     </div>
                    #     """
                    logging.error(f'Error validation {e_val} - {msg_e}')
                    if not cont: return [{'error': msg_e }], args, kwargs
                    rsps.append({'error': msg_e})
                else:
                    if rsp.get('error'): 
                        logging.error(rsp.get('error'))
                        mme = f"""
                            <div class="">
                                <h3>TRACKING SYSTEM</h3>
                                <ul>
                                <li>module = {module}</li>
                                <li>package = {package}</li>
                                <li>attr = {attr}</li>
                                <li>mname = {mname}</li>
                                <li>con = {cont}</li>
                                </ul>
                            </div>
                            """
                        logging.error(mme)
                        # if settings.DEBUG:
                        #     rsp['error'] += mme
                        if not cont: return [rsp], args, kwargs
                    rsp['show_success'] = show_success
                    rsps.append(rsp)
            else:
                try:
                    rsp, args, kwargs = dobj(*args, **kwargs)
                except Exception as e:
                    capture_exception()
                    msg_e = f'{traceback.format_exc()}'
                    if settings.DEBUG:
                        msg_e += f"""
                        <div class="bg-white">
                            <h3>TRACKING SYSTEM</h3>
                            <ul>
                            <li>module = {module}</li>
                            <li>package = {package}</li>
                            <li>attr = {attr}</li>
                            <li>mname = {mname}</li>
                            <li>con = {cont}</li>
                            </ul>
                        </div>
                        """                    
                    logging.error(f'Error validation {e_val} - {traceback.format_exc()}')
                    if not cont: return [{'error': msg_e}], args, kwargs
                    rsps.append({'error': msg_e})
                else:
                    if rsp.get('error'): 
                        if settings.DEBUG:
                            rsp['error'] += f"""
                            <div class="bg-white">
                                <h3>TRACKING SYSTEM</h3>
                                <ul>
                                <li>module = {module}</li>
                                <li>package = {package}</li>
                                <li>attr = {attr}</li>
                                <li>mname = {mname}</li>
                                <li>con = {cont}</li>
                                </ul>
                            </div>
                            """
                        logging.error(rsp.get('error'))
                        if not cont: return [rsp], args, kwargs
                    rsp['show_success'] = show_success
                    rsps.append(rsp)
        return rsps, args, kwargs
