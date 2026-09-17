import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

base = dict(pkg='mng_ecommerce', attr='MEcommerce')
TIENDA = dict(type='fk', fk_model='Tienda', qs=[{'field': 'activa', 'value': True}])
PEDIDO_BADGE = ("if (rowobj.anulado) return '<span class=\"badge bg-dark\">Anulado</span>';"
                " let c = {recibido: 'bg-warning text-dark', pagado: 'bg-info', preparado: 'bg-primary', despachado: 'bg-success'}[data] || 'bg-secondary';"
                " return `<span class=\"badge ${c}\">${data}</span>`;")

PRODUCTO_SEARCH = """
    form_search.se_select({
        surl: '{% url "iom" %}', dele: '#form_productotienda_{{ rr }} select[name=productoobj_id]', app_name: 'Sifen', model_name: 'Producto',
        field_display: ['prod_cod', 'descripcion'], field_id: ['id'], db_fields: ['id', 'prod_cod', 'descripcion'],
        sterm: ['or_descripcion__icontains', 'or_ean__icontains'], dejoin: ' - ', ml: 2, dbcon: 'default', theme: 'bootstrap-5', width: '100%',
        placeholder: 'Buscar en el maestro de productos...', headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')},
        dropdownParent: $('#offcanvasGlobalUi'), clean: false
    });
    {% if mobj %}
        $('#form_productotienda_{{ rr }} select[name=productoobj_id]').append(new Option('{{ mobj.productoobj.prod_cod }} - {{ mobj.productoobj.descripcion|escapejs }}', '{{ mobj.productoobj_id }}', true, true)).trigger('change');
    {% endif %}
"""

