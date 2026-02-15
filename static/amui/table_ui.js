Grid = {
    datatables_wrapper: ({
        t_guid = undefined,
        from_hub = false,
        url_exec, 
        title,
        tselector,
        app_name,
        model_name,
        custom_module = undefined,
        custom_package = undefined,
        custom_attr = undefined,
        custom_mname = undefined,
        mquery = [],
        detail_objs = {},
        dbcon = 'default',
        columns,
        t_fsize = '14px',
        table_width = '100%',
        cls_table = 'display cell-border row-border table',
        cls_thead = 'table-light',
        plength = 100,
        t_opts = {},
        always_initquery = true,
        check_gmquery = false,
        builder_be = undefined,
    }) => {
        let default_opts = {
            dom: 'tp',
            fixedHeader: true,
            responsive: { details: {type: 'column'} },
            select: {
                style: 'single'
            },
            scrollCollapse: true,
            // scrollX: true,
            // scroller: true,
            scrollY: 700,
            searchDelay: 500,
            pageLength: plength,
            language: {
                paginate: {
                    previous: ' <i class=" ri-arrow-left-fill"></i> ',
                    next: ' <i class=" ri-arrow-right-fill"></i> '
                },
                info: '_START_ a _END_ de _TOTAL_',
            },
            processing: true,
            serverSide: true,
            order: [[0, 'desc']],
            ajax: {
                url: url_exec,
                type: 'POST',
                headers: {
                    'X-CSRFToken': OptsIO.getCookie('csrftoken')
                },
            },
        }
        //Create the ID for the html table
        if (t_guid === undefined) {
            t_guid =  `dtable_${OptsIO.s4generate()}`;
        }
        
        //Variables to hold the sending parameters of fields and methods of the model
        let fields = [];
        let methods = [];
        //Extend default options
        default_opts = Object.assign(default_opts, t_opts);
        //Create the HTML string for the html table
        filter_options = [
            '<option value="contain"> Continene </option>',
            '<option value="notcontain"> No contiene </option>',
            '<option value="equal"> Igual a </option>',
            '<option value="notequal"> No igual a </option>',
            '<option value="beginwith"> Empieza con </option>',
            '<option value="endwith"> Termina con </option>',
            '<option value="greaterthan"> Mayor a </option>',
            '<option value="lessthan"> Menor a </option>',
        ];        
        filter_cols = [];
        //<table id="${t_guid}" class="" style="width: 100%; font-size: ${t_fsize}">`,
        t_title = `<h4>${title}</h4>`;
        if (from_hub) { t_title = ``; }
        let datatable_html = [
            `${t_title}
            <div id="${t_guid}_info_dt"></div>
            <table id="${t_guid}" class="${cls_table}" style="width: ${table_width}; font-size: ${t_fsize};">`,
            
            `<thead class="${cls_thead}">`,
            `<tr>`,
        ];
        //Create the thead of the HTML table
        //Create the data to send to the BE
        //Create the column option for Datatables
        copt = [];
        columns.forEach((ii)=>{
            if (ii.fdis) {
                datatable_html.push(
                    `<th>${ii.tit}</th>`
                )
                ctmp = {
                    data: ii.idx ? ii.idx: null,
                    name: ii.name ? ii.name: null,
                    className: ii.cls ? ii.cls: '',
                    defaultContent: ii.dfcon ? ii.dfcon: '',
                    orderable: ii.nord ? false: true,
                    createdCell: ii.cce ? ii.cce: null, 
                    render: ii.render ? ii.render: null,
                    searchable: ii.nsear ? false: true,
                    visible: ii.hide ? false: true,
                }
                if(ii.width) {
                    ctmp['width'] = ii.width;
                } 
                copt.push(ctmp);
            }
            if (ii.gre) {
                if (ii.btyp === 'fdb') {
                    fields.push(ii.idx);
                    filter_cols.push(`<option value="${ii.idx}">${ii.tit}</option>`);
                }
                if (ii.btyp === 'mdb') {
                    methods.push(ii.idx);
                }
            }
            
        })
        default_opts.columns = copt;
        initquery = {
            module: 'OptsIO',
            package: 'io_grid',
            attr: 'IoG',
            mname: 'get_records',
            model_app_name:  app_name,
            model_name: model_name,
            methods: jfy(methods),
            fields: jfy(fields),
            dbcon: dbcon,
            mquery: jfy(mquery),
            format: 'datatables',
            always_initquery: always_initquery,
            detail_objs: jfy(detail_objs),
            check_gmquery: check_gmquery
        }
        if (( custom_module !== undefined) &&
            ( custom_package !== undefined ) &&
            ( custom_attr !== undefined ) &&
            ( custom_mname !== undefined )) {
                initquery.custom_module = custom_module
                initquery.custom_package = custom_package
                initquery.custom_attr = custom_attr
                initquery.custom_mname = custom_mname
        }
        default_opts.ajax.initquery = initquery
        default_opts.ajax.t_guid = t_guid;
        if (builder_be !== undefined) {
            default_opts.ajax.data = builder_be
        } else {
            default_opts.ajax.data = Grid.datatables_cfilter
        }
        
        datatable_html.push(`</tr></thead><tbody></tbody></table><div id="${t_guid}_info_dt_bottom"></div>`);
        qelem(`#${tselector}`).innerHTML += datatable_html.join('');
        //Initialize and Create the datatable object
        let dt =  $(`#${t_guid}`).DataTable(default_opts);
        console.log('Call datatables');
        return dt
    },
    datatables_cfilter: function (data, settings) {
        crdata = Object.assign({}, settings.ajax.initquery);
        mquery = [];
        if (crdata.always_initquery === true) {
            mquery = jpar(crdata.mquery);
        }
        t_guid = settings.ajax.t_guid;
        fse = `.${t_guid}-filter-column`;
        fva = `.${t_guid}-filter-value`;
        fop = `.${t_guid}-filter-operator`;
        fun = `.${t_guid}-filter-union`;
        
        // $.each($(fse), function (idx, ele) {
        qelems(fse).forEach((ele, idx)=> {
            
            var union = $(fun).eq(idx).val();
            var column = $(ele).val();
            var value = $(fva).eq(idx).val();
            var operator = value === '' ? 'contain' : $(fop).eq(idx).val();
            if (value === '') { return true }
            if (operator === 'notcontain') {
                mquery.push({ 'field': `nor_${column}__icontains`, 'value': value});
            } else if (operator === 'equal') {
                mquery.push({ 'field': column, 'value': value});
            } else if (operator === 'notequal') {
                mquery.push({ 'field': `nor_${column}`, 'value': value});
            } else if (operator === 'beginwith') {
                mquery.push({ 'field': `${union}${column}__startswith`, 'value': value});
            } else if (operator === 'endwith') {
                mquery.push({ 'field': `${union}${column}__endswith`, 'value': value});
            } else if (operator === 'greaterthan') {
                mquery.push({ 'field': `${union}${column}__gt`, 'value': value});
            } else if (operator === 'lessthan') {
                mquery.push({ 'field': `${union}${column}__lt`, 'value': value});
            } else if (operator === 'contain') {
                mquery.push({ 'field': `${union}${column}__icontains`, 'value': value});
            }
        });
        
        cf_mquery = Grid.custom_filter_query(t_guid)

        if (cf_mquery.length > 0) {
            mquery = [...mquery, ...cf_mquery];
        }
        if (crdata.check_gmquery) {
            if (typeof gmquery !== 'undefined') {
                mquery = [...mquery, ...gmquery];
            }
        }
        if (mquery.length > 0) {
            crdata.mquery = jfy(mquery);
        }
        adata = Object.assign(data, crdata);
        //console.log(adata, 'adata', 'kore');
        console.log(`Filtering data for table ${jfy(t_guid)}`, "with query",crdata)
        console.log("mquery", mquery, "ajax",  settings.ajax);
        return adata
    },
}