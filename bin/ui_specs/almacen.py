import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gen_plugin_ui import *

base = dict(pkg='mng_almacen', attr='MAlmacen')
QTY = "return UiN.formatNumberU(parseFloat(data || 0).toFixed(2));"
UBI = dict(type='fk', fk_model='Ubicacion', display=['get_descripcion'], methods=['get_descripcion'])

PRODUCTO_SEARCH_JS = """
    form_search.se_select({
        surl: '{% url "iom" %}', dele: '#form_ajustestock_{{ rr }} select[name=productoobj_id]', app_name: 'Sifen', model_name: 'Producto',
        field_display: ['prod_cod', 'descripcion'], field_id: ['id'], db_fields: ['id', 'prod_cod', 'descripcion'],
        sterm: ['or_descripcion__icontains', 'or_ean__icontains'], dejoin: ' - ', ml: 2, dbcon: 'default', theme: 'bootstrap-5', width: '100%',
        placeholder: 'Buscar producto...', headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')}, dropdownParent: $('#offcanvasGlobalUi')
    });
"""

TRASLADO_JS = """
    // Almacenaje: mover stock de esta ubicacion a otra
    $(`#${t_stockubicacion} tbody`).on('click', '.tr-stock-trasladar', function() {
        let rowobj = $(`#${t_stockubicacion}`).DataTable().row($(this).closest('tr')).data();
        let gbe = new FormData();
        gbe.append('module', 'Almacen');
        gbe.append('package', 'mng_almacen');
        gbe.append('attr', 'MAlmacen');
        gbe.append('mname', 'get_ubicaciones');
        gbe.append('dbcon', 'default');
        axios.post('{% url "iom" %}', gbe, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((rsp) => {
            let opciones = (rsp.data.ubicaciones || []).filter((u) => u.id !== rowobj.ubicacionobj_id)
                .map((u) => `<option value="${u.id}">${$('<span>').text(u.text).html()}</option>`).join('');
            Swal.fire({
                title: 'Trasladar / almacenar',
                html: `<div class="text-start"><p class="mb-2"><b>${$('<span>').text(rowobj.productoobj__descripcion).html()}</b><br>
                       Desde ${$('<span>').text(rowobj.get_ubicacion).html()} — hay ${parseFloat(rowobj.cantidad)}</p>
                       <label>Destino</label><select id="swal_traslado_destino" class="form-select mb-2">${opciones}</select>
                       <label>Cantidad</label><input id="swal_traslado_cantidad" type="text" class="form-control text-end" value="${parseFloat(rowobj.cantidad)}"></div>`,
                showCancelButton: true, confirmButtonText: 'Trasladar', cancelButtonText: 'Cancelar',
                preConfirm: () => ({ destino_id: qelem('#swal_traslado_destino').value, cantidad: qelem('#swal_traslado_cantidad').value.replace(',', '.') })
            }).then((result) => {
                if (!result.isConfirmed) return;
                let g2 = new FormData();
                g2.append('module', 'Almacen');
                g2.append('package', 'mng_almacen');
                g2.append('attr', 'MAlmacen');
                g2.append('mname', 'trasladar');
                g2.append('dbcon', 'default');
                g2.append('producto_id', rowobj.productoobj_id);
                g2.append('origen_id', rowobj.ubicacionobj_id);
                g2.append('destino_id', result.value.destino_id);
                g2.append('cantidad', result.value.cantidad);
                axios.post('{% url "iom" %}', g2, { headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')} }).then((r2) => {
                    if (r2.data.error) UiB.MsgError(r2.data.error); else UiB.MsgSuccess(r2.data.success);
                    $(`#${t_stockubicacion}`).DataTable().ajax.reload(null, false);
                });
            });
        });
    })
"""