specs = [
    dict(base, key='tienda', model='Tienda', title='Tiendas', singular='Tienda', c_a='save_tienda', delete_extra={'model_name': 'Tienda'},
         search=['nombre', 'slug'],
         acc='<i title="Ver/Editar" class="tr-tienda-query text fs-5 mdi mdi-archive-eye-outline me-1"></i>'
             '<i title="Abrir la tienda pública" class="tr-tienda-abrir text fs-5 mdi mdi-open-in-new text-primary cursor-pointer"></i>',
         cols=[col('nombre', 'Tienda'), col('slug', 'Dirección (/tienda/...)'), col('temaobj__nombre', 'Tema'),
               col('costo_envio', 'Envío', 'float', 'align-right', MONEY), col('activa', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True),
                 dict(name='slug', label='Dirección pública (slug)', type='text', ph='se genera del nombre', help='La tienda queda en /tienda/&lt;slug&gt;/'),
                 dict(name='descripcion', label='Descripción corta', type='text', col=12),
                 dict(name='temaobj_id', label='Tema', type='fk', fk_model='TemaTienda'),
                 dict(name='activa', label='Activa', type='bool', col=3),
                 dict(name='sec_portada', label='Portada', type='section'),
                 dict(name='logo', label='Logo', type='file'), dict(name='banner', label='Imagen de portada', type='file'),
                 dict(name='banner_titulo', label='Título de portada', type='text'), dict(name='banner_texto', label='Texto de portada', type='text'),
                 dict(name='sec_contacto', label='Contacto', type='section'),
                 dict(name='email', label='Email', type='text'), dict(name='whatsapp', label='WhatsApp (con código de país)', type='text', ph='5959xxxxxxxx'),
                 dict(name='sec_envio', label='Envío y pago', type='section'),
                 dict(name='costo_envio', label='Costo de envío', type='number', default='0', col=4),
                 dict(name='envio_gratis_desde', label='Envío gratis desde', type='number', default='0', col=4, help='0 = nunca gratis'),
                 dict(name='acepta_contra_entrega', label='Pago contra entrega', type='bool', col=4),
                 dict(name='acepta_transferencia', label='Transferencia bancaria', type='bool', col=4),
                 dict(name='datos_transferencia', label='Datos para transferir (los ve el cliente)', type='textarea', rows=3, col=8,
                      ph='Banco, número de cuenta, titular, RUC')],
         extra_js="""
    $(`#${t_tienda} tbody`).on('click', '.tr-tienda-abrir', function() {
        let rowobj = $(`#${t_tienda}`).DataTable().row($(this).closest('tr')).data();
        window.open(`/tienda/${rowobj.slug}/`, '_blank', 'noopener');
    })
"""),
    dict(base, key='tematienda', model='TemaTienda', title='Temas de Tienda', singular='Tema', c_a='save_tema',
         delete_extra={'model_name': 'TemaTienda'}, search=['nombre'],
         cols=[col('nombre', 'Tema'), col('layout', 'Layout'),
               col('color_primario', 'Primario', render="return `<span style=\"display:inline-block;width:18px;height:18px;border-radius:4px;border:1px solid #ccc;background:${data}\"></span> ${data}`;"),
               col('color_acento', 'Acento', render="return `<span style=\"display:inline-block;width:18px;height:18px;border-radius:4px;border:1px solid #ccc;background:${data}\"></span> ${data}`;"),
               col('activo', 'Activo', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True),
                 dict(name='layout', label='Layout base', type='select', col=4,
                      options=[('clasico', 'Clásico'), ('minimal', 'Minimal')]),
                 dict(name='activo', label='Activo', type='bool', col=2),
                 dict(name='color_primario', label='Color primario (cabecera/pie)', type='color', default='#111827', col=3),
                 dict(name='color_acento', label='Color de acento (botones/enlaces)', type='color', default='#2563eb', col=3),
                 dict(name='color_fondo', label='Fondo', type='color', default='#ffffff', col=3),
                 dict(name='color_texto', label='Texto', type='color', default='#1f2937', col=3),
                 dict(name='fuente', label='Tipografía (font-family CSS)', type='text', col=12, ph='"Inter", sans-serif'),
                 dict(name='css_archivo', label='Archivo CSS propio', type='file', col=12,
                      help='Se carga después del CSS base: puede redefinir cualquier estilo (.tienda-header, .producto-card, .btn-tienda...).'),
                 dict(name='css_extra', label='CSS adicional (rápido)', type='textarea', rows=6, col=12, ph='.tienda-banner { padding: 9rem 1rem; }')]),
    dict(base, key='coleccion', model='Coleccion', title='Colecciones', singular='Colección', c_a='save_coleccion',
         delete_extra={'model_name': 'Coleccion'}, search=['nombre', 'tiendaobj__nombre'],
         cols=[col('tiendaobj__nombre', 'Tienda'), col('nombre', 'Colección'), col('slug', 'Slug'), col('orden', 'Orden', 'int', 'align-right'),
               col('activa', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(TIENDA, name='tiendaobj_id', label='Tienda', required=True),
                 dict(name='nombre', label='Nombre', type='text', required=True),
                 dict(name='descripcion', label='Descripción', type='text', col=12),
                 dict(name='imagen', label='Imagen', type='file'),
                 dict(name='orden', label='Orden', type='number', integer=True, default='0', col=3),
                 dict(name='activa', label='Activa', type='bool', col=3)]),
    dict(base, key='productotienda', model='ProductoTienda', title='Productos Publicados', singular='Publicación', c_a='save_productotienda',
         create_label='Publicar producto', delete_extra={'model_name': 'ProductoTienda'}, search=['titulo', 'productoobj__descripcion'],
         cols=[col('get_imagen', 'Foto', btyp='mdb', render="return data ? `<img src=\"${data}\" style=\"width:44px;height:44px;object-fit:cover;border-radius:4px;\">` : '';"),
               col('tiendaobj__nombre', 'Tienda'), col('titulo', 'Título'), col('coleccionobj__nombre', 'Colección'),
               col('get_precio', 'Precio', 'float', 'align-right', MONEY, btyp='mdb'),
               col('get_disponible', 'Disponible', 'float', 'align-right', MONEY, btyp='mdb'),
               col('destacado', 'Destacado', 'bool', 'align-center', BOOL), col('publicado', 'Publicado', 'bool', 'align-center', BOOL)],
         fields=[dict(TIENDA, name='tiendaobj_id', label='Tienda', required=True),
                 dict(name='productoobj_id', label='Producto del maestro', type='fk', app='Sifen', fk_model='Producto', required=True, no_populate=True),
                 dict(name='titulo', label='Título en la tienda', type='text', ph='Si queda vacío usa la descripción del producto', col=8),
                 dict(name='coleccionobj_id', label='Colección', type='fk', fk_model='Coleccion', display=['get_descripcion'], methods=['get_descripcion'],
                      qs=[{'field': 'activa', 'value': True}], col=4),
                 dict(name='precio_online', label='Precio online', type='number', default='0', col=4, help='0 = precio del maestro'),
                 dict(name='precio_comparacion', label='Precio tachado', type='number', default='0', col=4),
                 dict(name='orden', label='Orden', type='number', integer=True, default='0', col=4),
                 dict(name='destacado', label='Destacado en portada', type='bool', col=4), dict(name='publicado', label='Publicado', type='bool', col=4),
                 dict(name='descripcion_larga', label='Descripción', type='textarea', rows=6, col=12),
                 dict(name='imagen', label='Imagen principal', type='file', col=4), dict(name='imagen_2', label='Imagen 2', type='file', col=4),
                 dict(name='imagen_3', label='Imagen 3', type='file', col=4)],
         form_extra_js=PRODUCTO_SEARCH),
    dict(base, key='pedido', model='Pedido', title='Pedidos Online', workflow=True, workflow_states=('recibido', 'pagado', 'preparado', 'despachado'),
         create=False, edit=True, search=['cliente_nombre', 'cliente_email', 'cliente_telefono', 'pago_referencia'], order_col=1, order_dir='desc',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('get_tienda', 'Tienda', btyp='mdb'), col('cliente_nombre', 'Cliente'),
               col('cliente_telefono', 'Teléfono'), col('metodo_pago', 'Pago'), col('pago_referencia', 'Referencia'),
               col('total', 'Total', 'float', 'align-right', MONEY), col('documentheader_id', 'Factura', 'int'),
               col('estado', 'Estado', render=PEDIDO_BADGE)]),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Ecommerce', specs, os.path.join(BASE, 'Ecommerce', 'templates', 'Ecommerce'))
