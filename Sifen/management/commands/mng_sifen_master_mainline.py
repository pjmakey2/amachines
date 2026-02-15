from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.http import QueryDict
from django.contrib.auth.models import User
from Sifen import mng_sifen_masters, ekuatia_gf, ekuatia_serials
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--create_business', action='store_true', help='')
        parser.add_argument('--set_tipo_contribuyente', action='store_true', help='')
        parser.add_argument('--load_actividades', action='store_true', help='')
        parser.add_argument('--load_geografias', action='store_true', help='')

    def handle(self, *args, **options):
        if options['create_business']:
            mng_sifen_masters.create_business()
        if options['set_tipo_contribuyente']:
            mng_sifen_masters.set_tipo_contribuyente()
        if options['load_actividades']:
            mng_sifen_masters.load_actividades()
        if options['load_geografias']:
            mng_sifen_masters.load_geografias()


