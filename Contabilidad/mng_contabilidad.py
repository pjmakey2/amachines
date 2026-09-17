"""
Contabilidad: plan de cuentas (plantillas extensibles), roles y mapeos de cuentas, formatos de
asiento, asientos manuales, reproceso de eventos y reportes (diario, mayor, sumas y saldos,
estado de resultados, balance general).
"""
import re
from datetime import date, datetime
from io import BytesIO
from decimal import Decimal

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q, Sum
from openpyxl import Workbook
from openpyxl.styles import Font

from Contabilidad import handlers, rg90
from Contabilidad.models import (
    Asiento, AsientoDetalle, ConfigContable, CuentaRol, FormatoAsiento, FormatoAsientoLinea, MapeoCuenta, PlanCuenta,
)
from Contabilidad.plantillas.formatos import FORMATOS, ROLES
from Contabilidad.plantillas.planes import PLANTILLAS
from OptsIO.io_business import get_active_business, siguiente_numero, user_label
from OptsIO.io_json import from_json
from OptsIO.io_money import precision_monetaria
from OptsIO.models import BusinessEvent

RE_DECIMAL = re.compile(r'^\d+(\.\d+)?$')
RE_FECHA = re.compile(r'^\d{4}-\d{2}-\d{2}$')
RE_CODIGO = re.compile(r'^\d+(\.\d+)*$')
RE_PERIODO = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')

# Evento -> handler que genera su asiento (mismo mapa que publica plugin.py)
HANDLERS = {
    'sifen.documento.aprobado': handlers.asiento_venta,
    'sifen.documento.cancelado': handlers.reverso,
    'cobro.recibo.aprobado': handlers.asiento_cobro,
    'deposito.deposito.aprobado': handlers.asiento_deposito,
    'egreso.gasto.aprobado': handlers.asiento_gasto,
    'egreso.gasto.rendido': handlers.asiento_gasto_rendido,
    'egreso.pago.aprobado': handlers.asiento_pago,
    'egreso.transferencia.aprobado': handlers.asiento_transferencia,
}
# Registros de otros plugins que pueden tener cuenta contable propia: tipo -> (app, modelo)
MAPEABLES = {'cuenta_bancaria': ('Tesoreria', 'CuentaBancaria'), 'caja': ('Tesoreria', 'Caja'),
             'categoria_gasto': ('Egreso', 'CategoriaGasto')}


def _dec(value) -> Decimal:
    texto = str(value if value is not None else '').strip()
    return Decimal(texto) if RE_DECIMAL.match(texto) else Decimal(0)


def _fecha(value, default=None):
    texto = str(value or '').strip()[:10]
    return datetime.strptime(texto, '%Y-%m-%d').date() if RE_FECHA.match(texto) else default


def _padre_de(codigo: str, cuentas: dict):
    """Cuenta existente cuyo codigo es el prefijo mas largo de `codigo` (1.1.01 es padre de 1.1.01.04)."""
    partes = codigo.split('.')
    for n in range(len(partes) - 1, 0, -1):
        padre = cuentas.get('.'.join(partes[:n]))
        if padre:
            return padre
    return None


