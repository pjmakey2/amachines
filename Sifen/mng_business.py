"""Business Configuration Management"""
from Sifen.models import Business
from OptsIO.models import UserProfile, UserBusiness
from OptsIO.io_serial import IoS
from OptsIO.io_json import from_json
from django.forms import model_to_dict
from datetime import datetime
from django.core.files import File
import logging

log = logging.getLogger(__name__)

class MBusiness:
    """Business Configuration Management Class"""

    def get_business(self, *args, **kwargs) -> dict:
        """
        Get the business configuration (should be only one record)
        """
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        try:
            business = Business.objects.using(dbcon).first()
            if business:
                business_data = model_to_dict(business)
                # Add related object names for display
                business_data['contribuyente_tipo'] = business.contribuyenteobj.tipo if business.contribuyenteobj else ''
                business_data['ciudad_nombre'] = business.ciudadobj.nombre_ciudad if business.ciudadobj else ''
                business_data['actividad_nombre'] = business.actividadecoobj.nombre_actividad if business.actividadecoobj else ''

                return {'business': business_data}
            else:
                return {'info': 'No hay configuración de negocio registrada'}
        except Exception as e:
            log.error(f'Error getting business: {str(e)}')
            return {'error': f'Error al obtener configuración: {str(e)}'}

    def create_or_update_business(self, *args, **kwargs) -> dict:
        """
        Create or update business configuration
        Only one business record should exist in the system
        """
        ios = IoS()
        userobj = kwargs.get('userobj')
        q: dict = kwargs.get('qdict', {})
        files: dict = kwargs.get('files', {})
        dbcon = q.get('dbcon', 'default')
        uc_fields: dict = from_json(q.get('uc_fields', {}))

        # Remove fields that shouldn't be updated directly
        ff = ios.form_model_fields(uc_fields, Business._meta.fields)
        for rr in ff:
            uc_fields.pop(rr, None)

        # Format data for database
        rnorm, rrm, rbol = ios.format_data_for_db(Business, uc_fields)
        for c in rrm:
            uc_fields.pop(c, None)
        for f, fv in rbol:
            uc_fields[f] = fv
        for f, fv in rnorm:
            uc_fields[f] = fv

        pk = uc_fields.pop('id', None)

        if pk:
            # Update existing business
            try:
                mobj = Business.objects.using(dbcon).get(pk=pk)
                msg = 'Configuración de negocio actualizada exitosamente'

                # Get differences
                u_fields = ios.get_differences_fields(model_to_dict(mobj), uc_fields)

                # Handle file upload
                if files:
                    for name, fobj in files.items():
                        if name == 'logo':
                            fname = f'business_logo_{fobj.name}'
                            dfobj = File(fobj, name=fname)
                            setattr(mobj, name, dfobj)
                            mobj.save()

                if not u_fields and not files:
                    return {'info': 'Nada que actualizar'}

                if u_fields:
                    u_fields['actualizado_fecha'] = datetime.now()
                    u_fields['actualizado_usuario'] = userobj.username
                    Business.objects.using(dbcon).filter(pk=mobj.pk).update(**u_fields)

                if u_fields and files:
                    msg = 'Configuración y logo actualizados exitosamente'
                elif files and not u_fields:
                    msg = 'Logo actualizado exitosamente'

                return {
                    'success': msg,
                    'record_id': mobj.id
                }

            except Business.DoesNotExist:
                return {'error': 'Configuración de negocio no encontrada'}

        else:
            # Create new business
            uc_fields['cargado_fecha'] = datetime.now()
            uc_fields['cargado_usuario'] = userobj.username

            mobj = Business.objects.using(dbcon).create(**uc_fields)

            # Handle file upload
            if files:
                for name, fobj in files.items():
                    if name == 'logo':
                        fname = f'business_logo_{fobj.name}'
                        dfobj = File(fobj, name=fname)
                        setattr(mobj, name, dfobj)
                        mobj.save()

            # Create UserBusiness relationship
            profile = UserProfile.objects.using(dbcon).filter(username=userobj.username).first()
            if profile:
                # Deactivate all other businesses for this user
                UserBusiness.objects.using(dbcon).filter(userprofileobj=profile).update(active=False)

                # Create new UserBusiness
                UserBusiness.objects.using(dbcon).create(
                    userprofileobj=profile,
                    businessobj=mobj,
                    active=True
                )
                log.info(f'UserBusiness created for {userobj.username} - Business ID: {mobj.id}')

            return {
                'success': 'Configuración de negocio creada exitosamente',
                'record_id': mobj.id
            }

    def validate_ruc(self, *args, **kwargs) -> dict:
        """
        Validate RUC format and check if it already exists
        """
        q: dict = kwargs.get('qdict', {})
        ruc = q.get('ruc', '')
        current_id = q.get('current_id', None)
        dbcon = q.get('dbcon', 'default')

        if not ruc:
            return {'error': 'RUC requerido'}

        # Check if RUC already exists (excluding current record)
        query = Business.objects.using(dbcon).filter(ruc=ruc)
        if current_id:
            query = query.exclude(pk=current_id)

        if query.exists():
            return {'error': 'Este RUC ya está registrado'}

        return {'success': 'RUC disponible'}

    def get_business_logo_path(self, *args, **kwargs) -> dict:
        """
        Get the path to the business logo for use in reports
        """
        q: dict = kwargs.get('qdict', {})
        dbcon = q.get('dbcon', 'default')

        try:
            business = Business.objects.using(dbcon).first()
            if business and business.logo:
                return {
                    'logo_path': business.logo.path,
                    'logo_url': business.logo.url
                }
            else:
                return {'info': 'No hay logo configurado'}
        except Exception as e:
            log.error(f'Error getting business logo: {str(e)}')
            return {'error': f'Error al obtener logo: {str(e)}'}
