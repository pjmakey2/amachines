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
                 dict(name='banner_cta_texto', label='Botón de portada (texto)', type='text', col=4, ph='Ver ofertas'),
                 dict(name='banner_cta_url', label='Botón de portada (destino)', type='text', col=8, ph='/tienda/mi-tienda/coleccion/ofertas/'),
                 dict(name='anuncio_texto', label='Barra de anuncio', type='text', col=8, ph='Envío gratis desde Gs 300.000'),
                 dict(name='anuncio_url', label='Enlace del anuncio', type='text', col=4),
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
         acc='<i title="Ver/Editar" class="tr-tematienda-query text fs-5 mdi mdi-archive-eye-outline me-1"></i>'
             '<i title="Vista previa en la tienda" class="tr-tematienda-preview text fs-5 mdi mdi-eye-outline text-primary cursor-pointer"></i>',
         toolbar_extra="""            <button id="btn_presets_tematienda" class="btn btn-outline-primary"><i class="mdi mdi-palette-swatch-outline"></i> Ver estilos disponibles</button>\n""",
         cols=[col('nombre', 'Tema'), col('get_preset_nombre', 'Estilo base', btyp='mdb'),
               col('colores_propios', 'Colores propios', 'bool', 'align-center', BOOL),
               col('color_acento', 'Acento', render="return rowobj.colores_propios ? `<span style=\"display:inline-block;width:18px;height:18px;border-radius:4px;border:1px solid #ccc;background:${data}\"></span> ${data}` : '<span class=\"text-muted\">del estilo</span>';"),
               col('activo', 'Activo', 'bool', 'align-center', BOOL), col('preset', 'preset', hide=True)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True, col=8),
                 dict(name='activo', label='Activo', type='bool', col=4),
                 dict(name='preset', label='Estilo base', type='select', col=12,
                      options=[('clasico', 'Clásico — General'), ('minimal', 'Minimal — Moda / diseño'), ('bazaar', 'Bazaar — Electrónica / marketplace'),
                               ('fresco', 'Fresco — Almacén / alimentos'), ('hogar', 'Hogar — Muebles / decoración')],
                      help='Cada estilo trae su CSS, colores, tipografía y estructura (sidebar de categorías, tipo de portada).'),
                 dict(name='sec_colores', label='Colores', type='section'),
                 dict(name='colores_propios', label='Usar colores propios (si no, los del estilo)', type='bool', col=12),
                 dict(name='color_primario', label='Primario (cabecera/pie)', type='color', default='#111827', col=3),
                 dict(name='color_acento', label='Acento (botones/badges)', type='color', default='#2563eb', col=3),
                 dict(name='color_fondo', label='Fondo', type='color', default='#ffffff', col=3),
                 dict(name='color_texto', label='Texto', type='color', default='#1f2937', col=3),
                 dict(name='fuente', label='Tipografía (font-family CSS)', type='text', col=12, ph='"Inter", sans-serif'),
                 dict(name='sec_css', label='CSS propio', type='section'),
                 dict(name='css_archivo', label='Archivo CSS propio', type='file', col=12,
                      help='Se carga después del estilo base: puede redefinir cualquier clase (.tienda-header, .producto-card, .hero-principal, .btn-tienda...).'),
                 dict(name='css_extra', label='CSS adicional (rápido)', type='textarea', rows=6, col=12, ph='.hero-principal { min-height: 480px; }')],
         form_extra_js="""
    tematienda_toggle_colores = () => {
        let propios = qelem('#form_tematienda_{{ rr }} select[name=colores_propios]').value === 'true';
        ['color_primario', 'color_acento', 'color_fondo', 'color_texto', 'fuente'].forEach((n) => {
            let el = qelem(`#form_tematienda_{{ rr }} [data-field=${n}]`);
            if (el) el.hidden = !propios;
        });
    }
    qelem('#form_tematienda_{{ rr }} select[name=colores_propios]').addEventListener('change', tematienda_toggle_colores);
    tematienda_toggle_colores();
""",
         extra_js="""
    tematienda_post = (mname) => {
        let gbe = new FormData();
        gbe.append('module', 'Ecommerce');
        gbe.append('package', 'mng_ecommerce');
        gbe.append('attr', 'MEcommerce');
        gbe.append('mname', mname);
        gbe.append('dbcon', 'default');
        return axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => rsp.data);
    }
    // Galeria de estilos base: muestra colores y estructura, y abre la tienda con ?preset= para verlo aplicado
    qelem('#btn_presets_tematienda').addEventListener('click', () => {
        tematienda_post('get_presets').then((d) => {
            let esc = (v) => $('<span>').text(v == null ? '' : v).html();
            let sw = (c) => `<span style="display:inline-block;width:16px;height:16px;border-radius:4px;border:1px solid #ccc;background:${c}"></span>`;
            let cards = d.presets.map((p) => `
                <div class="col-md-6"><div class="card h-100"><div class="card-body">
                    <div class="d-flex justify-content-between align-items-start"><div><h6 class="mb-0">${esc(p.nombre)}</h6><small class="text-muted">${esc(p.rubro)}</small></div>
                    ${d.tienda_url ? `<a class="btn btn-sm btn-outline-primary" target="_blank" rel="noopener" href="${d.tienda_url}?preset=${p.clave}"><i class="mdi mdi-eye-outline"></i> Ver</a>` : ''}</div>
                    <p class="small mt-2 mb-2">${esc(p.descripcion)}</p>
                    <div class="small">${sw(p.colores.primario)} ${sw(p.colores.acento)} ${sw(p.colores.fondo)} ${sw(p.colores.texto)}
                    &nbsp; <span class="badge bg-secondary">${p.sidebar ? 'con sidebar' : 'sin sidebar'}</span> <span class="badge bg-secondary">portada ${esc(p.hero)}</span></div>
                </div></div></div>`).join('');
            $('#offcanvasGlobalUiLabel').html('Estilos base de tienda');
            $('#offcanvasGlobalUiBody').html(`<p class="text-muted small">${d.tienda_url ? 'La vista previa abre tu tienda con ese estilo sin cambiar nada; solo vos lo ves mientras estés logueado.' : 'Creá una tienda activa para poder previsualizar.'}</p><div class="row g-3">${cards}</div>`);
            new bootstrap.Offcanvas('#offcanvasGlobalUi').show();
        });
    });
    $(`#${t_tematienda} tbody`).on('click', '.tr-tematienda-preview', function() {
        let rowobj = $(`#${t_tematienda}`).DataTable().row($(this).closest('tr')).data();
        tematienda_post('get_presets').then((d) => {
            if (!d.tienda_url) { UiB.MsgInfo('Creá una tienda activa para previsualizar.'); return; }
            window.open(`${d.tienda_url}?preset=${rowobj.preset}`, '_blank', 'noopener');
        });
    })
"""),
    dict(base, key='promotienda', model='PromoTienda', title='Promociones de Portada', singular='Promoción', c_a='save_promo',
         delete_extra={'model_name': 'PromoTienda'}, search=['titulo', 'subtitulo', 'tiendaobj__nombre'],
         cols=[col('tiendaobj__nombre', 'Tienda'), col('posicion', 'Posición'), col('etiqueta', 'Etiqueta'), col('titulo', 'Título'), col('subtitulo', 'Subtítulo'),
               col('orden', 'Orden', 'int', 'align-right'), col('activa', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(TIENDA, name='tiendaobj_id', label='Tienda', required=True, col=8),
                 dict(name='posicion', label='Posición', type='select', col=4,
                      options=[('lateral', 'Tarjeta lateral de la portada'), ('carrusel', 'Carrusel de promociones')],
                      help='Lateral: estilos Bazaar y Hogar (hasta 2). Carrusel: estilo Fresco (hasta 8).'),
                 dict(name='etiqueta', label='Etiqueta (texto chico)', type='text', col=4, ph='Novedades'),
                 dict(name='titulo', label='Título', type='text', required=True, col=8, ph='Zapatillas de invierno'),
                 dict(name='subtitulo', label='Subtítulo / oferta', type='text', col=6, ph='20% OFF'),
                 dict(name='url', label='Destino al hacer clic', type='text', col=6, ph='/tienda/mi-tienda/coleccion/zapatillas/'),
                 dict(name='imagen', label='Imagen (fondo transparente queda mejor)', type='file', col=6),
                 dict(name='color_fondo', label='Color de fondo (opcional)', type='text', col=3, ph='#fce7f3'),
                 dict(name='orden', label='Orden', type='number', integer=True, default='0', col=3),
                 dict(name='activa', label='Activa', type='bool', col=3)]),
    dict(base, key='coleccion', model='Coleccion', title='Colecciones', singular='Colección', c_a='save_coleccion',
         delete_extra={'model_name': 'Coleccion'}, search=['nombre', 'tiendaobj__nombre'],
         cols=[col('tiendaobj__nombre', 'Tienda'), col('nombre', 'Colección'), col('slug', 'Slug'), col('orden', 'Orden', 'int', 'align-right'),
               col('activa', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(TIENDA, name='tiendaobj_id', label='Tienda', required=True),
                 dict(name='nombre', label='Nombre', type='text', required=True),
                 dict(name='descripcion', label='Descripción', type='text', col=12),
                 dict(name='imagen', label='Imagen', type='file'),
                 dict(name='icono', label='Ícono del menú lateral (Bootstrap Icons)', type='text', col=6, ph='bi-basket', help='Nombre de un ícono de icons.getbootstrap.com'),
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
                 dict(name='etiqueta', label='Badge sobre la foto', type='text', col=4, ph='Nuevo / Más vendido', help='Si hay precio tachado se muestra el % OFF en su lugar.'),
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
