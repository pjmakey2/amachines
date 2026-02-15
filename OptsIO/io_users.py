#coding: utf-8
import arrow
import pandas as pd
from tqdm import tqdm
from datetime import date, datetime
import hashlib, secrets
import logging
from django.contrib.auth.models import Permission, Group, User
from django.contrib.contenttypes.models import ContentType
from apps.FL_Structure.models import Usuarios, Sucursal, Perfiles, Ofremota, Clientes
from OptsIO.models import SysParams
from OptsIO.io_serial import IoS
from OptsIO.io_json import to_json, from_json
from apps.OptsTrack.models import UserProfile
from django.forms import model_to_dict
from django.db.models import Q
from django.conf import settings
from django.core.files import File
from django.db.utils import IntegrityError
import os, json
from django.apps import apps
from django.core.cache import caches

get_model = apps.get_model




class IOUser:
    def __init__(self):
        self.dbcon = 'fl'

    def check_grouppermission(self, *args: list, **kwargs: dict) -> tuple:
        q = kwargs.get('qdict').copy()
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        if not uc_fields.get('permissions'):
            return {'error': 'No se han seleccionado permisos' }, args, kwargs
        
        if not uc_fields.get('usuarios'):
            return {'error': 'No se han seleccionado usuarios' }, args, kwargs
        
        if Group.objects.filter(name=uc_fields.get('name').strip()):
            return {'error': f'El grupo {uc_fields.get("name")} ya existe' }, args, kwargs
        return {'success': 'Hecho' }, args, kwargs
    
    def create_grouppermission(self, *args: list, **kwargs: dict) -> tuple:
        q = kwargs.get('qdict').copy()
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        group = Group.objects.create(name=uc_fields.get('name'))
        group.permissions.set(
            Permission.objects.filter(pk__in=uc_fields.get('permissions'))
        )
        for u in uc_fields.get('allowed_users'):
            userobj, created = User.objects.get_or_create(username=u)
            try:
                ufl = Usuarios.objects.using('fl').get(funcionariocodigo=u)
            except:
                pass
            else:
                userobj.first_name = f'{ufl.funcionarionombre} {ufl.funcionarioapellido}'[0:150]
            userobj.save()
            userobj.groups.add(group)
        return {'success': 'Hecho' }, args, kwargs
    
    def update_grouppermission(self, *args: list, **kwargs: dict) -> tuple:
        q = kwargs.get('qdict').copy()
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        group = Group.objects.get(pk=uc_fields.get('id'))
        group.permissions.clear()
        group.user_set.clear()
        group.permissions.set(
            Permission.objects.filter(pk__in=uc_fields.get('permissions'))
        )
        Group.objects.filter(pk=uc_fields.get('id')).update(
            name=uc_fields.get('name')
        )
        for u in uc_fields.get('allowed_users'):
            userobj, created = User.objects.get_or_create(username=u)
            try:
                ufl = Usuarios.objects.using('fl').get(funcionariocodigo=u)
            except:
                pass
            else:
                userobj.first_name = f'{ufl.funcionarionombre} {ufl.funcionarioapellido}'[0:150]
            userobj.save()
            userobj.groups.add(group)
        return {'success': 'Hecho' }, args, kwargs

    def add_permission(self, *args: list, **kwargs: dict) -> tuple:
        q = kwargs.get('qdict').copy()
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        Permission.objects.get_or_create(
                codename=uc_fields.get('codename'),
                name=uc_fields.get('name'),
                content_type=ContentType.objects.get(model='sysparams')
        )
        return {'success': 'Hecho' }, args, kwargs


    def compare_password(self, *args, **kwargs) -> tuple:
        q: dict = kwargs.get('qdict')
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        funcionariopassword = uc_fields.get('funcionariopassword').strip()
        funcionariopassword_2 = uc_fields.get('funcionariopassword_2').strip()
        if (funcionariopassword != funcionariopassword_2):
            return {'error': 'Las claves no coinciden'}, args, kwargs
        return {'success': 'Clave comparada'}, args, kwargs

    def hash_password(self, *args, **kwargs) -> tuple:
        q: dict = kwargs.get('qdict')
        uc_fields: dict = json.loads(q.get('uc_fields', "{}"))
        funcionariopassword = uc_fields.get('funcionariopassword') 
        uc_fields['funcionariopassword'] = hashlib.md5(funcionariopassword.encode('utf-8')).hexdigest()
        kwargs['qdict']['uc_fields'] = json.dumps(uc_fields)
        return {'success': 'Password encriptado'}, args, kwargs
    




    def get_random_password(self, length=13):
        return secrets.token_urlsafe(length)

    def create_admin(self):
        uname = 111111
        userobj, c = User.objects.get_or_create(
            username=uname,
            email='unemailvalido',
            first_name='FL',
            last_name='ADMIN',
            is_active=True,
        )
        tpass = self.get_random_password()
        userobj.set_password(tpass)
        userobj.save()
        ggs = [
            'administrador',
            'atencion',
            'dlc_deposito',
            'dlc_atencion',
            'monitor_deposito',
            'monitor_dlc',
            'monitor_recepcion',
            'raspberry',
            'solicitud_api',
            'tablet_turnero',
        ]
        for g in Group.objects.filter(name__in=ggs):
            userobj.groups.add(g)
        mresult = hashlib.md5(tpass.encode()).hexdigest()
        Usuarios.objects.using('fl').filter(
            funcionariocodigo=uname
        ).update(funcionariopassword=mresult)
        
        return {'success': 'Hecho'}
    
    def call_predefined_permissions(self, *args, **kwargs) -> dict:
        q: dict = kwargs.get('qdict', {})
        BDIR = settings.BASE_DIR
        self.predefined_permissions(sps_file=f"{BDIR}/_docs/permisos/Permisos sistema_core.xlsx")
        return {'success': 'Hecho'}

    def predefined_permissions(self, sps_file=None):
        logging.info('Corriendo predefined_permissions')
        prefix = 'perms.OptsIO.'
        gggs = [
            'ATC Basico',
            'ATC Supervisor',
            'Operador de Registro paquetes',
            'ADM',
            'ADM Master',
            'Manager de Sucursal',
            'Depositero (Recepcion local)',
            'Asesor de compras',
            'Cajero',
            'Operaciones/ Gestiones Aduaneras',
            'Operador DLC',
            'Auxiliar ADM',
            'Contable',
        ]
        # Group.objects.filter(
        #     name__in=gggs,
        # ).delete()
        for g in gggs:
            gobj, bb = Group.objects.get_or_create(name=g)
            gobj.permissions.clear()
            logging.info(f'Eliminando permisos del grupos {g}')
        if not sps_file:
            mge = 'No se ha definido el archivo de permisos'
            logging.info(mge)
            raise Exception(mge)
        logging.info(f'Leyendo archivo {sps_file}')
        df = pd.read_excel(sps_file, sheet_name='sistematizado')
        GROUPS = list(df.columns)
        for a in range(3):
            GROUPS.pop(0)
        for group in GROUPS:
            logging.info(f'Creando grupo {group}')
            group, bb = Group.objects.get_or_create(name=group)
            #logging.info('Limpiando permisos del grupo {}'.format(group))
            #group.user_set.clear()
        group, bb = Group.objects.get_or_create(name='minimal_ui')
        #logging.info('Limpiando permisos del grupo {}'.format(group))
        #group.user_set.clear()

        #for holder, pdata in tqdm(DPERMS.items()):
        for idx, pdata in df.iterrows():
            #for pmd in pdata:
            #perm = f'{prefix}{pdata.Perm}'
            pobj, created = Permission.objects.get_or_create(
                    codename=pdata.Perm,
                    content_type=ContentType.objects.get(model='sysparams')
            )
            #pobj.name = f"{pmd.get('gname')}->{pmd.get('pname')}"
            pobj.name = f"{pdata.Menu} -> {pdata.Elemento}"
            pobj.save()
            logging.info(f'Creando permiso codename = {pdata.Perm} name = {pdata.Elemento}->{pdata.Menu}')
            for g in GROUPS:
                copts = pdata[g]
                if copts.strip() == 'SI':
                    group = Group.objects.get(name=g)
                    if not group.permissions.filter(codename=pdata.Perm):
                        logging.info(f'Asignando permiso {pdata.Perm} al grupo {g}')
                        group.permissions.add(pobj)
        #Mapping user groups
        # dfu = pd.read_excel(sps_file, sheet_name='user_mapping')
        # for idx, r in dfu.iterrows():
        #     logging.info('Mapeando grupos a usuario {}'.format(dict(r)))
        #     if not Usuarios.objects.using('fl').filter(funcionariocodigo=r.codigo):
        #         Usuarios.objects.using('fl').create(
        #             funcionariocodigo=r.codigo,
        #             funcionarionombre=r.nombre,
        #             funcionarioapellido=r.apellido,
        #             funcionariofecharegistro=datetime.now(),
        #             funcionarioestado=1,
        #             funcionariopassword = hashlib.md5(b'123456').hexdigest()
        #         )
        #     if not User.objects.filter(username=r.codigo):
        #         uobj = User.objects.create(
        #             username=r.codigo,
        #             first_name=r.nombre,
        #             last_name=r.apellido
        #         )
        #         uobj.set_password('123456')
        #         uobj.save()
        #     if not UserProfile.objects.filter(userobj=r.codigo):
        #         UserProfile.objects.create(
        #             userobj = r.codigo,
        #             username = f'{r.nombre}, {r.apellido}',
        #             first_login = False,
        #             last_changepassword = None,
        #             password_timechange = 90,
        #             password_next_change = arrow.get().shift(months=3).strftime('%Y-%m-%d'),
        #         )
        #     userobj = User.objects.get(username=r.codigo)
        #     for g in GROUPS:
        #         copts = r[g]
        #         if copts.strip() == 'SI':
        #             group = Group.objects.get(name=g)
        #             if not userobj.groups.filter(name=g):
        #                 logging.info(f'Asignando grupo {g} al usuario {r.codigo}')
        #                 userobj.groups.add(group)
        # groupobj = Group.objects.get(name='Depositero (Recepcion local)')
        # gm, bb = Group.objects.get_or_create(name='minimal_ui')
        # for c in groupobj.user_set.all():
        #     c.groups.add(gm)

        # u = [
        #     (111228, 'Operador de Registro paquetes'),
        #     (111219, 'ADM Master'),
        #     (111221, 'ATC Basico'),
        #     (111223, 'Auxiliar ADM'),
        #     (111225, 'Depositero (Recepcion local)'),
        #     (111218, 'ADM'),
        #     (111227, 'Operaciones/ Gestiones Aduaneras'),
        #     (111220, 'Asesor de compras'),
        #     (111222, 'ATC Supervisor'),
        #     (111224, 'Cajero'),
        #     (111226, 'Manager de Sucursal'),
        #     (111229, 'Contable'),
        # ]

        # for uu, ll in u:
        #     userobj = User.objects.get(username=uu)
        #     groupobj = Group.objects.get(name=ll)
        #     userobj.groups.add(groupobj)

        return {'success': 'Done!!!'}
    
    def set_tested_users(self):
        #Si estan como is_superuser = True, todo los permisos son True
        users = [
            ('111160','12345', 'ADM Master'),
            ('111111','123456', 'ADM Master'),
            ('111111','123456', 'Operador de Registro paquetes'),
            ('111120', '12345', 'Operador de Registro paquetes'), #Ezequiel Central
            ('111144', '12345', 'Operador de Registro paquetes'), #Central 
            ('111182', '12345', 'Depositero (Recepcion local)'),  #Central 
            ('111172', '12345', 'Depositero (Recepcion local)'),  #Fdo
            ('111172', '12345', 'Operador de Registro paquetes'),  #Carmelitas
            ('111181', '12345', 'Depositero (Recepcion local)'),  #Carmelitas
            ('111181', '12345', 'Operador de Registro paquetes'),  #Carmelitas
            ('111146', '12345', 'Depositero (Recepcion local)'),  #Espana
            ('111138','4509134', 'ATC Supervisor'),
            ('111188', None, 'ATC Basico'),
            ('111193', '12345', 'ADM'),
            ('111192', '12345', 'Depositero (Recepcion local)'),
            ('111182', None, 'Operaciones/ Gestiones Aduaneras')
        ]
        for username, password, group in users:
            user_fl = Usuarios.objects.using('fl').get(funcionariocodigo=username)
            userobj, created = User.objects.get_or_create(
                        username=username,
                    )
            userobj.first_name = f'{user_fl.funcionarionombre} {user_fl.funcionarioapellido}'[0:150]
            if password:
                userobj.set_password(password)
            userobj.save()
            userobj.groups.add(Group.objects.get(name=group))
        return {'success': 'Done!!!'}
    
    
    def set_user_dashboard(self):
        usuarios = [
            111111,
            111160,
            111120,
            111144,
            111172,
            111181
        ]
        Group.objects.get_or_create(name='Operador de Registro paquetes')
        Group.objects.get_or_create(name='SaDashboard')
        for user_fl in Usuarios.objects.using('fl').filter(funcionariocodigo__in=usuarios):
            userobj, created = User.objects.get_or_create(
                        username=user_fl.funcionariocodigo,
                    )
            if created:
                userobj.first_name = f'{user_fl.funcionarionombre} {user_fl.funcionarioapellido}'[0:150]
                userobj.save()
            userobj.groups.add(Group.objects.get(name='Operador de Registro paquetes'))
            userobj.groups.add(Group.objects.get(name='SaDashboard'))
        return {'success': 'Done!!'}

    def set_global_parameters_business(self):
        tnow = date.today()
        if SysParams.objects.filter(valor='Business'):
            SysParams.objects.filter(
                valor = 'Business'
            ).update(
                tipo =  'json',
                valor_s = '',
                valor_f = 0,
                valor_j =  {
                    'razon_social':'TU EMPRESA',
                    'ruc':'TU RUC-TU DV',
                    'direccion':'Algun lugar',
                    'geolocalidad':'Algun lugar'
                },
                vigencia = tnow,
                save_user = 'AUTOMATICO',
                date_save = datetime.now()
            )
        else:
            SysParams.objects.create(
                valor = 'Business',
                tipo =  'json',
                valor_s = '',
                valor_f = 0,
                valor_j =  {
                    'razon_social':'TU EMPRESA',
                    'ruc':'TU RUC-TU DV',
                    'direccion':'Algun lugar',
                    'geolocalidad':'Algun lugar'
                },
                vigencia = tnow,
                save_user = 'AUTOMATICO',
                date_save = datetime.now()
            )
        return {'success': 'Done!!!'}
    
    def get_modules(self, *args: list, **kwargs: dict) -> dict:
        modules = set()
        for p in Permission.objects.filter(
            content_type=ContentType.objects.get(model='sysparams'),
            name__icontains='->'
            ).order_by('pk'):
            modules.add(p.name.split('->')[0])
        modules = list(modules)
        return {'modules': modules}

    def get_permissions(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict').dict()
        module = q.get('fl_module')
        pps = {
            'content_type':ContentType.objects.get(model='sysparams'),
            'name__icontains':'->',
        }
        if module != '':
            pps['name__icontains'] = module
        pmns = {}
        for p in Permission.objects.filter(**pps).order_by('pk'):
            group = p.name.split('->')[0]
            if not pmns.get(group):
                pmns[group] = []
            idt = 2
            if p.codename.startswith('menu_'):
                idt = 1                
            pmns[group].append({'id': p.pk, 
                            'name': p.name, 
                            'codename': p.codename, 
                            'label': ' '.join(p.codename.split('_')[idt:]).upper(),
                            #'label': p.codename.upper()
                        })
        return pmns
    
    def get_permissions_group(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict').dict()
        gname = q.get('group')
        module = q.get('fl_module')
        pps = {}
        if module != '':
            pps['name__icontains'] = module
        groupobj = Group.objects.get(name=gname)
        pmns = {}
        for p in groupobj.permissions.filter(**pps).order_by('pk'):
            group = p.name.split('->')[0]
            if not pmns.get(group):
                pmns[group] = []
            idt = 2
            if p.codename.startswith('menu_'):
                idt = 1
            pmns[group].append({'id': p.pk, 'name': p.name, 
                                'codename': p.codename, 
                                'label': ' '.join(p.codename.split('_')[idt:]).upper()
                                #'label': p.codename.upper()
                                })
        return pmns
    
    def set_permission(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict')
        id = q.getlist('id')
        group = q.get('group')
        groupobj = Group.objects.get(name=group)
        for permissionobj in Permission.objects.filter(pk__in=id):
            if not groupobj.permissions.filter(codename=permissionobj.codename):
                groupobj.permissions.add(permissionobj)
        return {'success': f'Permisos aderidos con exito'}
    
    def remove_permission(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict')
        id = q.getlist('id')
        group = q.get('group')
        groupobj = Group.objects.get(name=group)
        for permissionobj in Permission.objects.filter(pk__in=id):
            if groupobj.permissions.filter(codename=permissionobj.codename):
                groupobj.permissions.remove(permissionobj)
        return {'success': f'Permisos removidos con exito'}
    
    def set_user(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict')
        id = q.getlist('id')
        group = q.get('group')
        groupobj = Group.objects.get(name=group)
        for user_fl in Usuarios.objects.using('fl').filter(funcionariocodigo__in=id):
            userobj, created = User.objects.get_or_create(
                        username=user_fl.funcionariocodigo,
                    )
            if created:
                userobj.first_name = f'{user_fl.funcionarionombre} {user_fl.funcionarioapellido}'[0:150]
                userobj.save()
            userobj.groups.add(groupobj)
        return {'success': f'Usuarios aderidos con exito'}
    
    def remove_user(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict')
        id = q.getlist('id')
        group = q.get('group')
        groupobj = Group.objects.get(name=group)
        for userobj in User.objects.filter(username__in=id):
            userobj.groups.remove(groupobj)
        return {'success': f'Usuarios removidos con exito'}
    
    def get_group_user(self, *args: list, **kwargs: dict) -> list:
        q = kwargs.get('qdict')
        gname = q.get('group')
        groupobj = Group.objects.get(name=gname)
        pmns = []
        for p in groupobj.user_set.all():
            pmns.append({
                'first_name': p.first_name,
                'username': p.username,
            })
        return pmns
    
    def set_sucursal_estante(self, *args: list, **kwargs: dict) -> list:
        for c in Clientes.objects.using('fl').filter(estante__isnull=False):
            estante = c.estante.split('-')[-1].strip()
            nestante = f'{c.sucursal.abv}-{estante}'
            c.estante = nestante
            if not c.clientefecharegistro:
                c.clientefecharegistro = datetime.now()
            c.save()
        return {'exitos': 'Hecho'}
    
    def check_password(self, *args: list, **kwargs: dict) -> dict:
        q = kwargs.get('qdict')
        userobj = kwargs.get('userobj')
        if userobj.check_password(q.get('login')):
            return {'success': 'Hecho'}
        return {'error': 'Usuario incorrecto'}
    
    def get_grupos_permisos(self, *args, **kwargs) -> list:
        q: dict = kwargs.get('qdict')
        unames = []
        username = q.get('username')
        if username:
            try:
                userp = User.objects.get(username=username)
                unames = userp.groups.all().values_list('name', flat=True)
            except: pass
        cc = []
        for c in Group.objects.all().order_by('name'):
            selected = False
            if c.name in unames:
                selected = True
            cc.append({
                'pk': c.pk,
                'name': c.name,
                'selected': selected
            })
        return cc
    
    def view_grupos_permisos(self, *args, **kwargs) -> dict:
        grouppk = kwargs.get('grouppk')
        group = Group.objects.get(pk=grouppk)
        cc = []
        for c in group.permissions.all().order_by('name'):
            cc.append({
                'elemento':c.name.split("->")[0], 
                'name': ' '.join(c.codename.split('_')[2:])
            })
        gg = {
            'grupo': group.name,
            'permisos': cc
        }
        return gg
    
    def sync_remove_users_not_fl(self):
        not_match = []
        for a in User.objects.all():
            try:
                user_fl = Usuarios.objects.using('fl').get(funcionariocodigo=a.username)
            except:
                try:
                    int(a.username)
                except:
                    continue
                else:
                    not_match.append(a.username)
            else:
                ff = f'{user_fl.funcionarionombre} {user_fl.funcionarioapellido}'[0:150]
                a.first_name = ff
                a.save()
                UserProfile.objects.filter(userobj=a.username).update(
                    username=ff
                )
        for u in User.objects.filter(username__in=not_match):
            u.asignacionpos_set.all().delete()
            u.delete()
        return not_match

