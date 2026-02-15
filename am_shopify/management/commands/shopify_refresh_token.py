from django.core.management.base import BaseCommand
from am_shopify.services import ShopifyTokenService


class Command(BaseCommand):
    help = 'Renueva el access token de Shopify'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Renovando token de Shopify...'))
        
        service = ShopifyTokenService()
        token = service.get_valid_token()
        
        self.stdout.write(self.style.SUCCESS(
            f'✓ Token renovado exitosamente\n'
            f'  Access Token: {token[:10]}...{token[-4:]}'
        ))
