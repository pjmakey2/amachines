"""
Comando mainline para el plugin FL Facturación Legacy.
Registra el plugin en la base de datos y sincroniza sus menús.
"""
from django.core.management.base import BaseCommand
from OptsIO.models import Plugin as PluginModel, Menu, Apps
from OptsIO.plugin_manager import plugin_manager


class Command(BaseCommand):
    help = 'Registra el plugin FL Facturación Legacy y sincroniza sus menús'

    def add_arguments(self, parser):
        parser.add_argument(
            '--register_plugin',
            action='store_true',
            help='Registra el plugin en la BD y sincroniza sus menús',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se haría sin hacer cambios',
        )

    def handle(self, *args, **options):
        register_plugin = options.get('register_plugin', False)
        dry_run = options.get('dry_run', False)

        if not register_plugin:
            self.stdout.write(self.style.ERROR('Debe especificar --register_plugin'))
            self.stdout.write('Uso: python manage.py fl_legacy_mainline --register_plugin')
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN - No se harán cambios ===\n'))

        self.stdout.write(self.style.SUCCESS('=== FL Facturación Legacy - Mainline ===\n'))

        # 1. Descubrir y registrar el plugin
        self.stdout.write('1. Descubriendo plugin...')
        discovered = plugin_manager.discover_plugins()
        fl_plugin = next((p for p in discovered if p.name == 'fl_facturacion_legacy'), None)

        if not fl_plugin:
            self.stdout.write(self.style.ERROR('Error: Plugin fl_facturacion_legacy no encontrado'))
            return

        self.stdout.write(f'   Plugin encontrado: {fl_plugin.display_name} v{fl_plugin.version}')

        # 2. Registrar en la base de datos
        if not dry_run:
            self.stdout.write('\n2. Registrando plugin en BD...')
            plugin_obj, created = PluginModel.objects.update_or_create(
                name=fl_plugin.name,
                defaults={
                    'display_name': fl_plugin.display_name,
                    'description': fl_plugin.description,
                    'version': fl_plugin.version,
                    'author': fl_plugin.author,
                    'app_name': fl_plugin.app_name,
                    'module_path': fl_plugin.module_path,
                    'is_core': fl_plugin.is_core,
                    'dependencies': fl_plugin.dependencies,
                    'icon': fl_plugin.icon,
                    'category': fl_plugin.category,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS('   Plugin CREADO en BD'))
            else:
                self.stdout.write(self.style.SUCCESS('   Plugin ACTUALIZADO en BD'))
        else:
            self.stdout.write('\n2. [DRY] Registrar plugin en BD')

        # 3. Sincronizar menús
        self.stdout.write('\n3. Sincronizando menús...')
        menus_created = 0
        apps_created = 0

        for menu_def in fl_plugin.menus:
            menu_name = menu_def.get('menu')
            if not menu_name:
                continue

            # Crear menú
            if not dry_run:
                menu_obj, created = Menu.objects.get_or_create(
                    menu=menu_name,
                    defaults={
                        'prioridad': menu_def.get('prioridad', 50),
                        'friendly_name': menu_name,
                        'icon': menu_def.get('menu_icon', 'mdi mdi-folder'),
                        'url': '#',
                        'background': menu_def.get('background', '#8B5CF6'),
                        'active': True,
                    }
                )
                if created:
                    menus_created += 1
                    self.stdout.write(self.style.SUCCESS(f'   Menú CREADO: {menu_name}'))
                else:
                    self.stdout.write(f'   Menú existe: {menu_name}')
            else:
                exists = Menu.objects.filter(menu=menu_name).exists()
                status = 'existe' if exists else 'CREAR'
                self.stdout.write(f'   [DRY] Menú ({status}): {menu_name}')

            # Crear apps del menú
            items = menu_def.get('items', [])
            for item in items:
                app_name = item.get('app_name')
                if not app_name:
                    continue

                if not dry_run:
                    app_obj, created = Apps.objects.get_or_create(
                        app_name=app_name,
                        defaults={
                            'prioridad': item.get('prioridad', 1),
                            'menu': menu_name,
                            'menu_icon': menu_def.get('menu_icon', 'mdi mdi-folder'),
                            'friendly_name': item.get('friendly_name', app_name),
                            'icon': item.get('icon', 'mdi mdi-application'),
                            'url': item.get('url', ''),
                            'version': '1.0',
                            'background': item.get('background', '#8B5CF6'),
                            'active': True,
                        }
                    )
                    if created:
                        apps_created += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'     App CREADA: {item.get("friendly_name")}'
                        ))
                    else:
                        self.stdout.write(f'     App existe: {item.get("friendly_name")}')
                else:
                    exists = Apps.objects.filter(app_name=app_name).exists()
                    status = 'existe' if exists else 'CREAR'
                    self.stdout.write(f'     [DRY] App ({status}): {item.get("friendly_name")}')

        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN:'))
        if not dry_run:
            self.stdout.write(f'  Menús creados: {menus_created}')
            self.stdout.write(f'  Apps creadas: {apps_created}')
        self.stdout.write(self.style.SUCCESS('\nPlugin FL Facturación Legacy configurado exitosamente!'))
