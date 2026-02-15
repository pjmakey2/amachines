from datetime import datetime
from django.conf import settings
import pandas as pd
from Sifen.models import Geografias, AreasPoliticas, Paises, Departamentos, ActividadEconomica, Business, Etimbrado, TipoContribuyente, Ciudades, Medida

def create_business():
    bs_name = 'TU EMPRESA'
    Business.objects.create(
        name = bs_name,
        abbr = 'TU ABREVIATURA',
        ruc = 'TU RUC',
        ruc_dv = 'TU DV',
        contribuyenteobj = TipoContribuyente.objects.get(codigo = 2,tipo = 'Juridica'),
        nombrefactura = bs_name,
        nombrefantasia = bs_name,
        numero_casa = 3985,
        direccion = 'Algun lugar',
        dir_comp_uno = 'Algun lugar',
        dir_comp_dos = 'Algun lugar',
        ciudadobj = Ciudades.objects.get(codigo_ciudad=1),
        telefono = '000000',
        celular = '000000',
        correo = 'info@tuempresa.com',
        denominacion = 'S.A.',
        actividadecoobj = ActividadEconomica.objects.get(codigo_actividad='52299'),
        cargado_fecha = datetime.now(),
        cargado_usuario = 'AUTOMATIC',
        actualizado_fecha = datetime.now(),
        actualizado_usuario = 'AUTOMATIC',
        aprobado_fecha = datetime.now(),
        aprobado_usuario = 'AUTOMATIC'
    )

def load_medidas():
    medidas = [
        (87, 'm', 'Metros'),
        (2366, 'CPM', 'Costo por Mil'),
        (2329, 'UI', 'Unidad Internacional'),
        (110, 'M3', 'Metros cúbicos'),
        (77, 'UNI', 'Unidad'),
        (86, 'g', 'Gramos'),
        (89, 'LT', 'Litros'),
        (90, 'MG', 'Miligramos'),
        (91, 'CM', 'Centimetros'),
        (92, 'CM2', 'Centimetros cuadrados'),
        (93, 'CM3', 'Centimetros cubicos'),
        (94, 'PUL', 'Pulgadas'),
        (96, 'MM2', 'Milímetros cuadrados'),
        (79, 'kg/m²', 'Kilogramos s/ metrocuadrado'),
        (97, 'AA', 'Año'),
        (98, 'ME', 'Mes'),
        (99, 'TN', 'Tonelada'),
        (100, 'Hs', 'Hora'),
        (101, 'Mi', 'Minuto'),
        (104, 'DET', 'Determinación'),
        (103, 'Ya', 'Yardas'),
        (108, 'MT', 'Metros'),
        (109, 'M2', 'Metros cuadrados'),
        (95, 'MM', 'Milímetros'),
        (666, 'Se', 'Segundo'),
        (102, 'Di', 'Día'),
        (83, 'kg', 'Kilogramos'),
        (88, 'ML', 'Mililitros'),
        (625, 'Km', 'Kilómetros'),
        (660, 'ml', 'Metro lineal'),
        (885, 'GL', 'Unidad Medida Global'),
        (891, 'pm', 'Por Milaje'),
        (869, 'ha', 'Hectáreas'),
        (569, 'ración', 'Ración'),
    ]
    for m in medidas:
        cobj, cre  = Medida.objects.get_or_create(
            medida_cod=m[0],
            medida=m[1],
            medida_descripcion=m[2]
        )
        if cre:
            cobj.cargado_usuario = 'AUTOMATICO'
            cobj.cargado_fecha = datetime.now()
            cobj.save()    

def load_actividades():
    df = pd.read_csv(f'{settings.BASE_DIR}/Sifen/rf/actividades_economicas_utf8.csv', sep=',', encoding='utf-8', quotechar='"')
    for idx, data in df.iterrows():
        aobj, cre = ActividadEconomica.objects.get_or_create(
            codigo_actividad = data.codigo,
            nombre_actividad = data.descripcion,
        )
        if cre:
            aobj.cargado_fecha = datetime.now()
            aobj.cargado_usuario = 'AU'
            aobj.save()

def load_geografias():
    gobj, cr = Geografias.objects.get_or_create(
        continente = 'America',
        descripcion = 'America',
        comentarios = ''
    )

    areobj, cr  = AreasPoliticas.objects.get_or_create(
        geografia = gobj,
        area_politica = 'SUDAMERICA',
        descripcion = '',
        comentarios = '',
    )

    paisobj, cr = Paises.objects.get_or_create(
        nombre_pais = 'PARAGUAY',
        codigo_pais = 600,
        alfa_uno = 'PY',
        alfa_dos = 'PRY',
        areapolitica = areobj,
        adjetivo = 'PARAGUAYO',
        nacionalidad = 'PARAGUAYA',
        habitante = 'PARAGUAYOS',
        descripcion = 'ND',
        comentarios = 'ND'
    )
    ff = 'SET'
    dfg = pd.read_excel(f'{settings.BASE_DIR}/Sifen/rf/CODIGO DE REFERENCIA GEOGRAFICA.xlsx')
    dfg.fillna('', inplace=True)
    for idx, data in dfg.iterrows():
        dobj, cr = Departamentos.objects.get_or_create(
                fuente = ff,
                pais = paisobj,
                codigo_departamento = data.DEP_COD,
                nombre_departamento = data.DEP,
                habitante = 'ND',
                descripcion = 'ND',
                comentarios = 'ND'
            )
        disobj, cr = dobj.distrito_set.get_or_create(
            fuente = ff,
            codigo_distrito = data.DIS_COD,
            nombre_distrito = data.DIS,
            habitante = 'ND',
            descripcion = 'ND',
            comentarios = 'ND'
        )
        if str(data.CIU_COD).strip() == '': continue
        ciuobj, cr = disobj.ciudades_set.get_or_create(
            fuente = ff,
            codigo_ciudad = data.CIU_COD,
            nombre_ciudad = data.CIU,
            habitante = 'ND',
            descripcion = 'ND',
            comentarios = 'ND'
        )
        if str(data.BAR_COD).strip() == '': continue
        ciuobj.barrios_set.get_or_create(
            fuente = ff,
            codigo_barrio = data.BAR_COD,
            nombre_barrio = data.BAR,
            habitante = 'ND',
            descripcion = 'ND',
            comentarios = 'ND'
        )

def set_tipo_contribuyente():
    TipoContribuyente.objects.get_or_create(
        codigo = 2,
        tipo = 'Juridica'
    )

    TipoContribuyente.objects.get_or_create(
        codigo = 1,
        tipo = 'Fisica'
    )