class MContabilidad:

    # ------------------------------------------------------------------ Plantillas y configuracion

    def get_config(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}
        config = ConfigContable.objects.filter(businessobj=bobj).first()
        roles = {r.rol: r.cuentaobj_id for r in CuentaRol.objects.filter(businessobj=bobj)}
        mapeos = {(m.tipo, m.ref_id): m.cuentaobj_id for m in MapeoCuenta.objects.filter(businessobj=bobj)}
        mapeables = []
        for tipo, (app, modelo) in MAPEABLES.items():
            if apps.is_installed(app):
                for obj in apps.get_model(app, modelo).objects.filter(businessobj=bobj, activo=True):
                    mapeables.append({'tipo': tipo, 'ref_id': obj.pk, 'ref_desc': str(obj), 'cuenta_id': mapeos.get((tipo, obj.pk))})
        return {
            'success': True,
            'plantilla': config.plantilla if config else '',
            'fecha_inicio': config.fecha_inicio.strftime('%Y-%m-%d') if config and config.fecha_inicio else '',
            'plantillas': [{'clave': k, 'nombre': v['nombre'], 'descripcion': v['descripcion'], 'cuentas': len(v['cuentas'])}
                           for k, v in PLANTILLAS.items()],
            'roles': [{'rol': rol, 'descripcion': desc, 'cuenta_id': roles.get(rol)} for rol, desc in ROLES.items()],
            'mapeables': mapeables,
            'cuentas': [{'id': c.pk, 'text': str(c)} for c in PlanCuenta.objects.filter(businessobj=bobj, imputable=True, activo=True)],
        }

    def aplicar_plantilla(self, *args, **kwargs) -> dict:
        """
        Crea las cuentas, roles y formatos de asiento de la plantilla que aun no existan.
        Nunca pisa lo existente: se puede re-aplicar o combinar con otra plantilla para extender el plan.
        """
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        plantilla = PLANTILLAS.get(q.get('plantilla'))
        if not bobj or not plantilla:
            return {'error': 'Plantilla inválida'}
        ahora, usuario = datetime.now(), user_label(userobj)
        with transaction.atomic():
            config, _ = ConfigContable.objects.get_or_create(businessobj=bobj, defaults={
                'cargado_fecha': ahora, 'cargado_usuario': usuario, 'fecha_inicio': _fecha(q.get('fecha_inicio'))})
            config.plantilla = q.get('plantilla')
            if _fecha(q.get('fecha_inicio')):
                config.fecha_inicio = _fecha(q.get('fecha_inicio'))
            config.save()

            cuentas = {c.codigo: c for c in PlanCuenta.objects.filter(businessobj=bobj)}
            codigos = [c[0] for c in plantilla['cuentas']]
            creadas = 0
            for codigo, nombre, tipo, rol in sorted(plantilla['cuentas'], key=lambda c: [int(p) for p in c[0].split('.')]):
                if codigo not in cuentas:
                    agrupa = any(otro.startswith(codigo + '.') for otro in codigos)
                    cuentas[codigo] = PlanCuenta.objects.create(
                        businessobj=bobj, codigo=codigo, nombre=plantilla['renombrar'].get(codigo, nombre), tipo=tipo,
                        padreobj=_padre_de(codigo, cuentas), nivel=len(codigo.split('.')), imputable=not agrupa,
                        cargado_fecha=ahora, cargado_usuario=usuario)
                    creadas += 1
                if rol and cuentas[codigo].imputable:
                    CuentaRol.objects.get_or_create(businessobj=bobj, rol=rol, defaults={
                        'cuentaobj': cuentas[codigo], 'cargado_fecha': ahora, 'cargado_usuario': usuario})
            formatos = 0
            for f in FORMATOS:
                formato, nuevo = FormatoAsiento.objects.get_or_create(businessobj=bobj, evento=f['evento'], defaults={
                    'nombre': f['nombre'], 'concepto': f['concepto'], 'cargado_fecha': ahora, 'cargado_usuario': usuario})
                if nuevo:
                    formatos += 1
                    FormatoAsientoLinea.objects.bulk_create([
                        FormatoAsientoLinea(formatoobj=formato, orden=i, lado=lado, rol=rol, monto=monto, glosa=glosa)
                        for i, (lado, rol, monto, glosa) in enumerate(f['lineas'], 1)])
        return {'success': f"Plantilla '{plantilla['nombre']}' aplicada: {creadas} cuentas y {formatos} formatos de asiento nuevos."}

    def set_fecha_inicio(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        n = ConfigContable.objects.filter(businessobj=bobj).update(fecha_inicio=_fecha(kwargs.get('qdict', {}).get('fecha_inicio')))
        return {'success': 'Fecha de inicio actualizada'} if n else {'error': 'Aplique primero una plantilla'}

    def set_rol(self, *args, **kwargs) -> dict:
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        cuenta = PlanCuenta.objects.filter(pk=q.get('cuenta_id') or 0, businessobj=bobj, imputable=True).first()
        if q.get('rol') not in ROLES:
            return {'error': 'Rol inválido'}
        if not cuenta:
            CuentaRol.objects.filter(businessobj=bobj, rol=q.get('rol')).delete()
            return {'success': f"Rol {q.get('rol')} sin cuenta"}
        CuentaRol.objects.update_or_create(businessobj=bobj, rol=q.get('rol'), defaults={
            'cuentaobj': cuenta, 'actualizado_fecha': datetime.now(), 'actualizado_usuario': user_label(userobj)})
        return {'success': f"{q.get('rol')} → {cuenta}"}

    def set_mapeo(self, *args, **kwargs) -> dict:
        userobj, q = kwargs.get('userobj'), kwargs.get('qdict', {})
        bobj = get_active_business(userobj)
        tipo = q.get('tipo')
        if tipo not in MAPEABLES or not apps.is_installed(MAPEABLES[tipo][0]):
            return {'error': 'Tipo de mapeo inválido'}
        ref = apps.get_model(*MAPEABLES[tipo]).objects.filter(pk=q.get('ref_id') or 0, businessobj=bobj).first()
        if not ref:
            return {'error': 'Registro inexistente'}
        cuenta = PlanCuenta.objects.filter(pk=q.get('cuenta_id') or 0, businessobj=bobj, imputable=True).first()
        if not cuenta:
            MapeoCuenta.objects.filter(businessobj=bobj, tipo=tipo, ref_id=ref.pk).delete()
            return {'success': f'{ref}: usa la cuenta del rol por defecto'}
        MapeoCuenta.objects.update_or_create(businessobj=bobj, tipo=tipo, ref_id=ref.pk, defaults={
            'cuentaobj': cuenta, 'ref_desc': str(ref)[:200], 'actualizado_fecha': datetime.now(),
            'actualizado_usuario': user_label(userobj)})
        return {'success': f'{ref} → {cuenta}'}

    # ------------------------------------------------------------------ Plan de cuentas

    def create_cuenta(self, *args, **kwargs) -> tuple:
        """c_a de PlanCuentaCreateUi. El padre y el nivel salen del codigo; el tipo se hereda del padre."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        codigo, nombre = (f.get('codigo') or '').strip(), (f.get('nombre') or '').strip()
        if not RE_CODIGO.match(codigo) or not nombre:
            return {'error': 'Código (ej: 6.1.13) y nombre son obligatorios'}, args, kwargs
        cuentas = {c.codigo: c for c in PlanCuenta.objects.filter(businessobj=bobj)}
        activo = str(f.get('activo', 'true')).lower() in ('true', '1', 'on')
        with transaction.atomic():
            if f.get('id'):
                cuenta = PlanCuenta.objects.filter(pk=f.get('id'), businessobj=bobj).first()
                if not cuenta:
                    return {'error': 'Cuenta inexistente'}, args, kwargs
                if cuenta.codigo != codigo:
                    return {'error': 'El código de una cuenta no se modifica: cree otra y desactive esta'}, args, kwargs
                PlanCuenta.objects.filter(pk=cuenta.pk).update(
                    nombre=nombre, activo=activo, actualizado_fecha=datetime.now(), actualizado_usuario=user_label(userobj))
                return {'success': f'Cuenta {codigo} actualizada', 'record_id': cuenta.pk}, args, kwargs
            if codigo in cuentas:
                return {'error': f'Ya existe la cuenta {cuentas[codigo]}'}, args, kwargs
            padre = _padre_de(codigo, cuentas)
            tipo = padre.tipo if padre else f.get('tipo')
            if tipo not in dict(PlanCuenta.TIPOS):
                return {'error': 'Una cuenta de primer nivel requiere el tipo'}, args, kwargs
            if padre and padre.imputable:
                if AsientoDetalle.objects.filter(cuentaobj=padre).exists():
                    return {'error': f'{padre} ya tiene movimientos: no puede pasar a ser cuenta agrupadora'}, args, kwargs
                if CuentaRol.objects.filter(cuentaobj=padre).exists() or MapeoCuenta.objects.filter(cuentaobj=padre).exists():
                    return {'error': f'{padre} está asignada a un rol o mapeo: reasígnelo antes de abrirle subcuentas'}, args, kwargs
                PlanCuenta.objects.filter(pk=padre.pk).update(imputable=False)
            cuenta = PlanCuenta.objects.create(
                businessobj=bobj, codigo=codigo, nombre=nombre, tipo=tipo, padreobj=padre, nivel=len(codigo.split('.')),
                imputable=True, activo=activo, cargado_fecha=datetime.now(), cargado_usuario=user_label(userobj))
        return {'success': f'Cuenta {cuenta} creada', 'record_id': cuenta.pk}, args, kwargs

    def delete_cuentas(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        ids = list(PlanCuenta.objects.filter(pk__in=from_json(kwargs.get('qdict', {}).get('ids', '[]')), businessobj=bobj).values_list('pk', flat=True))
        en_uso = (AsientoDetalle.objects.filter(cuentaobj_id__in=ids).exists() or PlanCuenta.objects.filter(padreobj_id__in=ids).exists()
                  or CuentaRol.objects.filter(cuentaobj_id__in=ids).exists() or MapeoCuenta.objects.filter(cuentaobj_id__in=ids).exists()
                  or FormatoAsientoLinea.objects.filter(cuentaobj_id__in=ids).exists())
        if en_uso:
            return {'msgs': [{'error': 'La cuenta tiene movimientos, subcuentas o está asignada a un rol/mapeo/formato: desactívela'}]}
        n, _ = PlanCuenta.objects.filter(pk__in=ids).delete()
        return {'msgs': [{'success': f'{n} cuenta(s) borrada(s)'}]}

    # ------------------------------------------------------------------ Formatos de asiento

    def get_formato(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        formato = FormatoAsiento.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not formato:
            return {'error': 'Formato inexistente'}
        return {'success': True, 'roles': list(ROLES), 'lineas': [
            {'lado': l.lado, 'rol': l.rol, 'cuenta_id': l.cuentaobj_id, 'monto': l.monto, 'glosa': l.glosa} for l in formato.lineas.all()]}

    def save_formato(self, *args, **kwargs) -> tuple:
        """c_a de FormatoAsientoCreateUi: nombre, concepto, activo y lineas del formato."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        formato = FormatoAsiento.objects.filter(pk=f.get('id') or 0, businessobj=bobj).first()
        if not formato:
            return {'error': 'Los formatos nacen de una plantilla: aplique una y edítelo'}, args, kwargs
        lineas = [l for l in (f.get('lineas') or []) if (l.get('monto') or '').strip()]
        cuentas = {c.pk: c for c in PlanCuenta.objects.filter(businessobj=bobj, imputable=True)}
        for l in lineas:
            if l.get('lado') not in ('debe', 'haber'):
                return {'error': 'Cada línea va al debe o al haber'}, args, kwargs
            if not l.get('cuenta_id') and l.get('rol') not in ROLES:
                return {'error': f"La línea '{l.get('monto')}' necesita un rol o una cuenta fija"}, args, kwargs
            if l.get('cuenta_id') and int(l.get('cuenta_id')) not in cuentas:
                return {'error': 'Cuenta fija inválida (debe ser imputable)'}, args, kwargs
        if not {l.get('lado') for l in lineas} == {'debe', 'haber'}:
            return {'error': 'El formato necesita al menos una línea al debe y una al haber'}, args, kwargs
        with transaction.atomic():
            formato.nombre = (f.get('nombre') or formato.nombre).strip()[:200]
            formato.concepto = (f.get('concepto') or formato.concepto).strip()[:300]
            formato.activo = str(f.get('activo', 'true')).lower() in ('true', '1', 'on')
            formato.actualizado_fecha, formato.actualizado_usuario = datetime.now(), user_label(userobj)
            formato.save()
            formato.lineas.all().delete()
            FormatoAsientoLinea.objects.bulk_create([FormatoAsientoLinea(
                formatoobj=formato, orden=i, lado=l.get('lado'), rol=l.get('rol') or '', monto=l.get('monto').strip(),
                cuentaobj=cuentas.get(int(l.get('cuenta_id'))) if l.get('cuenta_id') else None,
                glosa=(l.get('glosa') or '').strip()[:200]) for i, l in enumerate(lineas, 1)])
        return {'success': f'Formato "{formato.nombre}" guardado', 'record_id': formato.pk}, args, kwargs

    # ------------------------------------------------------------------ Asientos

    @precision_monetaria
    def create_asiento(self, *args, **kwargs) -> tuple:
        """c_a de AsientoCreateUi: asiento manual. Se edita solo en 'cargado'; cuenta para reportes al aprobarse."""
        userobj = kwargs.get('userobj')
        f = from_json(kwargs.get('qdict', {}).get('uc_fields', '{}'))
        bobj = get_active_business(userobj)
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}, args, kwargs
        fecha, concepto = _fecha(f.get('fecha')), (f.get('concepto') or '').strip()
        lineas = [l for l in (f.get('lineas') or []) if l.get('cuenta_id') and (_dec(l.get('debe')) > 0 or _dec(l.get('haber')) > 0)]
        cuentas = {c.pk: c for c in PlanCuenta.objects.filter(businessobj=bobj, imputable=True, activo=True)}
        if not fecha or not concepto or len(lineas) < 2:
            return {'error': 'Fecha, concepto y al menos dos líneas son obligatorios'}, args, kwargs
        for l in lineas:
            if int(l.get('cuenta_id')) not in cuentas:
                return {'error': 'Hay líneas con cuentas inválidas o no imputables'}, args, kwargs
            if _dec(l.get('debe')) > 0 and _dec(l.get('haber')) > 0:
                return {'error': 'Una línea va al debe o al haber, no a ambos'}, args, kwargs
        debe, haber = sum(_dec(l.get('debe')) for l in lineas), sum(_dec(l.get('haber')) for l in lineas)
        if debe != haber:
            return {'error': f'El asiento no balancea: debe {debe:,.2f} / haber {haber:,.2f}'}, args, kwargs
        with transaction.atomic():
            if f.get('id'):
                asiento = Asiento.objects.select_for_update().filter(pk=f.get('id'), businessobj=bobj).first()
                if not asiento:
                    return {'error': 'Asiento inexistente'}, args, kwargs
                if asiento.origen != 'manual' or asiento.estado != 'cargado' or asiento.anulado:
                    return {'error': 'Solo se modifica un asiento manual en estado cargado'}, args, kwargs
                asiento.actualizado_fecha, asiento.actualizado_usuario = datetime.now(), user_label(userobj)
            else:
                asiento = Asiento(businessobj=bobj, numero=siguiente_numero(Asiento, bobj), origen='manual')
                asiento.registrar_carga(userobj)
            asiento.fecha, asiento.concepto, asiento.total = fecha, concepto[:300], debe
            asiento.save()
            asiento.detalles.all().delete()
            AsientoDetalle.objects.bulk_create([AsientoDetalle(
                asientoobj=asiento, cuentaobj=cuentas[int(l.get('cuenta_id'))], debe=_dec(l.get('debe')), haber=_dec(l.get('haber')),
                glosa=(l.get('glosa') or '').strip()[:200]) for l in lineas])
        return {'success': f'Asiento {asiento.get_numero_display()} guardado', 'record_id': asiento.pk}, args, kwargs

    def get_asiento(self, *args, **kwargs) -> dict:
        bobj = get_active_business(kwargs.get('userobj'))
        asiento = Asiento.objects.filter(pk=kwargs.get('qdict', {}).get('id') or 0, businessobj=bobj).first()
        if not asiento:
            return {'error': 'Asiento inexistente'}
        return {'success': True, 'lineas': [{
            'cuenta_id': d.cuentaobj_id, 'cuenta': str(d.cuentaobj), 'debe': float(d.debe), 'haber': float(d.haber), 'glosa': d.glosa,
        } for d in asiento.detalles.select_related('cuentaobj')]}

    def reprocesar_eventos(self, *args, **kwargs) -> dict:
        """
        Vuelve a pasar por contabilidad los eventos del negocio en un rango de fechas. Sirve cuando se
        configuro la contabilidad despues de operar, o tras corregir un rol/formato. No duplica asientos.
        """
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        desde, hasta = _fecha(q.get('desde'), date(2000, 1, 1)), _fecha(q.get('hasta'), date.today())
        eventos = BusinessEvent.objects.filter(
            business=bobj, created_at__date__gte=desde, created_at__date__lte=hasta).filter(
            Q(event_type__in=list(HANDLERS)) | Q(event_type__endswith='.anulado')).order_by('created_at')
        nuevos = omitidos = 0
        for event in eventos:
            resultado = HANDLERS.get(event.event_type, handlers.reverso)(event)
            if resultado.get('asiento') and not resultado.get('existente') or resultado.get('reversos'):
                nuevos += 1
            else:
                omitidos += 1
        return {'success': f'{nuevos} asiento(s) generado(s); {omitidos} evento(s) ya asentados o sin formato.'}

    # ------------------------------------------------------------------ Reportes

    def _movimientos(self, bobj, desde, hasta):
        """Lineas de asientos que cuentan para los libros: aprobados y no anulados."""
        qs = AsientoDetalle.objects.filter(asientoobj__businessobj=bobj, asientoobj__estado='aprobado', asientoobj__anulado=False)
        if desde:
            qs = qs.filter(asientoobj__fecha__gte=desde)
        return qs.filter(asientoobj__fecha__lte=hasta)

    @precision_monetaria
    def _saldos_jerarquicos(self, bobj, desde, hasta, tipos):
        """[{codigo, nombre, tipo, nivel, imputable, saldo}] con los saldos acumulados hacia las cuentas padre."""
        cuentas = list(PlanCuenta.objects.filter(businessobj=bobj, tipo__in=tipos).order_by('codigo'))
        sumas = {r['cuentaobj_id']: (r['d'] or 0, r['h'] or 0) for r in self._movimientos(bobj, desde, hasta).filter(
            cuentaobj__tipo__in=tipos).values('cuentaobj_id').annotate(d=Sum('debe'), h=Sum('haber'))}
        saldos = {c.pk: Decimal(0) for c in cuentas}
        por_id = {c.pk: c for c in cuentas}
        for c in cuentas:
            debe, haber = sumas.get(c.pk, (0, 0))
            saldo = (debe - haber) if c.deudora else (haber - debe)
            nodo = c
            while nodo is not None and saldo:
                saldos[nodo.pk] += saldo
                nodo = por_id.get(nodo.padreobj_id)
        return [{'codigo': c.codigo, 'nombre': c.nombre, 'tipo': c.tipo, 'nivel': c.nivel, 'imputable': c.imputable,
                 'saldo': float(saldos[c.pk])} for c in cuentas if saldos[c.pk]]

    @precision_monetaria
    def get_reporte(self, *args, **kwargs) -> dict:
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        if not bobj:
            return {'error': 'El usuario no tiene un negocio activo'}
        reporte = q.get('reporte')
        desde, hasta = _fecha(q.get('desde')), _fecha(q.get('hasta'), date.today())
        titulo = {'diario': 'Libro Diario', 'mayor': 'Libro Mayor', 'sumas_saldos': 'Balance de Sumas y Saldos',
                  'resultados': 'Estado de Resultados', 'balance': 'Balance General'}.get(reporte)
        if not titulo:
            return {'error': 'Reporte inválido'}
        data = getattr(self, f'_rpt_{reporte}')(bobj, desde, hasta, q)
        data.update({'success': True, 'titulo': titulo, 'negocio': bobj.name,
                     'periodo': f"{desde.strftime('%d/%m/%Y') if desde else 'Inicio'} al {hasta.strftime('%d/%m/%Y')}"})
        if q.get('excel'):
            return {'success': True, 'excel_file': self._excel(data)}
        return data

    def _rpt_diario(self, bobj, desde, hasta, q):
        filas = []
        asientos = Asiento.objects.filter(businessobj=bobj, estado='aprobado', anulado=False, fecha__lte=hasta)
        if desde:
            asientos = asientos.filter(fecha__gte=desde)
        for a in asientos.order_by('fecha', 'numero').prefetch_related('detalles__cuentaobj'):
            filas.append({'titulo': True, 'celdas': [a.fecha.strftime('%d/%m/%Y'), f"Asiento {a.get_numero_display()}", a.concepto, '', '']})
            for d in a.detalles.all():
                filas.append({'celdas': ['', d.cuentaobj.codigo, ('    ' if d.haber else '') + d.cuentaobj.nombre, float(d.debe), float(d.haber)]})
        return {'columnas': ['Fecha', 'Código', 'Cuenta / Concepto', 'Debe', 'Haber'], 'filas': filas}

    def _rpt_mayor(self, bobj, desde, hasta, q):
        cuenta = PlanCuenta.objects.filter(pk=q.get('cuenta_id') or 0, businessobj=bobj).first()
        if not cuenta:
            return {'columnas': [], 'filas': [], 'aviso': 'Seleccione una cuenta'}
        signo = 1 if cuenta.deudora else -1
        anterior = self._movimientos(bobj, None, hasta).filter(cuentaobj=cuenta, asientoobj__fecha__lt=desde).aggregate(
            d=Sum('debe'), h=Sum('haber')) if desde else {'d': 0, 'h': 0}
        saldo = ((anterior['d'] or 0) - (anterior['h'] or 0)) * signo
        filas = [{'titulo': True, 'celdas': ['', '', f'{cuenta} — saldo anterior', '', '', float(saldo)]}]
        movs = self._movimientos(bobj, desde, hasta).filter(cuentaobj=cuenta).select_related('asientoobj').order_by('asientoobj__fecha', 'asientoobj__numero', 'id')
        for d in movs:
            saldo += (d.debe - d.haber) * signo
            filas.append({'celdas': [d.asientoobj.fecha.strftime('%d/%m/%Y'), d.asientoobj.get_numero_display(),
                                     d.asientoobj.concepto, float(d.debe), float(d.haber), float(saldo)]})
        return {'columnas': ['Fecha', 'Asiento', 'Concepto', 'Debe', 'Haber', 'Saldo'], 'filas': filas}

    def _rpt_sumas_saldos(self, bobj, desde, hasta, q):
        filas, td, th = [], Decimal(0), Decimal(0)
        sumas = self._movimientos(bobj, desde, hasta).values('cuentaobj__codigo', 'cuentaobj__nombre').annotate(
            d=Sum('debe'), h=Sum('haber')).order_by('cuentaobj__codigo')
        for r in sumas:
            debe, haber = r['d'] or 0, r['h'] or 0
            td, th = td + debe, th + haber
            filas.append({'celdas': [r['cuentaobj__codigo'], r['cuentaobj__nombre'], float(debe), float(haber),
                                     float(max(debe - haber, 0)), float(max(haber - debe, 0))]})
        filas.append({'titulo': True, 'celdas': ['', 'TOTALES', float(td), float(th), '', '']})
        return {'columnas': ['Código', 'Cuenta', 'Debe', 'Haber', 'Saldo deudor', 'Saldo acreedor'], 'filas': filas}

    def _rpt_resultados(self, bobj, desde, hasta, q):
        cuentas = self._saldos_jerarquicos(bobj, desde, hasta, ['ingreso', 'costo', 'gasto'])
        total = lambda tipo: sum((Decimal(str(c['saldo'])) for c in cuentas if c['tipo'] == tipo and c['nivel'] == 1), Decimal(0))
        ingresos, costos, gastos = total('ingreso'), total('costo'), total('gasto')
        filas = []
        for tipo, etiqueta in (('ingreso', None), ('costo', ('UTILIDAD BRUTA', ingresos - costos)), ('gasto', ('RESULTADO DEL PERÍODO', ingresos - costos - gastos))):
            for c in (c for c in cuentas if c['tipo'] == tipo):
                filas.append({'titulo': not c['imputable'], 'celdas': [c['codigo'], '    ' * (c['nivel'] - 1) + c['nombre'], c['saldo']]})
            if etiqueta:
                filas.append({'titulo': True, 'total': True, 'celdas': ['', etiqueta[0], float(etiqueta[1])]})
        return {'columnas': ['Código', 'Cuenta', 'Importe'], 'filas': filas,
                'resumen': {'ingresos': float(ingresos), 'costos': float(costos), 'gastos': float(gastos),
                            'resultado': float(ingresos - costos - gastos)}}

    def _rpt_balance(self, bobj, desde, hasta, q):
        """Balance acumulado a la fecha `hasta`; el resultado aun no cerrado se muestra dentro del patrimonio."""
        cuentas = self._saldos_jerarquicos(bobj, None, hasta, ['activo', 'pasivo', 'patrimonio'])
        resultado = Decimal(str(self._rpt_resultados(bobj, None, hasta, q)['resumen']['resultado']))
        total = lambda tipo: sum((Decimal(str(c['saldo'])) for c in cuentas if c['tipo'] == tipo and c['nivel'] == 1), Decimal(0))
        filas = []
        for tipo, nombre in (('activo', 'TOTAL ACTIVO'), ('pasivo', 'TOTAL PASIVO'), ('patrimonio', 'TOTAL PATRIMONIO NETO')):
            for c in (c for c in cuentas if c['tipo'] == tipo):
                filas.append({'titulo': not c['imputable'], 'celdas': [c['codigo'], '    ' * (c['nivel'] - 1) + c['nombre'], c['saldo']]})
            if tipo == 'patrimonio':
                filas.append({'celdas': ['', '    Resultado del período (sin cerrar)', float(resultado)]})
            filas.append({'titulo': True, 'total': True, 'celdas': ['', nombre, float(total(tipo) + (resultado if tipo == 'patrimonio' else 0))]})
        filas.append({'titulo': True, 'total': True, 'celdas': ['', 'PASIVO + PATRIMONIO NETO', float(total('pasivo') + total('patrimonio') + resultado)]})
        return {'columnas': ['Código', 'Cuenta', 'Importe'], 'filas': filas}

    def generar_rg90(self, *args, **kwargs) -> dict:
        """TXT de RG90 del periodo (YYYY-MM): libro = 'ventas' | 'compras'."""
        q = kwargs.get('qdict', {})
        bobj = get_active_business(kwargs.get('userobj'))
        if not bobj or not RE_PERIODO.match(q.get('periodo') or ''):
            return {'error': 'Indique el período (mes y año)'}
        if q.get('libro') not in ('ventas', 'compras'):
            return {'error': 'Libro inválido'}
        return rg90.ventas(bobj, q.get('periodo')) if q.get('libro') == 'ventas' else rg90.compras(bobj, q.get('periodo'))

    def _excel(self, data) -> str:
        wb = Workbook()
        ws = wb.active
        ws.title = data['titulo'][:30]
        ws.append([data['negocio']])
        ws.append([f"{data['titulo']} — {data['periodo']}"])
        ws.append([])
        ws.append(data['columnas'])
        for cell in ws[4]:
            cell.font = Font(bold=True)
        for fila in data['filas']:
            ws.append(fila['celdas'])
            if fila.get('titulo'):
                for cell in ws[ws.max_row]:
                    cell.font = Font(bold=True)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or '')) for c in col) + 2))
        buffer = BytesIO()
        wb.save(buffer)
        nombre = default_storage.save(f"contabilidad/{data['titulo'].replace(' ', '_')}_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                                      ContentFile(buffer.getvalue()))
        return f'{settings.MEDIA_URL}{nombre}'
