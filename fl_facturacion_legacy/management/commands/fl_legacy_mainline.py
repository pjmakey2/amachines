"""
Comando mainline para el plugin FL Facturación Legacy.
Registra el plugin y gestiona la migración de la base de datos MySQL legacy.
"""
import subprocess
import sys
import os
import tempfile

from django.core.management.base import BaseCommand
from OptsIO.models import Plugin as PluginModel, Menu, Apps
from OptsIO.plugin_manager import plugin_manager


class Command(BaseCommand):
    help = 'FL Facturación Legacy - registro de plugin y migración de BD MySQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--register_plugin',
            action='store_true',
            help='Registra el plugin en la BD y sincroniza sus menús',
        )
        parser.add_argument(
            '--migrate_db',
            action='store_true',
            help='Copia frontlin_db desde servidor remoto al MariaDB local',
        )
        parser.add_argument(
            '--remote_host',
            type=str,
            default='165.227.23.149',
            help='Host del servidor MySQL remoto (default: 165.227.23.149)',
        )
        parser.add_argument(
            '--remote_user',
            type=str,
            default='fesifen',
            help='Usuario MySQL remoto (default: fesifen)',
        )
        parser.add_argument(
            '--remote_pass',
            type=str,
            default='',
            help='Password MySQL remoto',
        )
        parser.add_argument(
            '--remote_db',
            type=str,
            default='frontlin_db',
            help='Nombre de la BD remota (default: frontlin_db)',
        )
        parser.add_argument(
            '--local_db',
            type=str,
            default='frontlin_db',
            help='Nombre de la BD local destino (default: frontlin_db)',
        )
        parser.add_argument(
            '--local_user',
            type=str,
            default='',
            help='Usuario MySQL local (default: FL_MYSQL_USER o frontlin_user)',
        )
        parser.add_argument(
            '--local_pass',
            type=str,
            default='',
            help='Password MySQL local (default: FL_MYSQL_PASSWORD)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se haría sin hacer cambios',
        )

    def handle(self, *args, **options):
        register_plugin = options.get('register_plugin', False)
        migrate_db = options.get('migrate_db', False)
        dry_run = options.get('dry_run', False)

        if not register_plugin and not migrate_db:
            self.stdout.write(self.style.ERROR('Debe especificar una acción:'))
            self.stdout.write('  --register_plugin   Registrar plugin y menús')
            self.stdout.write('  --migrate_db        Copiar BD remota al localhost')
            return

        if migrate_db:
            self._migrate_db(options)
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

    # =========================================================================
    # MIGRACIÓN DE BD MYSQL
    # =========================================================================

    def _migrate_db(self, options):
        """
        Copia frontlin_db desde un servidor MySQL remoto al MariaDB local.

        Usa pymysql para el dump (compatible con MariaDB 5.5 remoto) y el
        cliente mysql local para la importación.

        Uso:
            python manage.py fl_legacy_mainline --migrate_db \
                --remote_pass 'password'
        """
        remote_host = options['remote_host']
        remote_user = options['remote_user']
        remote_pass = options['remote_pass']
        remote_db = options['remote_db']
        local_db = options['local_db']
        local_user = options.get('local_user') or os.environ.get('FL_MYSQL_USER', 'frontlin_user')
        local_pass = options.get('local_pass') or os.environ.get('FL_MYSQL_PASSWORD', '')
        dry_run = options.get('dry_run', False)

        if not remote_pass:
            self.stdout.write(self.style.ERROR(
                'Debe especificar --remote_pass con la contraseña del MySQL remoto'
            ))
            return

        self.stdout.write(self.style.SUCCESS('=== Migración de BD MySQL Legacy ===\n'))
        self.stdout.write(f'  Origen:  {remote_user}@{remote_host}/{remote_db}')
        self.stdout.write(f'  Destino: localhost/{local_db}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No se ejecutarán cambios'))
            return

        try:
            import pymysql
        except ImportError:
            self.stdout.write(self.style.ERROR(
                'pymysql no está instalado. Ejecute: pip install pymysql'
            ))
            return

        # 1. Conectar al servidor remoto
        self.stdout.write('\n1. Conectando al servidor remoto...')
        try:
            remote_conn = pymysql.connect(
                host=remote_host,
                user=remote_user,
                password=remote_pass,
                database=remote_db,
                charset='utf8',
                ssl_disabled=True,
            )
        except pymysql.Error as e:
            self.stdout.write(self.style.ERROR(f'   Error de conexión: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('   Conectado'))

        # 2. Generar dump a archivo temporal
        self.stdout.write('\n2. Generando dump...')
        dump_file = os.path.join(tempfile.gettempdir(), f'{remote_db}_dump.sql')

        try:
            cur = remote_conn.cursor()
            cur.execute("SHOW TABLES")
            tables = [r[0] for r in cur.fetchall()]
            self.stdout.write(f'   {len(tables)} tablas encontradas')

            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write("SET NAMES utf8;\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n")
                f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n\n")

                for table in tables:
                    self.stdout.write(f'   Dumping: {table}...', ending=' ')
                    sys.stdout.flush()

                    # CREATE TABLE
                    cur.execute(f"SHOW CREATE TABLE `{table}`")
                    create_sql = cur.fetchone()[1]
                    f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                    f.write(f"{create_sql};\n\n")

                    # DATA
                    cur.execute(f"SELECT * FROM `{table}`")
                    rows = cur.fetchall()
                    desc = cur.description
                    row_count = len(rows)

                    if rows:
                        batch = []
                        for row in rows:
                            vals = []
                            for i, v in enumerate(row):
                                if v is None:
                                    vals.append("NULL")
                                elif isinstance(v, (int, float)):
                                    vals.append(str(v))
                                elif isinstance(v, bytes):
                                    vals.append("X'" + v.hex() + "'")
                                else:
                                    s = str(v)
                                    s = s.replace("\\", "\\\\")
                                    s = s.replace("'", "\\'")
                                    s = s.replace("\n", "\\n")
                                    s = s.replace("\r", "\\r")
                                    s = s.replace("\x00", "")
                                    vals.append("'" + s + "'")
                            batch.append("(" + ",".join(vals) + ")")

                            if len(batch) >= 1000:
                                f.write(f"INSERT INTO `{table}` VALUES\n")
                                f.write(",\n".join(batch))
                                f.write(";\n")
                                batch = []

                        if batch:
                            f.write(f"INSERT INTO `{table}` VALUES\n")
                            f.write(",\n".join(batch))
                            f.write(";\n")

                    f.write("\n")
                    self.stdout.write(f'{row_count} filas')

                f.write("SET FOREIGN_KEY_CHECKS=1;\n")

            remote_conn.close()

            file_size = os.path.getsize(dump_file)
            self.stdout.write(self.style.SUCCESS(
                f'\n   Dump completado: {dump_file} ({file_size / 1024 / 1024:.1f} MB)'
            ))

        except Exception as e:
            remote_conn.close()
            self.stdout.write(self.style.ERROR(f'\n   Error durante dump: {e}'))
            return

        # 3. Crear BD local y usuario
        self.stdout.write(f'\n3. Preparando BD local "{local_db}"...')
        try:
            # Usar root via sudo para crear BD y usuario
            setup_sql = (
                f"CREATE DATABASE IF NOT EXISTS `{local_db}` "
                f"CHARACTER SET utf8 COLLATE utf8_general_ci; "
                f"CREATE USER IF NOT EXISTS '{local_user}'@'localhost' "
                f"IDENTIFIED BY '{local_pass}'; "
                f"GRANT ALL PRIVILEGES ON `{local_db}`.* TO '{local_user}'@'localhost'; "
                f"FLUSH PRIVILEGES;"
            )
            result = subprocess.run(
                ['sudo', 'mariadb', '-e', setup_sql],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f'   Error: {result.stderr}'))
                return
            self.stdout.write(self.style.SUCCESS(
                f'   BD "{local_db}" y usuario "{local_user}" listos'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error preparando BD local: {e}'))
            return

        # 4. Importar dump
        self.stdout.write(f'\n4. Importando dump en "{local_db}"...')
        try:
            with open(dump_file, 'r') as f:
                result = subprocess.run(
                    ['sudo', 'mariadb', local_db],
                    stdin=f, capture_output=True, text=True
                )
            if result.returncode != 0:
                self.stdout.write(self.style.ERROR(f'   Error: {result.stderr[:500]}'))
                return
            self.stdout.write(self.style.SUCCESS('   Importación completada'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error importando: {e}'))
            return

        # 5. Verificar
        self.stdout.write('\n5. Verificando...')
        try:
            result = subprocess.run(
                ['sudo', 'mariadb', local_db, '-e',
                 'SELECT COUNT(*) as tablas FROM information_schema.tables '
                 f"WHERE table_schema='{local_db}';"],
                capture_output=True, text=True
            )
            self.stdout.write(f'   {result.stdout.strip()}')
        except Exception:
            pass

        # Limpiar
        os.unlink(dump_file)

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Migración completada exitosamente!'))
        self.stdout.write(f'\nVariables de entorno para .env:')
        self.stdout.write(f'  FL_MYSQL_HOST=localhost')
        self.stdout.write(f'  FL_MYSQL_DATABASE={local_db}')
        self.stdout.write(f'  FL_MYSQL_USER={local_user}')
        self.stdout.write(f'  FL_MYSQL_PASSWORD={local_pass}')
