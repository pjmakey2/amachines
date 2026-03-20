#!/usr/bin/env python3
"""
dump_mysql_compat.py
Dump de base de datos MySQL/MariaDB compatible con cualquier version del servidor.
Usa pymysql para evitar incompatibilidades del cliente mysqldump local.
Escribe directamente al archivo (no acumula en RAM) y hace fetch por lotes.

Uso:
    python3 dump_mysql_compat.py <host> <port> <user> <password> <database> [archivo_salida.sql] [--exclude tabla1,tabla2]

Ejemplo:
    python3 dump_mysql_compat.py 165.227.23.149 3306 upj_sys 'ZrLn4j0@Yo*l1fyu' frontlin_db
    python3 dump_mysql_compat.py 165.227.23.149 3306 upj_sys 'ZrLn4j0@Yo*l1fyu' frontlin_db dump.sql --exclude bitacora,auditorias
"""
import pymysql
import sys
import bz2
from datetime import datetime

BATCH_SIZE = 1000

def escape_value(v):
    if v is None:
        return 'NULL'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, bytes):
        return "0x" + v.hex()
    s = str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r").replace("\0", "")
    return f"'{s}'"

def dump(host, port, user, password, db, out_file, exclude=None, compress=False):
    exclude = set(exclude or [])

    conn = pymysql.connect(host=host, port=int(port), user=user, password=password, db=db,
                           charset='utf8mb4', ssl={'ssl': {}})
    cur = conn.cursor()

    # Cursor separado para datos (SSCursor = streaming, no carga todo en RAM)
    data_cur = conn.cursor(pymysql.cursors.SSCursor)

    cur.execute("SHOW TABLES")
    all_tables = [row[0] for row in cur.fetchall()]
    tables = [t for t in all_tables if t not in exclude]

    if exclude:
        skipped = [t for t in all_tables if t in exclude]
        print(f"Tablas excluidas: {', '.join(skipped)}")
    print(f"Tablas a dumpear: {len(tables)}")

    opener = bz2.open if compress else open
    mode   = 'wt' if compress else 'w'
    with opener(out_file, mode, encoding='utf-8') as f:
        f.write(f'-- Dump de {db} desde {host}\n')
        f.write(f'-- Fecha: {datetime.now().isoformat()}\n')
        f.write('SET FOREIGN_KEY_CHECKS=0;\n')
        f.write('SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";\n')
        f.write('SET NAMES utf8mb4;\n\n')

        for table in tables:
            print(f"  Dumpeando: {table} ...", end='', flush=True)

            # Estructura
            cur.execute(f"SHOW CREATE TABLE `{table}`")
            create = cur.fetchone()[1]
            f.write(f'DROP TABLE IF EXISTS `{table}`;\n')
            f.write(create + ';\n\n')

            # Columnas
            cur.execute(f"SHOW COLUMNS FROM `{table}`")
            cols = [f"`{c[0]}`" for c in cur.fetchall()]
            col_str = ', '.join(cols)

            # Datos en streaming por lotes
            data_cur.execute(f"SELECT * FROM `{table}`")
            count = 0
            while True:
                rows = data_cur.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                for row in rows:
                    vals = ', '.join(escape_value(v) for v in row)
                    f.write(f"INSERT INTO `{table}` ({col_str}) VALUES ({vals});\n")
                count += len(rows)

            if count:
                f.write('\n')
            print(f" {count} filas")

        f.write('SET FOREIGN_KEY_CHECKS=1;\n')

    data_cur.close()
    cur.close()
    conn.close()
    print(f"\nDump guardado en: {out_file}")


if __name__ == '__main__':
    if len(sys.argv) < 6:
        print(__doc__)
        sys.exit(1)

    host     = sys.argv[1]
    port     = sys.argv[2]
    user     = sys.argv[3]
    password = sys.argv[4]
    db       = sys.argv[5]

    exclude = []
    remaining = sys.argv[6:]
    out = None
    i = 0
    while i < len(remaining):
        if remaining[i] == '--exclude' and i + 1 < len(remaining):
            exclude = [t.strip() for t in remaining[i+1].split(',')]
            i += 2
        else:
            out = remaining[i]
            i += 1

    compress = '--bzip2' in remaining
    if compress:
        remaining = [r for r in remaining if r != '--bzip2']

    if not out:
        suffix = '_no_' + '_'.join(exclude) if exclude else ''
        ext = '.sql.bz2' if compress else '.sql'
        out = f"{db}{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"

    dump(host, port, user, password, db, out, exclude=exclude, compress=compress)
