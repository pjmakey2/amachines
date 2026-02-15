from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.http import QueryDict
from django.contrib.auth.models import User
from django.db.models import Q
from Sifen import mng_sifen_masters, ekuatia_gf, ekuatia_serials, mng_sifen_ruc_mapper, mng_sifen
from Sifen.models import DocumentHeader, Clientes
from OptsIO.models import Apps
from tqdm import tqdm


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--date', nargs='?', help='Date in YYYY-MM-DD format')
        parser.add_argument('--track_lotes', action='store_true', help='Track pending lotes from Sifen')
        parser.add_argument('--send_pending_docs', action='store_true', help='Send pending documents to Sifen')
        parser.add_argument('--send_email', action='store_true', help='Send invoice emails to clients')
        parser.add_argument('--load_actividades', action='store_true', help='')
        parser.add_argument('--load_geografias', action='store_true', help='')
        parser.add_argument('--load_medidas', action='store_true', help='')
        parser.add_argument('--set_tipo_contribuyente', action='store_true', help='')
        parser.add_argument('--sync_rucs', action='store_true', help='Download and sync RUC data from DNIT')
        parser.add_argument('--create_core_apps', action='store_true', help='Create core apps entries')
        parser.add_argument('--classify_clients', action='store_true', help='Classify clients as B2B or B2C based on RUC')

        parser.add_argument('--ruc', nargs='?')
        parser.add_argument('--dv', nargs='?')
        parser.add_argument('--create_timbrado',action='store_true', default=False,help='Crear timbrado')
        parser.add_argument('--timbrado', nargs='?')
        parser.add_argument('--establecimiento', nargs='+')
        parser.add_argument('--inicio', nargs='?')
        parser.add_argument('--fcsc', nargs='?', type=str)
        parser.add_argument('--scsc', nargs='?', type=str)
        parser.add_argument('--tipo', nargs='+', type=str)
        parser.add_argument('--expd', nargs='+', type=int)
        parser.add_argument('--serie', nargs='+', type=str)
        parser.add_argument('--nstart', nargs='+', type=int)
        parser.add_argument('--nend', nargs='+', type=int)
        parser.add_argument('--set_number',nargs='+', help='Pasar el numero de un pedido para firmarlo')
        parser.add_argument('--generate_numbers_timbrado',action='store_true', help='Generar numeros a tipos de documentos')

    def handle(self, *args, **options):
        if options['load_actividades']:
            mng_sifen_masters.load_actividades()
        if options['load_geografias']:
            mng_sifen_masters.load_geografias()

        if options['load_medidas']:
            mng_sifen_masters.load_medidas()

        if options['set_tipo_contribuyente']:
            mng_sifen_masters.set_tipo_contribuyente()

        if options['sync_rucs']:
            self.stdout.write(self.style.SUCCESS('Starting RUC sync process...'))
            rmap = mng_sifen_ruc_mapper.RMap()
            result = rmap.sync_rucs()
            self.stdout.write(self.style.SUCCESS(f"RUC sync tasks dispatched:"))
            self.stdout.write(f"  - Tasks sent: {result['tasks_sent']}")
            self.stdout.write(f"  - Total records: {result['total_records']}")
            self.stdout.write(f"  - Task IDs: {', '.join(result['task_ids'][:5])}{'...' if len(result['task_ids']) > 5 else ''}")
            self.stdout.write(self.style.WARNING('Tasks are running asynchronously. Check Celery logs for progress.'))

        if options['track_lotes']:
            fdate = options.get('date')
            if not fdate:
                self.stdout.write(self.style.ERROR('--date is required for track_lotes (YYYY-MM-DD)'))
                return
            self.stdout.write(self.style.SUCCESS(f'Tracking lotes from {fdate}...'))
            eser = ekuatia_serials.Eserial()
            result = eser.track_lotes(fdate=fdate)
            self.stdout.write(self.style.SUCCESS(f"Track lotes completed: {result}"))

        if options['send_pending_docs']:
            self.stdout.write(self.style.SUCCESS('Sending pending documents to Sifen...'))
            dobjs = DocumentHeader.objects.filter(
                ~Q(pdv_ruc='0'),
                ek_estado__isnull=True,
            ).exclude(
                lote_estado__in=['Aprobado',
                    'RECIBIDO',
                    'PROCESANDO',
                    'CONCLUIDO'
                ]
            )
            count = dobjs.count()
            if count == 0:
                self.stdout.write(self.style.WARNING('No pending documents found'))
                return
            self.stdout.write(f'  - Found {count} pending documents')
            dobjs.update(ek_xml_ekua=False)
            eser = ekuatia_serials.Eserial()
            qek = QueryDict(mutable=True)
            profs = []
            for docobj in dobjs:
                qek.update({
                    'prof_number': str(docobj.prof_number),
                    'ruc': docobj.ek_bs_ruc,
                })
                profs.append(str(docobj.prof_number))
            eser.set_data_ekuatia(qdict=qek)
            eser.send_pending_signedxml(profs)
            self.stdout.write(self.style.SUCCESS(f'Sent {count} documents to Sifen'))

        if options['send_email']:
            fdate = options.get('date')
            if not fdate:
                self.stdout.write(self.style.ERROR('--date is required for send_email (YYYY-MM-DD)'))
                return
            self.stdout.write(self.style.SUCCESS(f'Sending invoice emails for documents from {fdate}...'))
            dobjs = DocumentHeader.objects.filter(
                doc_fecha__gte=fdate,
                enviado_cliente=False,
                ek_estado='Aprobado'
            )
            count = dobjs.count()
            if count == 0:
                self.stdout.write(self.style.WARNING('No pending emails to send'))
                return
            self.stdout.write(f'  - Found {count} documents to email')
            msifen = mng_sifen.MSifen()
            for docobj in tqdm(dobjs, desc='Sending emails'):
                try:
                    qdict = QueryDict(mutable=True)
                    qdict.update({
                        'docpk': str(docobj.pk),
                        'dbcon': 'default',
                        'from_console': 'true'
                    })
                    result = msifen.send_invoice(qdict=qdict)
                    if 'error' in result[0] if isinstance(result, tuple) else 'error' in result:
                        self.stdout.write(self.style.WARNING(f'  - Doc {docobj.doc_numero}: {result}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'  - Doc {docobj.doc_numero}: Email sent'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  - Doc {docobj.doc_numero}: Error - {str(e)}'))
            self.stdout.write(self.style.SUCCESS(f'Email sending completed'))

        if options['create_timbrado']:
            eser = ekuatia_serials.Eserial()
            qdict = QueryDict(mutable=True)
            qdict.update(
                {
                    'ruc': options['ruc'],
                    'dv': options['dv'],
                    'timbrado': options['timbrado'],
                    'inicio': options['inicio'],
                    'fcsc': options['fcsc'],
                    'scsc': options['scsc'],
                }
            )
            qdict.setlist('establecimiento', options['establecimiento'])
            qdict.setlist('tipo', options['tipo'])
            qdict.setlist('expd', options['expd'])
            qdict.setlist('serie', options['serie'])
            qdict.setlist('nstart', options['nstart'])
            qdict.setlist('nend', options['nend'])
            eser.create_timbrado(
                User.objects.get(username='amadmin'),
                qdict=qdict
            )

        if options['generate_numbers_timbrado']:
            eser = ekuatia_serials.Eserial()
            eser.generate_numbers_timbrado(
                options['timbrado'],
                options['tipo'][0],
                options['establecimiento'][0],
                options['expd'][0],
                options['serie'][0],
                options['nstart'][0],
                options['nend'][0]
            )

        if options['create_core_apps']:
            self.create_core_apps()

        if options['classify_clients']:
            self.classify_clients()

    def create_core_apps(self):
        """Create core apps entries if they don't exist"""
        apps_core = [
            {
                'prioridad': 1,
                'menu': 'Sifen',
                'menu_icon': 'mdi mdi mdi-cash',
                'app_name': 'sifen_facturar',
                'friendly_name': 'Facturar',
                'icon': 'bi bi-file-earmark-text',
                'url': 'Sifen/DocumentHeaderUi.html',
                'version': '1.0',
                'background': '#4f46e5',
                'active': True
            },
            {
                'prioridad': 2,
                'menu': 'Sifen',
                'menu_icon': 'mdi mdi mdi-cash',
                'app_name': 'sifen_documentnc',
                'friendly_name': 'Notas de Crédito',
                'icon': 'mdi mdi-file-document-minus',
                'url': 'Sifen/DocumentNcUi.html',
                'version': '1.0',
                'background': '#FF6B6B',
                'active': True
            },
            {
                'prioridad': 3,
                'menu': 'Sifen',
                'menu_icon': 'mdi mdi mdi-cash',
                'app_name': 'sifen_recibo',
                'friendly_name': 'Recibo',
                'icon': 'bi bi-file-earmark-check',
                'url': 'Sifen/DocumentReciboHomeUi.html',
                'version': '1.0',
                'background': '#9d95b2',
                'active': True
            },
            {
                'prioridad': 4,
                'menu': 'Sifen',
                'menu_icon': 'mdi mdi mdi-cash',
                'app_name': 'sifen_retenciones',
                'friendly_name': 'Retenciones',
                'icon': 'bi bi-file-earmark-minus',
                'url': 'Sifen/RetencionHomeUi.html',
                'version': '1.0',
                'background': '#9b62fe',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Maestros',
                'menu_icon': 'mdi mdi-source-commit-start',
                'app_name': 'Producto',
                'friendly_name': 'Productos',
                'icon': 'mdi mdi-package-variant',
                'url': 'Sifen/ProductoUi.html',
                'version': '1',
                'background': '#FFFFFF',
                'active': True
            },
            {
                'prioridad': 2,
                'menu': 'Maestros',
                'menu_icon': 'mdi mdi-source-commit-start',
                'app_name': 'Marca',
                'friendly_name': 'Marcas',
                'icon': 'mdi mdi-tag',
                'url': 'Sifen/MarcaUi.html',
                'version': '1',
                'background': '#FFFFFF',
                'active': True
            },
            {
                'prioridad': 3,
                'menu': 'Maestros',
                'menu_icon': 'mdi mdi-source-commit-start',
                'app_name': 'Categoria',
                'friendly_name': 'Categorías',
                'icon': 'mdi mdi-shape',
                'url': 'Sifen/CategoriaUi.html',
                'version': '1',
                'background': '#FFFFFF',
                'active': True
            },
            {
                'prioridad': 4,
                'menu': 'Maestros',
                'menu_icon': 'mdi mdi-source-commit-start',
                'app_name': 'PorcentajeIva',
                'friendly_name': 'Porcentajes IVA',
                'icon': 'mdi mdi-percent',
                'url': 'Sifen/PorcentajeIvaUi.html',
                'version': '1',
                'background': '#FFFFFF',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Negocios',
                'menu_icon': 'mdi mdi mdi-domain',
                'app_name': 'Business',
                'friendly_name': 'Empresas',
                'icon': 'mdi mdi-domain',
                'url': 'Sifen/BusinessUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 2,
                'menu': 'Negocios',
                'menu_icon': 'mdi mdi-domain',
                'app_name': 'BusinessConfig',
                'friendly_name': 'Configuración Negocio',
                'icon': 'mdi mdi-office-building',
                'url': 'OptsIO/BusinessUi.html',
                'version': '1',
                'background': '#ffffff',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Timbrado',
                'menu_icon': 'mdi mdi mdi-file-cog',
                'app_name': 'Etimbrado',
                'friendly_name': 'Timbrado',
                'icon': 'mdi mdi-stamp',
                'url': 'Sifen/EtimbradoUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 2,
                'menu': 'Timbrado',
                'menu_icon': 'mdi mdi mdi-file-cog',
                'app_name': 'EnumberCreate',
                'friendly_name': 'Crear Timbrado',
                'icon': 'mdi mdi-numeric',
                'url': 'Sifen/EnumberCreateUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 3,
                'menu': 'Timbrado',
                'menu_icon': 'mdi mdi mdi-file-cog',
                'app_name': 'Eestablecimiento',
                'friendly_name': 'Establecimientos',
                'icon': 'mdi mdi-store',
                'url': 'Sifen/EestablecimientoUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 4,
                'menu': 'Timbrado',
                'menu_icon': 'mdi mdi mdi-file-cog',
                'app_name': 'Enumbers',
                'friendly_name': 'Numeración',
                'icon': 'mdi mdi-numeric',
                'url': 'Sifen/EnumbersUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 5,
                'menu': 'Timbrado',
                'menu_icon': 'mdi mdi mdi-file-cog',
                'app_name': 'EnumberExtend',
                'friendly_name': 'Gestión Números',
                'icon': 'mdi mdi-numeric-positive-1',
                'url': 'Sifen/EnumberExtendUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Trazabilidad',
                'menu_icon': 'mdi mdi-radar',
                'app_name': 'Track Lotes',
                'friendly_name': 'Track Lotes',
                'icon': 'mdi mdi-package-variant-closed',
                'url': 'Sifen/SoapMsgUi.html',
                'version': '1',
                'background': '#FFFFFF',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Geografias',
                'friendly_name': 'Geografías',
                'icon': 'mdi mdi-earth',
                'url': 'Sifen/GeografiasUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 2,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'AreasPoliticas',
                'friendly_name': 'Áreas Políticas',
                'icon': 'mdi mdi-map-marker-radius',
                'url': 'Sifen/AreasPoliticasUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 3,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Paises',
                'friendly_name': 'Países',
                'icon': 'mdi mdi-flag',
                'url': 'Sifen/PaisesUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 4,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Departamentos',
                'friendly_name': 'Departamentos',
                'icon': 'mdi mdi-map',
                'url': 'Sifen/DepartamentosUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 5,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Distrito',
                'friendly_name': 'Distritos',
                'icon': 'mdi mdi-map-outline',
                'url': 'Sifen/DistritoUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 6,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Ciudades',
                'friendly_name': 'Ciudades',
                'icon': 'mdi mdi-city',
                'url': 'Sifen/CiudadesUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 7,
                'menu': 'Geografías',
                'menu_icon': 'mdi mdi-earth',
                'app_name': 'Barrios',
                'friendly_name': 'Barrios',
                'icon': 'mdi mdi-home-group',
                'url': 'Sifen/BarriosUi.html',
                'version': '1',
                'background': '#000000',
                'active': True
            },
            {
                'prioridad': 1,
                'menu': 'Configuración',
                'menu_icon': 'mdi mdi-cog-outline',
                'app_name': 'UserProfile',
                'friendly_name': 'Mi Perfil',
                'icon': 'mdi mdi-account-circle',
                'url': 'OptsIO/UserProfileUi.html',
                'version': '1',
                'background': '#ffffff',
                'active': True
            },
        ]

        created_count = 0
        existing_count = 0

        for app_data in apps_core:
            url = app_data['url']
            if Apps.objects.filter(url=url).exists():
                self.stdout.write(f"  ⏭ App '{url}' already exists, skipping")
                existing_count += 1
            else:
                Apps.objects.create(**app_data)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Created app '{app_data['friendly_name']}' ({url})"))
                created_count += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f"Core apps setup complete:"))
        self.stdout.write(f"  - Created: {created_count}")
        self.stdout.write(f"  - Already existed: {existing_count}")
        self.stdout.write(f"  - Total: {len(apps_core)}")

    def classify_clients(self):
        """
        Classify clients as B2B or B2C based on RUC pattern.

        - RUCs with 7 digits or less (e.g., 2463986) → Persona física → B2C, tipocontribuyente=1
        - RUCs with 8+ digits starting with 80 (e.g., 80012345-6) → Empresa → B2B, tipocontribuyente=2

        Uses bulk_update for efficiency (~1000x faster than individual saves)
        """
        self.stdout.write(self.style.SUCCESS('Starting client classification...'))

        total = Clientes.objects.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('No clients found'))
            return

        self.stdout.write(f'  - Found {total} clients to process')

        b2c_count = 0
        b2b_count = 0
        skipped_count = 0

        BATCH_SIZE = 5000
        clients_to_update = []

        # Use iterator() to avoid loading all records into memory
        for client in tqdm(Clientes.objects.only('pk', 'pdv_ruc', 'pdv_type_business', 'pdv_tipocontribuyente').iterator(),
                          desc='Classifying clients', total=total):
            ruc = client.pdv_ruc

            if not ruc:
                skipped_count += 1
                continue

            # Clean RUC - remove any non-numeric characters for length check
            ruc_clean = ''.join(filter(str.isdigit, str(ruc)))

            if not ruc_clean:
                skipped_count += 1
                continue

            # Classification logic:
            # - RUCs with 8+ digits starting with 80 are companies (B2B, Juridica)
            # - All others are individuals (B2C, Fisica)
            if len(ruc_clean) >= 8 and ruc_clean.startswith('80'):
                new_type = 'B2B'
                new_tipocontribuyente = '2'  # Juridica
                b2b_count += 1
            else:
                new_type = 'B2C'
                new_tipocontribuyente = '1'  # Fisica
                b2c_count += 1

            # Only update if different
            needs_update = False
            if client.pdv_type_business != new_type:
                client.pdv_type_business = new_type
                needs_update = True
            if client.pdv_tipocontribuyente != new_tipocontribuyente:
                client.pdv_tipocontribuyente = new_tipocontribuyente
                needs_update = True

            if needs_update:
                clients_to_update.append(client)

            # Bulk update in batches
            if len(clients_to_update) >= BATCH_SIZE:
                Clientes.objects.bulk_update(clients_to_update, ['pdv_type_business', 'pdv_tipocontribuyente'])
                clients_to_update = []

        # Update remaining records
        if clients_to_update:
            Clientes.objects.bulk_update(clients_to_update, ['pdv_type_business', 'pdv_tipocontribuyente'])

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Client classification complete:'))
        self.stdout.write(f'  - B2C (Persona física, tipocontribuyente=1): {b2c_count}')
        self.stdout.write(f'  - B2B (Empresa, tipocontribuyente=2): {b2b_count}')
        self.stdout.write(f'  - Skipped (no RUC): {skipped_count}')
        self.stdout.write(f'  - Total processed: {total}')

