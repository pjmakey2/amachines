# Documentación de Table UI (DataTables)

## Parámetros

    t_guid = Identificación de la tabla
    from_hub = Si la petición viene de una app móvil hub
    url_exec = El endpoint único siempre '{% url "iom" %}', pero damos al usuario la posibilidad de cambiar para personalización.
    title = Título de la tabla
    tselector = Id del div donde se dibujará/renderizará la tabla,
    app_name = El app_name del modelo,
    model_name = El modelo que se renderizará,
    ###INICIO Si el usuario quiere llamar un método personalizado en el backend.
    custom_module = Módulo personalizado
    custom_package = Paquete personalizado
    custom_attr = Attr personalizado (el nombre de la clase)
    custom_mname = Método personalizado
    ###FIN Si el usuario quiere llamar un método personalizado en el backend.
    mquery = Los parámetros a pasar para el método filter del queryset
              En el formato de [{'field': 'name__icontains', value: 'test'} ]
              Si always_query es true, esto se llama en cada petición y se adjunta automáticamente a la búsqueda del usuario

    detail_objs = Si el modelo es un header y tiene referencias en otros modelos, con esto pueden ser sus hijos,
    dbcon = Qué conexiones definidas usaremos
    timer_message = 5000,
    columns = Esta es la definición del orden y qué columnas (campos del modelo) mostrar
              Y si hay un campo, método o uno renderizado manualmente.
              Ejemplo:
                [
               { fdis: true, gre: false, btyp: 'loc', idx: null, tit: 'ACC',  dtyp: 'str', dfl: '', nord: false,
                dfcon: `
                    <i title="Ver ficha" class="tr-embarques-query fs-extra-lg  text text-info mdi mdi-archive-eye-outline"></i>
                `,
               }, //Definición manual de una columna
               { fdis: true,
                gre: true,
                btyp: 'fdb',  //Esto le dice al backend que es un campo
                idx: 'codoficina__nomoficina',  //Referenciamos una clave foránea aquí
                tit: 'Oficina',
                cls: 'align-left',
                dtyp: 'str',
                hide: false
              },
              { fdis: true,
                gre: true,
                btyp: 'mdb', //Esto le dice al backend que es un callable (método)
                idx: 'get_embarques', //el nombre del método dentro del modelo definido en model_name
                tit: 'Codigo',
                cls: 'align-left',
                dtyp: 'str',
                hide: false
              },
              ...
    t_fsize = Tamaño de fuente de la tabla,
    table_width = Espacio de ancho,
    cls_table = clases personalizadas para <table> si el usuario quiere definir,
    cls_thead = clases personalizadas para <thead> si el usuario quiere definir,,
    plength = cuántos registros renderizará por página,
    t_opts = {
         //Opciones a pasar directamente al método de inicialización de parámetros de datatable.
         //Si un parámetro que tiene un valor por defecto se pone aquí, lo que está aquí sobrescribirá el valor por defecto

    },
    always_initquery = true //Si en cada petición enviaría los filtros mquery,
    check_gmquery = //Si usaría la variable nombre gmquery en el .html donde se usa esta librería,
    builder_be = //Método de búsqueda personalizado (definido en el .html donde se implementa esta lib) usado en lugar del método interno de la librería datatables_cfilter,


//Ejemplo de definición

dt_ofh_pc = Grid.datatables_wrapper({
          t_guid: t_ofh,
          url_exec: '{% url "iom" %}',
          title: '',
          tselector: 'table_container_DocumentHeader',
          app_name: 'Sifen',
          model_name: 'DocumentHeader',
          cls_table: 'cell-border row-border table table-sm',
          cls_thead: 'border-gray-900',
          dbcon: 'default',
          mquery: [],
          always_initquery: false,
          plength: 300,
          t_opts: {
              select: {
                style: 'os'
              },
              dom: 'it',
              fixedHeader: false,
              responsive: null,
              scrollCollapse: true,
              scrollX: true,
              scrollY: 600,
              paging: true,
              order: [[1, 'desc']],
              createdRow: function( row, data, dataIndex) {
                if (data.ek_estado === 'Aprobado') {
                  row.style.backgroundColor = '#8EF07A';
                }
                if (data.ek_estado === 'Rechazado') {
                    row.style.backgroundColor = '#FF9900FF';
                }
                if (data.ek_estado === 'Inutilizado') {
                    row.style.backgroundColor = '#E99A238A';
                }

                if (data.doc_tipo == "FE") {
                  if (data.doc_saldo !== 0) {
                    row.style.backgroundColor = '#FCFF648A';
                  }
                  if (data.doc_cre_tipo_cod === 2) {
                    today = moment();
                    vto = moment(data.doc_vencimiento);
                    dd = vto.diff(today, 'days')
                    if ((dd <= -30) || (dd === 0)) {
                      row.style.backgroundColor = '#F709FFB2';
                    }
                  }
                }
                if ((data.anulado_tipo === 'NC') || (data.anulado_tipo === 'SIFEN')) {
                  row.style.backgroundColor = '#FF00008A';
                }

              },
              rowId: function(row, se) {
                  return `tr_tclh_${row.id}`
              }
          },
          builder_be: documentheader_home_be,
          columns: [
              { fdis: true,
                gre: true,
                btyp: 'mdb',
                idx: 'get_total_venta_gs',
                tit: 'Total',
                cls: 'align-left',
                dtyp: 'str',
                hide: false,
                render: (data, dtype, rowobj)=>{
                  if (rowobj.moneda === 'USD') {
                    return `<span>$ </span>${UiN.formatNumberU(data.toFixed(2))}`;
                  }
                  return `<span>Gs </span>${UiN.formatNumberU(data.toFixed(0))}`;
                }
              },
              { fdis: true,
                gre: true,
                btyp: 'fdb',
                idx: 'doc_saldo',
                tit: 'Saldo',
                cls: 'align-left',
                dtyp: 'str',
                hide: false,
                render: (data, dtype, rowobj)=> {
                  if (rowobj.moneda === 'USD') {
                    return `<span>$ </span>${UiN.formatNumberU(data.toFixed(2))}`;
                  }
                  return `<span>Gs </span>${UiN.formatNumberU(data.toFixed(0))}`;
                }
              },
              { fdis: true,
                gre: true,
                btyp: 'fdb',
                idx: 'doc_cre_tipo_cod',
                tit: 'Forma Pago Codigo',
                cls: 'align-left',
                dtyp: 'int',
                hide: true,
              },

          ]
      })
