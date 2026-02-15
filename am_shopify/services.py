import requests
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import ShopifyAccessToken, ShopifySyncLog

logger = logging.getLogger(__name__)


class ShopifyTokenService:
    """
    Servicio para gestionar tokens de acceso de Shopify
    """

    def get_or_create_token(self, store_name=None, client_id=None, client_secret=None):
        """
        Obtiene el token actual o crea uno nuevo si no existe
        """
        if not store_name:
            store_name = settings.SHOPIFY_STORE.replace('.myshopify.com', '').replace('https://', '').replace('http://', '').replace('/', '')
        if not client_id:
            client_id = getattr(settings, 'SHOPIFY_CLIENTEID', '')
        if not client_secret:
            client_secret = getattr(settings, 'SHOPIFY_SECRET', '')

        try:
            token_obj = ShopifyAccessToken.objects.get(store_name=store_name, is_active=True)

            # Si el token está por expirar, renovarlo
            if token_obj.is_expiring_soon():
                logger.info(f"Token para {store_name} está por expirar, renovando...")
                return self.refresh_token(token_obj)

            # Si el token expiró, renovarlo
            if not token_obj.is_valid():
                logger.warning(f"Token para {store_name} ha expirado, renovando...")
                return self.refresh_token(token_obj)

            logger.info(f"Token válido encontrado para {store_name}")
            return token_obj.access_token

        except ShopifyAccessToken.DoesNotExist:
            # Si hay Admin API token en settings, usarlo directamente
            admin_token = getattr(settings, 'SHOPIFY_API_ADMIN', None)
            if admin_token:
                logger.info(f"Usando SHOPIFY_API_ADMIN token para {store_name}")
                # Crear registro en BD con el admin token
                from datetime import timedelta
                token_obj = ShopifyAccessToken.objects.create(
                    store_name=store_name,
                    client_id=client_id or '',
                    client_secret=client_secret or '',
                    access_token=admin_token,
                    scopes='read_products,write_products,read_orders,write_orders,read_inventory,write_inventory',
                    expires_at=timezone.now() + timedelta(days=365),
                    is_active=True
                )
                return admin_token

            logger.info(f"No se encontró token para {store_name}, creando uno nuevo...")
            return self.create_token(store_name, client_id, client_secret)

    def create_token(self, store_name, client_id, client_secret):
        """
        Crea un nuevo token de acceso
        """
        sync_log = ShopifySyncLog.objects.create(
            sync_type='token_refresh',
            status='success'
        )

        try:
            # Solicitar token usando Client Credentials Grant
            token_url = f"https://{store_name}.myshopify.com/admin/oauth/access_token"
            
            data = {
                'client_id': client_id,
                'client_secret': client_secret.strip(),
                'grant_type': 'client_credentials'
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(token_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data['access_token']
            scopes = token_data.get('scope', '')
            expires_in = token_data.get('expires_in', 86399)  # Default 24 horas

            # Calcular fecha de expiración
            expires_at = timezone.now() + timedelta(seconds=expires_in)

            # Crear o actualizar el registro
            token_obj, created = ShopifyAccessToken.objects.update_or_create(
                store_name=store_name,
                defaults={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'access_token': access_token,
                    'scopes': scopes,
                    'expires_at': expires_at,
                    'is_active': True
                }
            )

            action = "creado" if created else "actualizado"
            logger.info(f"Token {action} exitosamente para {store_name}")
            
            sync_log.items_processed = 1
            sync_log.items_created = 1 if created else 0
            sync_log.items_updated = 0 if created else 1
            sync_log.complete(status='success')

            return access_token

        except requests.exceptions.RequestException as e:
            error_msg = f"Error al obtener token para {store_name}: {str(e)}"
            logger.error(error_msg)
            sync_log.complete(status='error', error_message=error_msg)
            raise Exception(error_msg)

    def refresh_token(self, token_obj):
        """
        Renueva un token existente
        """
        return self.create_token(
            token_obj.store_name,
            token_obj.client_id,
            token_obj.client_secret
        )

    def get_valid_token(self):
        """
        Obtiene un token válido, renovándolo si es necesario
        """
        return self.get_or_create_token()