specs = [
    dict(base, key='bodega', model='Bodega', title='Bodegas', singular='Bodega', delete_extra={'model_name': 'Bodega'},
         search=['nombre', 'direccion'],
         cols=[col('nombre', 'Nombre'), col('direccion', 'Dirección'), col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='nombre', label='Nombre', type='text', required=True, col=8), dict(name='activo', label='Activa', type='bool', col=4),
                 dict(name='direccion', label='Dirección', type='text', col=12)]),
    dict(base, key='ubicacion', model='Ubicacion', title='Ubicaciones', singular='Ubicación', delete_extra={'model_name': 'Ubicacion'},
         search=['codigo', 'descripcion', 'bodegaobj__nombre'],
         cols=[col('bodegaobj__nombre', 'Bodega'), col('codigo', 'Código'), col('tipo', 'Tipo'), col('descripcion', 'Descripción'),
               col('activo', 'Activa', 'bool', 'align-center', BOOL)],
         fields=[dict(name='bodegaobj_id', label='Bodega', type='fk', fk_model='Bodega', required=True),
                 dict(name='codigo', label='Código', type='text', required=True, ph='A-01-03', help='Pasillo-estante-nivel, o el nombre del muelle.'),
                 dict(name='tipo', label='Tipo', type='select', col=6,
                      options=[('recepcion', 'Recepción (muelle)'), ('almacenaje', 'Almacenaje'), ('picking', 'Picking'), ('averiados', 'Averiados / no vendible')]),
                 dict(name='activo', label='Activa', type='bool', col=6),
                 dict(name='descripcion', label='Descripción', type='text', col=12)]),
    dict(base, key='recepcion', model='Recepcion', title='Recepción de Mercadería', singular='Recepción', workflow=True,
         create_label='Nueva recepción', search=['proveedor', 'documento_ref', 'orden_compra_ref'], order_col=1, order_dir='desc',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('bodegaobj__nombre', 'Bodega'), col('proveedor', 'Proveedor'),
               col('documento_ref', 'Remisión / Factura'), col('orden_compra_ref', 'OC'), col('estado', 'Estado', render=ESTADO_BADGE)]),
    dict(base, key='stockubicacion', model='StockUbicacion', title='Stock por Ubicación', create=False, delete=False,
         acc='<i title="Trasladar / almacenar" class="tr-stock-trasladar text fs-5 mdi mdi-transfer text-primary cursor-pointer"></i>',
         search=['productoobj__descripcion', 'ubicacionobj__codigo'], mquery=[{'field': 'cantidad__gt', 'value': 0}], order_col=1,
         cols=[col('productoobj__prod_cod', 'Código', 'int'), col('productoobj__descripcion', 'Producto'),
               col('get_ubicacion', 'Ubicación', btyp='mdb'), col('ubicacionobj__tipo', 'Tipo'),
               col('cantidad', 'Cantidad', 'float', 'align-right', QTY),
               col('productoobj_id', 'pid', 'int', hide=True), col('ubicacionobj_id', 'uid', 'int', hide=True)],
         extra_js=TRASLADO_JS),
    dict(base, key='movimientostock', model='MovimientoStock', title='Movimientos de Stock', create=False, delete=False, acc='',
         search=['productoobj__descripcion', 'concepto'], order_col=1, order_dir='desc',
         cols=[col('fecha', 'Fecha', 'date'), col('productoobj__descripcion', 'Producto'), col('get_ubicacion', 'Ubicación', btyp='mdb'),
               col('tipo', 'Tipo'), col('cantidad', 'Cantidad', 'float', 'align-right', QTY), col('saldo', 'Saldo ubic.', 'float', 'align-right', QTY),
               col('concepto', 'Concepto'), col('cargado_usuario', 'Usuario')]),
    dict(base, key='ajustestock', model='AjusteStock', title='Ajustes de Inventario', singular='Conteo', workflow=True, c_a='create_ajuste',
         create_label='Nuevo conteo', create_title='Cargar conteo físico', editable=False, search=['motivo', 'productoobj__descripcion'],
         order_col=1, order_dir='desc',
         acc='',
         cols=[col('numero', 'Nro.', 'int'), col('fecha', 'Fecha', 'date'), col('get_producto', 'Producto', btyp='mdb'),
               col('get_ubicacion', 'Ubicación', btyp='mdb'), col('cantidad_sistema', 'Sistema', 'float', 'align-right', QTY),
               col('cantidad_contada', 'Contado', 'float', 'align-right', QTY), col('motivo', 'Motivo'),
               col('estado', 'Estado', render=ESTADO_BADGE)],
         fields=[dict(name='fecha', label='Fecha', type='date', today=True, col=4),
                 dict(name='productoobj_id', label='Producto', type='fk', app='Sifen', fk_model='Producto', required=True, col=8, no_populate=True),
                 dict(UBI, name='ubicacionobj_id', label='Ubicación', required=True, col=8),
                 dict(name='cantidad_contada', label='Cantidad contada', type='number', required=True, col=4),
                 dict(name='motivo', label='Motivo', type='text', required=True, col=12)],
         form_extra_js=PRODUCTO_SEARCH_JS),
]
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
generate('Almacen', specs, os.path.join(BASE, 'Almacen', 'templates', 'Almacen'))
