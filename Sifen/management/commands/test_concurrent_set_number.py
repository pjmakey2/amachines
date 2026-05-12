"""
Test de concurrencia para Eserial.set_number.

Crea N DocumentHeader pendientes (doc_numero=NULL) y lanza T threads
que llaman set_number simultaneamente. Despues verifica que cada doc
recibio un numero unico (sin colisiones).

Uso:
  python manage.py test_concurrent_set_number \\
      --ruc 80070523 --timbrado 16561588 \\
      --establecimiento 001 --tipo FE --expd 1 --threads 8

Limpia los docs/numeros de test al final.
"""
import threading
import time
from datetime import date
from collections import Counter
from django.core.management.base import BaseCommand
from django.db import connection, connections
from django.http import QueryDict
from Sifen.models import DocumentHeader, Enumbers, Etimbrado
from Sifen.ekuatia_serials import Eserial

MARKER = 'TEST_CONCURRENCY'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--ruc', required=True)
        parser.add_argument('--timbrado', required=True)
        parser.add_argument('--establecimiento', required=True)
        parser.add_argument('--tipo', default='FE')
        parser.add_argument('--expd', type=int, default=1)
        parser.add_argument('--threads', type=int, default=8)
        parser.add_argument('--keep', action='store_true', help='No borrar los docs/numeros de test al final')

    def handle(self, *args, **opts):
        ruc = opts['ruc']
        timbrado = opts['timbrado']
        establecimiento = opts['establecimiento']
        tipo = opts['tipo']
        expd = opts['expd']
        n_threads = opts['threads']
        keep = opts['keep']

        self.stdout.write(self.style.SUCCESS(
            f'Test: ruc={ruc} timbrado={timbrado} est={establecimiento} tipo={tipo} threads={n_threads}'
        ))

        # Verificar timbrado y establecimiento
        try:
            etimb = Etimbrado.objects.get(timbrado=timbrado)
        except Etimbrado.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Timbrado {timbrado} no existe'))
            return
        try:
            estobj = etimb.eestablecimiento_set.get(establecimiento=establecimiento)
        except Exception:
            self.stdout.write(self.style.ERROR(f'Establecimiento {establecimiento} no existe para timbrado {timbrado}'))
            return

        # Verificar que haya >= n_threads numeros libres
        enum_tipo = 'PD' if tipo == 'MI' else tipo
        libres = Enumbers.objects.filter(expobj=estobj, estado='L', tipo=enum_tipo).count()
        self.stdout.write(f'  Numeros libres disponibles: {libres}')
        if libres < n_threads:
            self.stdout.write(self.style.ERROR(f'Se necesitan al menos {n_threads} numeros libres'))
            return

        # Crear N docs pendientes (uno por thread). Marca observacion para limpieza.
        docs = []
        for i in range(n_threads):
            d = DocumentHeader.objects.create(
                doc_tipo=tipo,
                doc_numero=None,
                doc_fecha=date.today(),
                doc_establecimiento=establecimiento,
                doc_expedicion=expd,
                doc_op='VTA',
                doc_estado='CREADO',
                doc_moneda='GS',
                doc_total=0, doc_iva=0, doc_exenta=0,
                doc_g10=0, doc_i10=0, doc_g5=0, doc_i5=0,
                doc_descuento=0, doc_per_descuento=0, doc_descuento_global=0,
                doc_saldo=0, doc_pago=0, doc_costo=0,
                tasa_cambio=1, peso=0, volumen=0,
                bs='TEST', source=MARKER,
                ek_bs_ruc=ruc, ek_timbrado=timbrado,
                ext_link=f'{MARKER}-{i}',
                observacion=MARKER,
                pdv_ruc='0', pdv_nombrefantasia='TEST', pdv_nombrefactura='TEST',
            )
            docs.append(d)
        self.stdout.write(f'  {len(docs)} docs creados (prof_numbers: {[d.prof_number for d in docs]})')

        # Cerrar la conexion del thread principal para que cada worker abra la suya
        connection.close()

        # Barrier para arrancar todos al mismo tiempo
        barrier = threading.Barrier(n_threads)
        results = [None] * n_threads
        errors = [None] * n_threads

        def worker(idx, prof_number):
            try:
                barrier.wait(timeout=10)
                eser = Eserial()
                qdict = QueryDict(mutable=True)
                qdict.update({
                    'timbrado': timbrado,
                    'establecimiento': establecimiento,
                    'tipo': tipo,
                    'ruc': ruc,
                    'expd': str(expd),
                    'sign_document': '',
                })
                qdict.update({'prof_number': str(prof_number)})
                t0 = time.time()
                result = eser.set_number(qdict=qdict)
                results[idx] = (prof_number, result, time.time() - t0)
            except Exception as e:
                errors[idx] = (prof_number, repr(e))
            finally:
                connections.close_all()

        threads = []
        for i, d in enumerate(docs):
            t = threading.Thread(target=worker, args=(i, d.prof_number))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Resultados por thread ==='))
        for r in results:
            if r:
                prof, rsp, elapsed = r
                self.stdout.write(f'  prof={prof} elapsed={elapsed:.3f}s rsp={rsp}')
        for e in errors:
            if e:
                self.stdout.write(self.style.ERROR(f'  ERROR prof={e[0]}: {e[1]}'))

        # Verificar resultados en DB
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Verificacion en DB ==='))
        prof_numbers = [d.prof_number for d in docs]
        final = list(
            DocumentHeader.objects
            .filter(prof_number__in=prof_numbers)
            .values('prof_number', 'doc_numero')
            .order_by('prof_number')
        )
        for f in final:
            self.stdout.write(f'  prof={f["prof_number"]} doc_numero={f["doc_numero"]}')

        numeros = [f['doc_numero'] for f in final if f['doc_numero'] is not None]
        counts = Counter(numeros)
        duplicados = {n: c for n, c in counts.items() if c > 1}
        none_count = sum(1 for f in final if f['doc_numero'] is None)

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Conclusion ==='))
        self.stdout.write(f'  Docs procesados: {len(final)}')
        self.stdout.write(f'  Docs con numero asignado: {len(numeros)}')
        self.stdout.write(f'  Docs sin numero (None): {none_count}')
        self.stdout.write(f'  Numeros unicos asignados: {len(set(numeros))}')
        if duplicados:
            self.stdout.write(self.style.ERROR(f'  COLISIONES DETECTADAS: {duplicados}'))
        else:
            self.stdout.write(self.style.SUCCESS('  Sin colisiones — todos los numeros son unicos'))

        # Limpieza
        if keep:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('--keep activo, no se limpian docs ni numeros'))
            return

        self.stdout.write('')
        self.stdout.write('Limpiando...')
        # Liberar Enumbers usados
        Enumbers.objects.filter(
            expobj=estobj, tipo=enum_tipo, numero__in=numeros
        ).update(estado='L')
        # Borrar docs de test
        deleted = DocumentHeader.objects.filter(
            prof_number__in=prof_numbers, source=MARKER
        ).delete()
        self.stdout.write(f'  Numeros liberados: {len(numeros)}')
        self.stdout.write(f'  Docs borrados: {deleted}')
