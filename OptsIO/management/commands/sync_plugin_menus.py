"""
Comando para sincronizar los menús de plugins NO-CORE con la base de datos.

IMPORTANTE: Este comando SOLO procesa plugins con is_core=False
Los plugins core (optsio, sifen) tienen sus menús en setup_sifen_menu.py

Este comando:
1. Descubre plugins NO-CORE (is_core=False)
2. Lee los menús definidos en get_menus()
3. AGREGA los menús y apps a la BD (sin tocar los existentes)

Uso:
    python manage.py sync_plugin_menus
    python manage.py sync_plugin_menus --remove-plugin=nombre  # Elimina menús de un plugin
"""

from django.core.management.base import BaseCommand
from OptsIO.models import Menu, Apps
from OptsIO.plugin_manager import plugin_manager


class Command(BaseCommand):
    help = 'Sincroniza menús de plugins NO-CORE con la base de datos (solo agrega, no elimina)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se haría sin hacer cambios',
        )
        parser.add_argument(
            '--remove-plugin',
            type=str,
            help='Elimina los menús y apps de un plugin específico',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        remove_plugin = options.get('remove_plugin')

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN - No se harán cambios ===\n'))

        # Modo eliminación de plugin
        if remove_plugin:
            self._remove_plugin_menus(remove_plugin, dry_run)
            return

        # 1. Descubrir plugins
        self.stdout.write('Descubriendo plugins...')
        discovered = plugin_manager.discover_plugins()
        self.stdout.write(f'  {len(discovered)} plugins encontrados')

        # 2. Filtrar solo plugins NO-CORE
        non_core_plugins = [p for p in discovered if not p.is_core]
        self.stdout.write(self.style.SUCCESS(
            f'  {len(non_core_plugins)} plugins NO-CORE para procesar'
        ))

        if not non_core_plugins:
            self.stdout.write('No hay plugins no-core con menús para agregar.')
            return

        # 3. Procesar cada plugin no-core
        menus_created = 0
        apps_created = 0

        for plugin_info in non_core_plugins:
            plugin_name = plugin_info.name
            menus = plugin_info.menus

            if not menus:
                continue

            self.stdout.write(f'\nPlugin: {plugin_info.display_name} (is_core={plugin_info.is_core})')

            for menu_def in menus:
                menu_name = menu_def.get('menu')
                if not menu_name:
                    continue

                # Crear menú si no existe
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
                        self.stdout.write(self.style.SUCCESS(f'  Menú CREADO: {menu_name}'))
                    else:
                        self.stdout.write(f'  Menú existe: {menu_name}')
                else:
                    exists = Menu.objects.filter(menu=menu_name).exists()
                    status = 'existe' if exists else 'CREAR'
                    self.stdout.write(f'  [DRY] Menú ({status}): {menu_name}')

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
                                f'    App CREADA: {item.get("friendly_name")}'
                            ))
                        else:
                            self.stdout.write(f'    App existe: {item.get("friendly_name")}')
                    else:
                        exists = Apps.objects.filter(app_name=app_name).exists()
                        status = 'existe' if exists else 'CREAR'
                        self.stdout.write(f'    [DRY] App ({status}): {item.get("friendly_name")}')

        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RESUMEN:'))
        self.stdout.write(f'  Plugins no-core procesados: {len(non_core_plugins)}')
        if not dry_run:
            self.stdout.write(f'  Menús creados: {menus_created}')
            self.stdout.write(f'  Apps creadas: {apps_created}')
        self.stdout.write(self.style.SUCCESS('\nSincronización completada!'))

    def _remove_plugin_menus(self, plugin_name: str, dry_run: bool):
        """Elimina los menús y apps de un plugin específico."""
        self.stdout.write(f'Buscando plugin: {plugin_name}')

        # Descubrir el plugin
        discovered = plugin_manager.discover_plugins()
        plugin_info = next((p for p in discovered if p.name == plugin_name), None)

        if not plugin_info:
            self.stdout.write(self.style.ERROR(f'Plugin "{plugin_name}" no encontrado'))
            return

        if plugin_info.is_core:
            self.stdout.write(self.style.ERROR(
                f'Plugin "{plugin_name}" es CORE. No se pueden eliminar sus menús.'
            ))
            return

        menus = plugin_info.menus
        if not menus:
            self.stdout.write(f'Plugin "{plugin_name}" no tiene menús definidos.')
            return

        self.stdout.write(f'Eliminando menús del plugin: {plugin_info.display_name}')

        for menu_def in menus:
            menu_name = menu_def.get('menu')
            items = menu_def.get('items', [])

            # Eliminar apps
            for item in items:
                app_name = item.get('app_name')
                if app_name:
                    if not dry_run:
                        deleted, _ = Apps.objects.filter(app_name=app_name).delete()
                        if deleted:
                            self.stdout.write(self.style.WARNING(
                                f'  App eliminada: {item.get("friendly_name")}'
                            ))
                    else:
                        self.stdout.write(f'  [DRY] Eliminar app: {item.get("friendly_name")}')

            # Eliminar menú (solo si no tiene otras apps)
            if menu_name:
                remaining_apps = Apps.objects.filter(menu=menu_name).count()
                if remaining_apps == 0:
                    if not dry_run:
                        deleted, _ = Menu.objects.filter(menu=menu_name).delete()
                        if deleted:
                            self.stdout.write(self.style.WARNING(f'  Menú eliminado: {menu_name}'))
                    else:
                        self.stdout.write(f'  [DRY] Eliminar menú: {menu_name}')
                else:
                    self.stdout.write(f'  Menú "{menu_name}" tiene otras apps, no se elimina')

        self.stdout.write(self.style.SUCCESS('\nEliminación completada!'))
