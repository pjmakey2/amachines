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
            '--exclude_tables',
            type=str,
            default='bitacora',
            help='Tablas a excluir del dump, separadas por coma (default: bitacora)',
        )
        parser.add_argument(
            '--sync_remote',
            action='store_true',
            help='Sincroniza frontlin_db desde servidor origen a servidor destino (remoto a remoto)',
        )
        parser.add_argument(
            '--src_host',
            type=str,
            default='',
            help='Host MySQL origen',
        )
        parser.add_argument(
            '--src_user',
            type=str,
            default='mainline',
            help='Usuario MySQL origen (default: mainline)',
        )
        parser.add_argument(
            '--src_pass',
            type=str,
            default='',
            help='Password MySQL origen',
        )
        parser.add_argument(
            '--src_db',
            type=str,
            default='frontlin_db',
            help='BD origen (default: frontlin_db)',
        )
        parser.add_argument(
            '--dst_host',
            type=str,
            default='',
            help='Host MySQL destino',
        )
        parser.add_argument(
            '--dst_user',
            type=str,
            default='mainline',
            help='Usuario MySQL destino (default: mainline)',
        )
        parser.add_argument(
            '--dst_pass',
            type=str,
            default='',
            help='Password MySQL destino',
        )
        parser.add_argument(
            '--dst_db',
            type=str,
            default='frontlin_db',
            help='BD destino (default: frontlin_db)',
        )
        parser.add_argument(
            '--sync_clientes_fl_to_sifen',
            action='store_true',
            help='Importa clientes desde MySQL FL al modelo Sifen.Clientes (sin duplicados por pdv_ruc)',
        )
        parser.add_argument(
            '--marcar_facturados',
            action='store_true',
            help='Marca como factura emitida todos los acuses con estado=2 desde la fecha indicada',
        )
        parser.add_argument(
            '--date',
            type=str,
            default=None,
            help='Fecha desde (YYYY-MM-DD) para --marcar_facturados',
        )
        parser.add_argument(
            '--fix_ext_links',
            action='store_true',
            help='Detecta y repara DocumentHeaders con ext_link=0 que tienen acuse_id en observacion',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra lo que se haría sin hacer cambios',
        )

    def handle(self, *args, **options):
        register_plugin = options.get('register_plugin', False)
        migrate_db = options.get('migrate_db', False)
        sync_remote = options.get('sync_remote', False)
        dry_run = options.get('dry_run', False)

        marcar_facturados = options.get('marcar_facturados', False)

        sync_clientes = options.get('sync_clientes_fl_to_sifen', False)

        fix_ext_links = options.get('fix_ext_links', False)

        if not register_plugin and not migrate_db and not sync_remote and not marcar_facturados and not sync_clientes and not fix_ext_links:
            self.stdout.write(self.style.ERROR('Debe especificar una acción:'))
            self.stdout.write('  --register_plugin   Registrar plugin y menús')
            self.stdout.write('  --migrate_db        Copiar BD remota al localhost')
            self.stdout.write('  --sync_remote       Sincronizar BD entre dos servidores remotos')
            self.stdout.write('  --marcar_facturados --date YYYY-MM-DD  Marcar acuses como facturados desde fecha')
            self.stdout.write('  --sync_clientes_fl_to_sifen             Importar clientes FL → Sifen.Clientes')
            return

        if fix_ext_links:
            self._fix_ext_links(dry_run)
            return

        if sync_clientes:
            self._sync_clientes_fl_to_sifen(options)
            return

        if marcar_facturados:
            self._marcar_facturados(options)
            return

        if sync_remote:
            self._sync_remote(options)
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
        exclude_tables = set(
            t.strip() for t in options.get('exclude_tables', '').split(',') if t.strip()
        )
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
            from pymysql.cursors import SSCursor
        except ImportError:
            self.stdout.write(self.style.ERROR(
                'pymysql no está instalado. Ejecute: pip install pymysql'
            ))
            return

        CHUNK_SIZE = 5000
        CONNECT_KWARGS = dict(
            host=remote_host,
            user=remote_user,
            password=remote_pass,
            database=remote_db,
            charset='utf8',
            ssl_disabled=True,
            connect_timeout=30,
            read_timeout=300,
            write_timeout=300,
        )

        def get_connection():
            conn = pymysql.connect(**CONNECT_KWARGS)
            conn.cursor().execute("SET NET_READ_TIMEOUT=600")
            conn.cursor().execute("SET NET_WRITE_TIMEOUT=600")
            return conn

        def escape_value(v):
            if v is None:
                return "NULL"
            elif isinstance(v, (int, float)):
                return str(v)
            elif isinstance(v, bytes):
                return "X'" + v.hex() + "'"
            else:
                s = str(v)
                s = s.replace("\\", "\\\\")
                s = s.replace("'", "\\'")
                s = s.replace("\n", "\\n")
                s = s.replace("\r", "\\r")
                s = s.replace("\x00", "")
                return "'" + s + "'"

        # 1. Conectar al servidor remoto
        self.stdout.write('\n1. Conectando al servidor remoto...')
        try:
            remote_conn = get_connection()
        except pymysql.Error as e:
            self.stdout.write(self.style.ERROR(f'   Error de conexión: {e}'))
            return

        self.stdout.write(self.style.SUCCESS('   Conectado'))

        # 2. Obtener lista de tablas y conteos
        self.stdout.write('\n2. Analizando tablas...')
        from django.conf import settings
        dump_dir = getattr(settings, 'BASE_DIR', os.getcwd())
        dump_file = os.path.join(dump_dir, f'{remote_db}_dump.sql')

        try:
            cur = remote_conn.cursor()
            cur.execute("SHOW TABLES")
            all_tables = [r[0] for r in cur.fetchall()]
            tables = [t for t in all_tables if t not in exclude_tables]
            self.stdout.write(f'   {len(all_tables)} tablas encontradas, {len(tables)} a migrar')
            if exclude_tables:
                self.stdout.write(f'   Excluidas: {", ".join(sorted(exclude_tables))}')

            # Obtener conteo de filas para progreso
            table_counts = {}
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM `{table}`")
                table_counts[table] = cur.fetchone()[0]
            cur.close()
            remote_conn.close()

            total_rows = sum(table_counts.values())
            self.stdout.write(f'   Total: {total_rows:,} filas')

            # 3. Dump tabla por tabla con conexión fresca por tabla
            self.stdout.write('\n3. Generando dump...')
            with open(dump_file, 'w', encoding='utf-8') as f:
                f.write("SET NAMES utf8;\n")
                f.write("SET FOREIGN_KEY_CHECKS=0;\n")
                f.write("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n\n")

                for table in tables:
                    expected = table_counts[table]
                    self.stdout.write(f'   Dumping: {table} ({expected:,} filas)...', ending=' ')
                    sys.stdout.flush()

                    # Conexión fresca por tabla para evitar timeouts
                    conn = get_connection()

                    # CREATE TABLE (cursor normal)
                    meta_cur = conn.cursor()
                    meta_cur.execute(f"SHOW CREATE TABLE `{table}`")
                    create_sql = meta_cur.fetchone()[1]
                    meta_cur.close()

                    f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
                    f.write(f"{create_sql};\n\n")

                    if expected > 0:
                        # SSCursor: streaming server-side, no carga todo en RAM
                        ss_cur = conn.cursor(SSCursor)
                        ss_cur.execute(f"SELECT * FROM `{table}`")

                        row_count = 0
                        batch = []

                        while True:
                            rows = ss_cur.fetchmany(CHUNK_SIZE)
                            if not rows:
                                break

                            for row in rows:
                                batch.append(
                                    "(" + ",".join(escape_value(v) for v in row) + ")"
                                )
                                row_count += 1

                                if len(batch) >= 1000:
                                    f.write(f"INSERT INTO `{table}` VALUES\n")
                                    f.write(",\n".join(batch))
                                    f.write(";\n")
                                    batch = []

                        if batch:
                            f.write(f"INSERT INTO `{table}` VALUES\n")
                            f.write(",\n".join(batch))
                            f.write(";\n")

                        ss_cur.close()
                    else:
                        row_count = 0

                    conn.close()
                    f.write("\n")
                    self.stdout.write(self.style.SUCCESS(f'{row_count:,} OK'))

                f.write("SET FOREIGN_KEY_CHECKS=1;\n")

            file_size = os.path.getsize(dump_file)
            self.stdout.write(self.style.SUCCESS(
                f'\n   Dump completado: {dump_file} ({file_size / 1024 / 1024:.1f} MB)'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n   Error durante dump: {e}'))
            return

        # 4. Crear BD local y usuario
        self.stdout.write(f'\n4. Preparando BD local "{local_db}"...')
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

        # 5. Importar dump
        self.stdout.write(f'\n5. Importando dump en "{local_db}"...')
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

        # 6. Verificar
        self.stdout.write('\n6. Verificando...')
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

    # =========================================================================
    # SINCRONIZACIÓN REMOTO → REMOTO
    # =========================================================================

    def _sync_remote(self, options):
        """
        Sincroniza frontlin_db desde un servidor MySQL origen a un servidor
        MySQL destino, sin archivo intermedio. Usa SSCursor en origen para
        streaming eficiente y escribe por lotes en el destino.

        Uso:
            python manage.py fl_legacy_mainline --sync_remote \
                --src_pass 'pass_origen' \
                --dst_pass 'pass_destino'

        Parámetros opcionales:
            --src_host  (default: 165.227.53.87)
            --src_user  (default: mainline)
            --src_db    (default: frontlin_db)
            --dst_host  (default: 143.110.238.24)
            --dst_user  (default: mainline)
            --dst_db    (default: frontlin_db)
            --exclude_tables  (default: bitacora)
            --dry-run
        """
        src_host = options['src_host']
        src_user = options['src_user']
        src_pass = options['src_pass']
        src_db   = options['src_db']
        dst_host = options['dst_host']
        dst_user = options['dst_user']
        dst_pass = options['dst_pass']
        dst_db   = options['dst_db']
        exclude_tables = set(
            t.strip() for t in options.get('exclude_tables', '').split(',') if t.strip()
        )
        dry_run = options.get('dry_run', False)

        if not src_host:
            self.stdout.write(self.style.ERROR('Debe especificar --src_host'))
            return
        if not src_pass:
            self.stdout.write(self.style.ERROR('Debe especificar --src_pass'))
            return
        if not dst_host:
            self.stdout.write(self.style.ERROR('Debe especificar --dst_host'))
            return
        if not dst_pass:
            self.stdout.write(self.style.ERROR('Debe especificar --dst_pass'))
            return

        self.stdout.write(self.style.SUCCESS('=== Sincronización Remoto → Remoto ===\n'))
        self.stdout.write(f'  Origen:  {src_user}@{src_host}/{src_db}')
        self.stdout.write(f'  Destino: {dst_user}@{dst_host}/{dst_db}')
        if exclude_tables:
            self.stdout.write(f'  Excluidas: {", ".join(sorted(exclude_tables))}')
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No se ejecutarán cambios'))
            return

        try:
            import pymysql
            from pymysql.cursors import SSCursor
        except ImportError:
            self.stdout.write(self.style.ERROR('pymysql no está instalado. Ejecute: pip install pymysql'))
            return

        CHUNK_SIZE  = 5000
        BATCH_SIZE  = 1000

        def make_conn(host, user, password, db):
            conn = pymysql.connect(
                host=host, user=user, password=password, database=db,
                charset='utf8', ssl_disabled=True,
                connect_timeout=30, read_timeout=600, write_timeout=600,
            )
            with conn.cursor() as c:
                c.execute("SET NET_READ_TIMEOUT=600")
                c.execute("SET NET_WRITE_TIMEOUT=600")
            return conn

        def escape_val(v):
            if v is None:
                return "NULL"
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, bytes):
                return "X'" + v.hex() + "'"
            s = str(v).replace("\\", "\\\\").replace("'", "\\'") \
                       .replace("\n", "\\n").replace("\r", "\\r").replace("\x00", "")
            return "'" + s + "'"

        # 1. Conectar a ambos servidores
        self.stdout.write('\n1. Conectando...')
        try:
            src_conn = make_conn(src_host, src_user, src_pass, src_db)
            self.stdout.write(f'   Origen  OK ({src_host})')
        except pymysql.Error as e:
            self.stdout.write(self.style.ERROR(f'   Error conectando a origen: {e}'))
            return
        try:
            dst_conn = make_conn(dst_host, dst_user, dst_pass, dst_db)
            self.stdout.write(f'   Destino OK ({dst_host})')
        except pymysql.Error as e:
            self.stdout.write(self.style.ERROR(f'   Error conectando a destino: {e}'))
            src_conn.close()
            return

        # 2. Obtener tablas y conteos desde origen
        self.stdout.write('\n2. Analizando tablas en origen...')
        try:
            with src_conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                all_tables = [r[0] for r in cur.fetchall()]
            tables = [t for t in all_tables if t not in exclude_tables]
            self.stdout.write(f'   {len(all_tables)} tablas totales, {len(tables)} a sincronizar')

            table_counts = {}
            for table in tables:
                with src_conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM `{table}`")
                    table_counts[table] = cur.fetchone()[0]

            total_rows = sum(table_counts.values())
            self.stdout.write(f'   Total filas: {total_rows:,}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error analizando tablas: {e}'))
            src_conn.close(); dst_conn.close()
            return

        # 3. Sincronizar tabla por tabla
        self.stdout.write('\n3. Sincronizando...')
        src_conn.close()  # Cerrar; se reabre por tabla para evitar timeouts

        errors = []
        total_synced = 0

        try:
            with dst_conn.cursor() as cur:
                cur.execute("SET FOREIGN_KEY_CHECKS=0")
                cur.execute("SET NAMES utf8")
                cur.execute("SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO'")

            for table in tables:
                expected = table_counts[table]
                self.stdout.write(f'   {table} ({expected:,} filas)...', ending=' ')
                sys.stdout.flush()

                try:
                    # Conexión fresca por tabla (evita timeout en tablas grandes)
                    src_conn = make_conn(src_host, src_user, src_pass, src_db)

                    # Obtener CREATE TABLE desde origen
                    with src_conn.cursor() as meta_cur:
                        meta_cur.execute(f"SHOW CREATE TABLE `{table}`")
                        create_sql = meta_cur.fetchone()[1]

                    # Recrear tabla en destino
                    with dst_conn.cursor() as cur:
                        cur.execute(f"DROP TABLE IF EXISTS `{table}`")
                        cur.execute(create_sql)
                    dst_conn.commit()

                    # Transferir datos si hay filas
                    row_count = 0
                    if expected > 0:
                        ss_cur = src_conn.cursor(SSCursor)
                        ss_cur.execute(f"SELECT * FROM `{table}`")

                        batch = []
                        while True:
                            rows = ss_cur.fetchmany(CHUNK_SIZE)
                            if not rows:
                                break
                            for row in rows:
                                batch.append("(" + ",".join(escape_val(v) for v in row) + ")")
                                row_count += 1
                                if len(batch) >= BATCH_SIZE:
                                    with dst_conn.cursor() as cur:
                                        cur.execute(
                                            f"INSERT INTO `{table}` VALUES " + ",".join(batch)
                                        )
                                    dst_conn.commit()
                                    batch = []

                        if batch:
                            with dst_conn.cursor() as cur:
                                cur.execute(
                                    f"INSERT INTO `{table}` VALUES " + ",".join(batch)
                                )
                            dst_conn.commit()

                        ss_cur.close()

                    src_conn.close()
                    total_synced += row_count
                    self.stdout.write(self.style.SUCCESS(f'{row_count:,} OK'))

                except Exception as e:
                    errors.append((table, str(e)))
                    self.stdout.write(self.style.ERROR(f'ERROR: {e}'))
                    try:
                        src_conn.close()
                    except Exception:
                        pass

            with dst_conn.cursor() as cur:
                cur.execute("SET FOREIGN_KEY_CHECKS=1")
            dst_conn.commit()

        finally:
            try:
                dst_conn.close()
            except Exception:
                pass

        # 4. Resumen
        self.stdout.write('\n' + '=' * 60)
        if errors:
            self.stdout.write(self.style.ERROR(f'Completado con {len(errors)} error(es):'))
            for table, err in errors:
                self.stdout.write(self.style.ERROR(f'  {table}: {err}'))
        else:
            self.stdout.write(self.style.SUCCESS('Sincronización completada sin errores!'))
        self.stdout.write(f'  Filas transferidas: {total_synced:,}')
        self.stdout.write(f'  Tablas sincronizadas: {len(tables) - len(errors)}/{len(tables)}')

    # =========================================================================
    # SINCRONIZACIÓN CLIENTES FL → SIFEN
    # =========================================================================

    def _sync_clientes_fl_to_sifen(self, options):
        """
        Importa clientes desde la tabla `clientes` del MySQL FL al modelo
        Sifen.Clientes (PostgreSQL).

        - Condicionante de duplicado: pdv_ruc (derivado de clienteci limpio)
        - Limpieza de clienteci:
            " 21212 "   → "21212"
            "2463986-9" → "2463986"   (solo la parte antes del guión)
        - Calcula DV con calculate_dv()
        - Si clienteci está vacío/nulo/0, el cliente se marca como innominado

        Uso:
            python manage.py fl_legacy_mainline --sync_clientes_fl_to_sifen
            python manage.py fl_legacy_mainline --sync_clientes_fl_to_sifen --dry-run
        """
        from fl_facturacion_legacy.fl_mysql_client import FLMySQLClient
        from Sifen.models import Clientes
        from Sifen.mng_gmdata import Gdata as Gmdata

        dry_run = options.get('dry_run', False)
        gdata = Gmdata()  # Gdata de mng_gmdata

        self.stdout.write(self.style.SUCCESS('=== Sincronización Clientes FL → Sifen ===\n'))
        if dry_run:
            self.stdout.write(self.style.WARNING('  [DRY RUN] No se harán cambios\n'))

        def clean_ruc(raw):
            """Extrae solo dígitos del clienteci, descartando DV y espacios."""
            if not raw:
                return None
            s = raw.strip()
            # Descartar dígito verificador si viene con guión: "2463986-9" → "2463986"
            if '-' in s:
                s = s.split('-')[0].strip()
            # Quedarse solo con dígitos
            digits = ''.join(c for c in s if c.isdigit())
            return digits if digits else None

        # 1. Leer clientes desde MySQL FL
        self.stdout.write('1. Leyendo clientes desde MySQL FL...')
        db = FLMySQLClient()
        rows = db.execute_query(
            "SELECT clientecodigo, clientenombre, clienteapellido, clienteci, "
            "clientetelefono, clientecelular, clientemail, clientedireccion "
            "FROM clientes ORDER BY clientecodigo"
        )
        self.stdout.write(f'   {len(rows):,} clientes encontrados en MySQL')

        # 2. Obtener RUCs ya existentes en Sifen para evitar duplicados
        self.stdout.write('\n2. Cargando RUCs existentes en Sifen...')
        existing_rucs = set(Clientes.objects.values_list('pdv_ruc', flat=True))
        self.stdout.write(f'   {len(existing_rucs):,} clientes ya existen en Sifen')

        # 3. Procesar y clasificar
        self.stdout.write('\n3. Procesando clientes...')
        to_create = []
        skipped_duplicates = 0
        skipped_sin_ruc = 0
        errores = []

        BATCH_SIZE = 500

        for row in rows:
            clientecodigo = row['clientecodigo']
            nombre = (row.get('clientenombre') or '').strip()
            apellido = (row.get('clienteapellido') or '').strip()
            nombre_completo = f"{nombre} {apellido}".strip() or f"CLIENTE {clientecodigo}"

            ruc_limpio = clean_ruc(row.get('clienteci'))

            # Sin RUC válido → omitir completamente
            if not ruc_limpio or ruc_limpio == '0':
                skipped_sin_ruc += 1
                continue

            innominado = False
            es_contribuyente = True

            # Verificar duplicado
            if ruc_limpio in existing_rucs:
                skipped_duplicates += 1
                continue

            try:
                dv = gdata.calculate_dv(ruc_limpio) if not innominado else 0
            except Exception as e:
                errores.append((clientecodigo, str(e)))
                continue

            to_create.append(Clientes(
                pdv_ruc=ruc_limpio,
                pdv_ruc_dv=dv,
                pdv_innominado=innominado,
                pdv_es_contribuyente=es_contribuyente,
                pdv_nombrefantasia=nombre_completo,
                pdv_nombrefactura=nombre_completo,
                pdv_telefono=row.get('clientetelefono') or None,
                pdv_celular=row.get('clientecelular') or None,
                pdv_email=row.get('clientemail') or None,
                pdv_direccion_entrega=row.get('clientedireccion') or None,
                pdv_codigo=clientecodigo,
                pdv_pais_cod='PRY',
                pdv_pais='PRY',
                pdv_tipocontribuyente='1',
                cargado_usuario='fl_sync',
                anclaje_cliente=str(clientecodigo),
            ))

            # Marcar como existente para evitar duplicados dentro del mismo batch
            existing_rucs.add(ruc_limpio)

            # Insertar en batch
            if len(to_create) >= BATCH_SIZE:
                if not dry_run:
                    Clientes.objects.bulk_create(to_create, ignore_conflicts=True)
                self.stdout.write(f'   Insertados {len(to_create)} clientes...', ending='\r')
                sys.stdout.flush()
                to_create = []

        # Insertar restantes
        if to_create and not dry_run:
            Clientes.objects.bulk_create(to_create, ignore_conflicts=True)

        # 4. Resumen
        total_nuevos = len(rows) - skipped_duplicates - skipped_sin_ruc - len(errores)
        self.stdout.write('\n\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Resumen:'))
        self.stdout.write(f'  Total en MySQL:      {len(rows):,}')
        self.stdout.write(f'  Nuevos importados:   {total_nuevos:,}{"  [DRY RUN]" if dry_run else ""}')
        self.stdout.write(f'  Ya existían:         {skipped_duplicates:,}')
        self.stdout.write(f'  Sin RUC (omitidos):  {skipped_sin_ruc:,}')
        if errores:
            self.stdout.write(self.style.ERROR(f'  Errores:             {len(errores)}'))
            for cod, err in errores[:10]:
                self.stdout.write(self.style.ERROR(f'    clientecodigo={cod}: {err}'))

    # =========================================================================
    # MARCAR ACUSES COMO FACTURADOS
    # =========================================================================

    def _marcar_facturados(self, options):
        """
        Marca facturaemitida=1 en todos los acuses con estado=2
        cuya fecha sea >= la fecha indicada.

        Uso:
            python manage.py fl_legacy_mainline --marcar_facturados --date 2026-01-01
        """
        from fl_facturacion_legacy.fl_mysql_client import FLMySQLClient

        fecha = options.get('date')
        dry_run = options.get('dry_run', False)

        if not fecha:
            self.stdout.write(self.style.ERROR('Debe especificar --date YYYY-MM-DD'))
            return

        self.stdout.write(self.style.SUCCESS('=== Marcar Acuses como Facturados ===\n'))
        self.stdout.write(f'  Fecha desde: {fecha}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  [DRY RUN] No se harán cambios\n'))

        db = FLMySQLClient()

        # Contar cuántos se van a afectar
        rows = db.execute_query(
            'SELECT COUNT(*) as cnt FROM facturas WHERE estado = 2 AND facturaemitida = 2 AND fecha <= %s',
            (fecha,)
        )
        total = rows[0]['cnt'] if rows else 0
        self.stdout.write(f'  Acuses a marcar: {total}')

        if total == 0:
            self.stdout.write(self.style.WARNING('  No hay acuses para marcar.'))
            return

        if not dry_run:
            affected = db.execute_update(
                'UPDATE facturas SET facturaemitida = 1 WHERE estado = 2 AND facturaemitida = 2 AND fecha <= %s',
                (fecha,)
            )
            self.stdout.write(self.style.SUCCESS(f'  {affected} acuses marcados como facturados.'))
        else:
            self.stdout.write(f'  [DRY] Se marcarían {total} acuses.')

        self.stdout.write(self.style.SUCCESS('\nListo!'))

    def _fix_ext_links(self, dry_run=False):
        """Detecta DocumentHeaders con ext_link=0 que tienen 'Acuse: NNNN' en observacion y repara el ext_link."""
        import re
        from Sifen.models import DocumentHeader

        self.stdout.write(self.style.SUCCESS('=== Reparando ext_link perdidos ==='))
        docs = DocumentHeader.objects.filter(ext_link__in=[0, None, '']).exclude(observacion='')
        found = 0
        fixed = 0
        for doc in docs:
            match = re.search(r'Acuse:\s*(\d+)', doc.observacion or '')
            if not match:
                continue
            acuse_id = match.group(1)
            found += 1
            self.stdout.write(f'  pk={doc.pk} doc_numero={doc.doc_numero} ext_link={doc.ext_link} -> acuse={acuse_id}')
            if not dry_run:
                DocumentHeader.objects.filter(pk=doc.pk).update(ext_link=acuse_id)
                fixed += 1

        if found == 0:
            self.stdout.write(self.style.WARNING('  No se encontraron ext_links rotos'))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'  [DRY] Se repararían {found} registros'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  {fixed} ext_links reparados'))
