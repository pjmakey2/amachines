form_serials = {
    get_form_fields: (fsel) => {
        ffields = [];
        qelems(`${fsel} [name]`).forEach((ii)=>{
            ffields.push(ii.name);
        })
        return ffields
    },
    form_to_json: (fdata) => {
        newo = {};
        fdata.forEach((item, idx) => {
            if (fdata.get(idx) instanceof File ) {
                return
            }
            if (newo.hasOwnProperty(idx)) {
                tmpvalue = newo[idx];
                if (typeof (tmpvalue) === 'string') {
                    tmpvalue = [tmpvalue, item];
                    newo[idx] = tmpvalue;
                } else {
                    newo[idx].push(item);
                }
            } else {
                newo[idx] = item;
            }
        });
        return newo;
    }, 
    form_files: (fdata)=> {
        f_attrs = [];
        fdata.forEach((item, idx) => {
            if (fdata.get(idx) instanceof File ) {
                f_attrs.push(idx)
            }
            
        });
        return f_attrs
    },
    // form_to_json: (formData) => {
    //     const jsonObject = {};
    //     formData.forEach((value, key) => {
    //       jsonObject[key] = value;
    //     });
    //     return jsonObject;
    // },
    form_from_json(fid, jdata) {
        for (const key in jdata) {
            const value = jdata[key];
            if (value === '' || (Array.isArray(value) && value.length === 0)) {
                continue;
            }
            // Find the corresponding form element by name
            const fele = qelem(`#${fid} [name="${key}"]`);
            if (fele) {
                // Check if the form element is a select and if it has the Select2 class
                if (fele.tagName.toLowerCase() === 'select') {
                    if (Array.isArray(value)) {
                        value.forEach(optv => {
                            if (optv.vax){
                                $(formElement).append(new Option(optv.vax, optv.idx, true, true));
                            }
                        });
                    } else {
                        if (value.vax) {
                            $(fele).append(new Option(value.vax, value.idx, true, true));
                        }
                        if (value.set) {
                            $(fele).val(value.set)
                        }
                    }
                    $(fele).trigger('change');
                } else if (fele.type === 'checkbox' || fele.type === 'radio') {
                    // For checkboxes and radio buttons, set the checked property
                    fele.checked = value;
                } else {
                    // For other elements, set the value property
                    fele.value = value;
                }
            }
        }
    },
    base64_to_binary: (b64) => {
        let binaryData = atob(b64);
        var byteArray = new Uint8Array(binaryData.length);
        for (let i = 0; i < binaryData.length; i++) {
            byteArray[i] = binaryData.charCodeAt(i);
        }
        let blob = new Blob([byteArray], { type: 'application/octet-stream' });
        fname = OptsIO.s4generate();
        return new File([blob], `${fname}.png`, { type: 'application/octet-stream' });
    },
    form_empty_localStorage: (formId) => {
        localStorage.removeItem(formId);
    },
    form_to_localStorage: (formId) => {
        let form = document.getElementById(formId);
        let elements = form.elements;
    
        let formData = {};
    
        for (let i = 0; i < elements.length; i++) {
            let element = elements[i];
            let name = element.name;
    
            if (!name) continue;
    
            if (!formData[name]) {
                formData[name] = [];
            }
    
            switch (element.type) {
                case 'checkbox':
                case 'radio':
                    if (element.checked) {
                        formData[name].push(element.value);
                    }
                    break;
                case 'select-multiple':
                    formData[name] = Array.from(element.selectedOptions).map(option => option.value);
                    break;
                case 'date':
                case 'text':
                case 'number':
                case 'email':
                case 'tel':
                case 'url':
                case 'textarea':
                    formData[name].push(element.value);
                    break;
                default:
                    formData[name].push(element.value);
            }
        }
    
        localStorage.setItem(formId, JSON.stringify(formData));
    },
    form_from_localStorage: (formId) => {
        let form = document.getElementById(formId);
        let elements = form.elements;
    
        let formData = JSON.parse(localStorage.getItem(formId));
    
        if (!formData) return; // No saved data
    
        for (let i = 0; i < elements.length; i++) {
            let element = elements[i];
            let name = element.name;
    
            if (!name || !formData.hasOwnProperty(name)) continue;
    
            switch (element.type) {
                case 'checkbox':
                case 'radio':
                    element.checked = formData[name].includes(element.value);
                    break;
                case 'select-multiple':
                    Array.from(element.options).forEach(option => {
                        option.selected = formData[name].includes(option.value);
                    });
                    break;
                case 'date':
                    element.value = formData[name][0] ? new Date(formData[name].shift()).toISOString().split('T')[0] : '';
                    break;
                case 'text':
                case 'number':
                case 'email':
                case 'tel':
                case 'url':
                case 'textarea':
                    element.value = formData[name].shift();
                    break;
                default:
                    element.value = formData[name].shift();
            }
        }
    }
}
form_search = {
    se_select: ({
        surl,
        dele,
        app_name,
        model_name,
        field_display = ['_id'],
        field_id = ['_id'],
        db_fields = [],
        db_methods = [],
        qs_be = [],
        sterm = [],
        theme = 'default',
        ml = 5,
        multiple = false,
        dbcon = 'default',
        dejoin = '_',
        round_v = undefined,
        templateResult = undefined,
        templateSelection = undefined,
        width = '240px',
        allowClear = false,
        placeholder = 'Elija una opcion',
        distinct = undefined,
        headers = {},
        dropdownParent = $(document.body),
        sort = undefined,
        specific_search = undefined,
        clean = false
    }) => {
        if (clean === true) {
            if ($(dele).hasClass("select2-hidden-accessible")) {
                $(dele).select2('destroy');
            }
        }
        return $(dele).select2({
            placeholder: placeholder,
            multiple: multiple,
            theme: theme,
            width: width,
            minimumInputLength: ml,
            templateResult: templateResult,
            templateSelection: templateSelection,
            dropdownParent: dropdownParent,
            allowClear: allowClear,
            ajax: {
                url: surl,
                type: 'POST',
                dataType: 'text',
                headers: headers,
                data: (pps) => {
                    let term = pps.term;
                    ffdata = {
                        'model_app_name': app_name,
                        'model_name': model_name,
                        'module': 'OptsIO',
                        'package': 'io_serial',
                        'attr': 'IoS',
                        'mname': 'seModel',
                        'dbcon': dbcon,
                        'fields': jfy(db_fields),
                        'methods': jfy(db_methods),
                        'mquery': []
                    }
                    if (distinct) {
                        ffdata['distinct'] = jfy(distinct);
                    }
                    if (sort) {
                        ffdata['pq_sort'] = jfy(sort);
                    }
                    if (specific_search) {
                        specific_search['search_value'] = term;
                        ffdata['specific_search'] = jfy(specific_search);
                    }
                    sterm.forEach((itobj) => { 
                        ffdata.mquery.push({'field': itobj, 'value': term });
                    });
                    qs_be.forEach((itobj) => { 
                        ffdata.mquery.push(itobj);
                    });
                    ffdata['mquery'] = jfy(ffdata.mquery);
                    return ffdata;
                },
                processResults: (data) => {
                    sdata = [];
                    dobj = JSON.parse(data);
                    dataj = dobj.qs;
                    dataj.forEach((itobj) => {
                        //id
                        tmpf = [];
                        field_id.forEach((fiobj)=>{
                            tmpf.push(itobj[fiobj]);
                        })
                        fid = tmpf.join(dejoin);
                        //text
                        tmpf = [];
                        field_display.forEach((fiobj)=>{
                            if (round_v) {
                                tmpf.push(`${round_v[0]}${itobj[fiobj]}${round_v[1]}`);
                            } else {
                                tmpf.push(itobj[fiobj]);
                            }
                        })
                        fname = tmpf.join(dejoin);
                        pobj = { id: fid, text: fname }
                        fpobj = Object.assign(itobj, pobj);
                        sdata.push(fpobj);
                    })
                    return { results: sdata };
                }
            }
        })
    },
    se_populate: ({
        surl,
        dele,
        app_name,
        model_name,
        field_display = ['_id'],
        field_id = ['_id'],
        db_fields = [],
        db_methods = [],
        qs_be = [],
        qexc = undefined,
        theme = 'default',
        ml = 2,
        multiple = false,
        dbcon = 'default',
        dejoin_id = '_',
        dejoin = '_',
        round_v = undefined,
        templateResult = undefined,
        templateSelection = undefined,
        createTag = undefined,
        width = '240px',
        allowClear = false,
        clean = true,
        distinct = undefined,
        sort = undefined,
        headers = {},
        init_select2 = true,
        on_focusopen = undefined,
        dropdownParent = $(document.body),
        dropdownCssClass = undefined,
        containerCssClass = undefined,
        closeOnSelect = undefined,
        dropdownAutoWidth = false,
        first_selected = false,
        focus_after_selected = undefined,
        type_after_selected = undefined,
        initialize_empty =  false,
        startRow = 0,
        endRow = 100,
        tags = false,
        check_cache = undefined,
        specific_populate = undefined,

    }) => {
        if (!qelem(dele)) {
            return new Promise((res, rej)=>{
                res(true)
            })
        }
        ffdata = new FormData();
        ffdata.append('model_app_name', app_name);
        ffdata.append('model_name', model_name);
        ffdata.append('module', 'OptsIO');
        ffdata.append('package', 'io_serial');
        ffdata.append('attr', 'IoS');
        ffdata.append('mname', 'seModel');
        ffdata.append('dbcon', dbcon);
        ffdata.append('startRow', startRow);
        ffdata.append('endRow', endRow);
        ffdata.append('fields', jfy(db_fields));
        ffdata.append('methods', jfy(db_methods));
        ffdata.append('mquery', jfy(qs_be))
        if (qexc) {
            ffdata.append('qexc', jfy(qexc))
        }
        if (check_cache) {
            ffdata.append('check_cache', check_cache)
        }
        if (distinct) {
            ffdata.append('distinct', jfy(distinct));
        }
        if (sort) {
            ffdata.append('pq_sort', jfy(sort));
        }
        if (specific_populate) {
            ffdata.append('specific_populate', jfy(specific_populate));
        }
        if (clean === true) {
            if ($(dele).hasClass("select2-hidden-accessible")) {
                try {
                    $(dele).select2('destroy');
                } catch { null }
                
            }            
            $(dele).html('');
            if (!initialize_empty) {
                $(dele).append('<option value="">Elija una opcion</option>');
            }            
        }
        
        return axios.post(surl, ffdata, {headers: headers}).then((rsp)=>{
            if (rsp.data.qs.length <= 0) {
                null
                //$(dele).html(`<option value="">SIN OPCIONES</option>`);
                if (tags === true) {
                    $(dele).select2({
                        multiple: multiple,
                        theme: theme,
                        width: width,
                        templateResult: templateResult,
                        templateSelection: templateSelection,
                        dropdownParent: dropdownParent,
                        dropdownCssClass: dropdownCssClass,
                        containerCssClass: containerCssClass,
                        closeOnSelect: closeOnSelect,
                        dropdownAutoWidth: dropdownAutoWidth,
                        allowClear: allowClear,
                        tags: tags,
                        createTag: createTag
                    })
                }
            } else {
                rsp.data.qs.forEach((itobj, idx)=>{
                    
                    //id
                    tmpf = [];
                    field_id.forEach((fiobj)=>{
                        tmpf.push(itobj[fiobj]);
                    })
                    fid = tmpf.join(dejoin_id);
                    //text
                    tmpf = [];
                    dattrs = []
                    field_display.forEach((fiobj)=>{
                        
                        if (round_v) {
                            tda = `${round_v[0]}${itobj[fiobj]}${round_v[1]}`;
                            
                        } else {
                            tda = itobj[fiobj]
                        }
                        
                        tmpf.push(tda);
                    })
                    
                    db_fields.forEach((fiobj)=>{
                        tda = itobj[fiobj]
                        dattrs.push(`data-${fiobj}="${tda}"`)
                    })
                    
                    db_methods.forEach((fiobj)=>{
                        tda = itobj[fiobj]
                        dattrs.push(`data-${fiobj}="${tda}"`)
                    })
                    fname = tmpf.join(dejoin);
                    dattrs = dattrs.join(' ');
                    
                    pobj = { id: fid, text: fname }
                    if (idx === 0 && first_selected) {
                        $(dele).append(`<option ${dattrs} selected value="${pobj.id}">${pobj.text}</option>`);
                        if (focus_after_selected) {
                            if (type_after_selected === 'select2') {
                                $(focus_after_selected).focus();
                                $(focus_after_selected).select2('open');
                            } else {
                                qelem(focus_after_selected).focus();
                            }
                        }
                    } else {
                        $(dele).append(`<option ${dattrs} value="${pobj.id}">${pobj.text}</option>`);
                    }
                });
                if (init_select2){
                    if (on_focusopen) {
                        $(dele).select2({
                            multiple: multiple,
                            theme: theme,
                            width: width,
                            templateResult: templateResult,
                            templateSelection: templateSelection,
                            dropdownParent: dropdownParent,
                            dropdownCssClass: dropdownCssClass,
                            containerCssClass: containerCssClass,
                            closeOnSelect: closeOnSelect,
                            dropdownAutoWidth: dropdownAutoWidth,
                            allowClear: allowClear,
                            tags: tags,
                            createTag: createTag
                        }).data('select2').listeners['*'].push(
                            function(name, target) { 
                            if(name == 'focus') {
                                $(this.$element).select2("open");
                            }
                        });
                    } else {
                        $(dele).select2({
                            multiple: multiple,
                            theme: theme,
                            width: width,
                            templateResult: templateResult,
                            templateSelection: templateSelection,
                            dropdownParent: dropdownParent,
                            dropdownCssClass: dropdownCssClass,
                            containerCssClass: containerCssClass,
                            closeOnSelect: closeOnSelect,
                            dropdownAutoWidth: dropdownAutoWidth,
                            allowClear: allowClear,
                            tags: tags,
                            createTag: createTag
                        })
                    }
                    if (initialize_empty) {
                        $(dele).val(null).trigger('change');
                    }
                }
            }
            return rsp
        })
    },
    search_select_multiple: ({
        sel = undefined,
        iel = undefined,
        bel = undefined,
        search_attr = undefined
    }) => {
        qelem(iel).addEventListener("keyup", function(evt) {
            let val = this.value.toLowerCase();
            let toexecOptions = qelem(sel).options;
            for (var i = 0; i < toexecOptions.length; i++) {
                var option = toexecOptions[i];
                search_term = option.text
                if (search_attr) {
                    search_term = option.getAttribute(search_attr);
                }
                var show = search_term.toLowerCase().indexOf(val) !== -1;
                option.style.display = show ? "" : "none";
                option.disabled = !show;
            }
            document.querySelectorAll(`${sel} optgroup`).forEach(optgroup => {
                label = optgroup.label.toLowerCase();
                let show = label.toLowerCase().indexOf(val) !== -1;
                optgroup.style.display = show ? "" : "none";
            });
            
            if (bel) {
                qelem(bel).disabled = this.value === "";
            }
            if (evt.key === 'Enter') {
                evt.preventDefault();
                return false;
            }
            
        });
        if (bel) {
            qelem(bel).addEventListener("click", function() {
                let searchtext = qelem(iel);
                searchtext.value = "";
                searchtext.dispatchEvent(new Event("input"));
            });
        }
        
    }
}

form_ui = {
    generate_bs5: (config)=> {
        let fields = [];
        if (!config.form_id) {
            console.error("Configuration must include a 'form_id'.");
            return;
          }
        
          const form = document.createElement("form");
          form.id = config.form_id;

          if (config.hasOwnProperty('hidden_fields')) {
            config.hidden_fields.forEach((ii)=> {
                let inh = document.createElement('input');
                inh.type = 'hidden';
                inh.name = ii.name;
                inh.value = ii.value;
                form.appendChild(inh);
                fields.push(inh.name);
            })
          }
        
          for (const key in config) {
            if (key === 'form_id' || key === 'submit_btn' || key === 'hidden_fields') continue;
        
            const rowDiv = document.createElement("div");
            rowDiv.classList.add("row");
            rowDiv.classList.add("py-2");
            for (const fieldConfig of config[key]) {
              if (fieldConfig.title_row) {
                const rtitle = document.createElement('h3')
                const ut = document.createElement('u')
                ut.innerHTML = fieldConfig.title_row;
                rtitle.appendChild(ut);
                rowDiv.appendChild(rtitle);
                continue
              }
              const colDiv = document.createElement("div");
              colDiv.classList.add(fieldConfig.cls || 'col-md-4');

        
              if (fieldConfig.type === 'input' || fieldConfig.type === 'textarea') {
                
                if (fieldConfig.label) {
                  const label = document.createElement('label');
                  label.textContent = fieldConfig.label;
                  label.classList.add('form-label');
                  colDiv.appendChild(label);
                }
        
                const input = document.createElement(fieldConfig.type);
                if (fieldConfig.required) {
                    input.setAttribute('required', true);
                }

                input.type = fieldConfig.kind || 'text';
                if (fieldConfig.kind == 'number') {
                    input.step = "0.01"
                }
                if (fieldConfig.type === 'textarea') {
                    input.setAttribute('rows', fieldConfig.rows || 3);
                    input.setAttribute('cols', fieldConfig.cols || 3);
                }
                input.name = fieldConfig.name;
                fields.push(input.name);
                input.className = `form-control${fieldConfig.size ? ` form-control-${fieldConfig.size}` : ''}`;
                if (fieldConfig.readonly) {
                    input.setAttribute('readonly', true);
                    input.style.background = '#D3D3D3';
                }

                if (fieldConfig.plh) {
                    input.placeholder = fieldConfig.plh
                }
                if (fieldConfig.value) {
                    input.value = fieldConfig.value
                }
                if (fieldConfig.hasOwnProperty('autocomplete')) {
                    input.setAttribute('autocomplete', fieldConfig.autocomplete);
                }                
                colDiv.appendChild(input);
              } 
              
              if (fieldConfig.type === 'input' && fieldConfig.kind === 'hidden') {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = fieldConfig.name;
                fields.push(input.name);
                colDiv.appendChild(input);
                if (fieldConfig.value) {
                    input.value = fieldConfig.value
                }
              }
              

              if (fieldConfig.type === 'select') {
                if (fieldConfig.label) {
                    const label = document.createElement('label');
                    label.textContent = fieldConfig.label;
                    label.classList.add('form-label');
                    colDiv.appendChild(label);
                }
                const select = document.createElement('select');
                select.name = fieldConfig.name;
                fields.push(select.name);
                select.className = `form-select${fieldConfig.size ? ` form-select-${fieldConfig.size}` : ''}`;
                if (fieldConfig.required) {
                    select.setAttribute('required', true);
                }

                if (fieldConfig.readonly) {
                    select.setAttribute('readonly', true);
                    select.style.background = '#D3D3D3';
                }
                if (fieldConfig.plh) {
                    const opt = document.createElement('option');
                    opt.innerHTML = fieldConfig.plh;
                    select.appendChild(opt);
                }
                if (fieldConfig.values) {
                    const optv = document.createElement('option');
                    optv.innerHTML = 'Elija una opcion';
                    select.appendChild(optv);
                    fieldConfig.values.forEach((vvobj)=>{
                        const optv = document.createElement('option');
                        optv.value = vvobj.value;
                        optv.innerHTML = vvobj.text;
                        if (vvobj.selected) {
                            optv.selected = true;
                        }
                        select.appendChild(optv);
                    })
                }
                colDiv.appendChild(select);
              }

              if (fieldConfig.hlp) {
                hlpdiv = document.createElement('div');
                hlpdiv.classList.add('form-text')
                hlpdiv.innerHTML = fieldConfig.hlp;
                colDiv.appendChild(hlpdiv);
              }
        
              rowDiv.appendChild(colDiv);
            }
        
            form.appendChild(rowDiv);
          }
        
          if (config.submit_btn) {
            const submitBtn = document.createElement("button");
            submitBtn.type = "submit";
            submitBtn.className = config.submit_btn.cls || 'btn btn-primary mt-2';
            submitBtn.textContent = config.submit_btn.label || 'Submit';
            form.appendChild(submitBtn);
          }
        
          return {form: form, fields: fields};
    },

    set_readonly: (formId) => {
        const form = document.getElementById(formId);
        if (!form) return;
        const elements = form.querySelectorAll('input, textarea, select, button, a');
        elements.forEach(el => {
            console.log(el.tagName);
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                //el.readOnly = true;
                el.disabled = true;
            } else if (el.tagName === 'SELECT') {
                if ($(el).hasClass('select2-hidden-accessible')) {
                    $(el).prop('disabled', true).trigger('change.select2');
                } else {
                    el.disabled = true;
                }
            } 
            else if (el.tagName === 'BUTTON') {
                el.disabled = true;
            }
            else if (el.tagName === 'A') {
                el.remove();
            }
        });
        // Remove submit buttons
        const submitButtons = form.querySelectorAll('input[type="submit"], button[type="submit"]');
        submitButtons.forEach(btn => btn.remove());
    }
}

form_select = {
    clear_select2: (selector)=>{
        $(selector).val(null).trigger('change');
    },
    remove_option_value: (selector, value) => {
        $(`${selector} option[value="${value}"]`).not(':selected').remove();
    }
}


form_input = {
    on_enter_func: (einput, call_func)=>{
        einput.addEventListener("keypress", function(event) {
            // If the user presses the "Enter" key on the keyboard
            if (event.key === "Enter") {
              event.preventDefault();
              call_func();
            }
        });
    },
    calculate_dv: (ori, dst) =>{
        ruc = qelem(ori).value;
        base_max=11;
        ruc_n = '';
        for (i=0; i < ruc.length;i++) {
            v_char = ruc[i];
            v_nchar =  v_char.toUpperCase().charCodeAt(0);
            if (!(v_nchar >= 48) && (v_nchar <= 57)) {
                ruc_n += str(v_nchar);
            } else {
                ruc_n += v_char;
            }
        }
        ruc = ruc_n;
        k = 2;
        total = 0;
        for (i=ruc.length-1; i >= 0;i--) {
            aux_num = ruc[i];
            if (k > base_max) { k = 2 }
            aux_num = parseInt(aux_num);
            total += (aux_num * k);
            k += 1;
        }
        rr = total % 11;
        if (rr > 1) {
            dv = 11 - rr;
        } else {
            dv = 0;
        }
        qelem(dst).value = dv;
    }
}

form_validation = {
    just_number: (e) => {
        const pattern = /^-?\d*(\.\d{0,3})?$/;
        if (!pattern.test(e.target.value)) {
            e.target.value = e.target.value.slice(0, -1); // Remove last character
        }
    },
    just_number_integer: (e) => {
        const pattern = /^-?\d*(\d{0,3})?$/;
        if (!pattern.test(e.target.value)) {
            e.target.value = e.target.value.slice(0, -1); // Remove last character
        }
    },
    justNumberAndLetters: (e) => {
        const pattern = /^[a-zA-Z0-9]*$/;
        if (!pattern.test(e.target.value)) {
            e.target.value = e.target.value.slice(0, -1); // Remove last char if invalid
        }
    },
    justLetters: (e) => {
        const pattern = /^[a-zA-Z]*$/;
        if (!pattern.test(e.target.value)) {
            e.target.value = e.target.value.slice(0, -1); // Remove last char if invalid
        }
    },
    password_strength: (password) => {
        let strength = 0;
        if (password.match(/[a-z]+/)) {
          strength += 1;
        }
        if (password.match(/[A-Z]+/)) {
          strength += 1;
        }
        if (password.match(/[0-9]+/)) {
          strength += 1;
        }
        if (password.match(/[$@#&!]+/)) {
          strength += 1;
        }
        if (password.length < 12) {
          msg = "El minimo de caracteres es 12";
          return {
            msg: msg,
            strength: strength
          }
        }
        switch (strength) {
          case 0:
            msg = "Tu clave es muy debil";
            break;
          case 1:
            msg = "Tu clave es debil";
            break;
          case 2:
            msg = "Tu clave es moderada";
            break;
          case 3:
            msg = "Tu clave es fuerte";
            break;
          case 4:
            msg = "Tu clave es muy fuerte";
            break;
        }
        return {msg: msg,strength: strength}
    }
}

form_controls = {
    filter_date_range: (selector, cb) => {
        var start = moment().subtract(30, 'days');
        var end = moment().add(1, 'days');
        
        $(selector).daterangepicker({
            startDate: start,
            endDate: end,
            ranges: {
                'Hoy': [moment(), moment()],
                'Ayer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Este mes': [moment().startOf('month'), moment().endOf('month')],
                'El mes pasado': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
                'Últimos 7 días': [moment().subtract(6, 'days'), moment()],
                'Últimos 15 días': [moment().subtract(14, 'days'), moment()],
                'Este año': [moment().startOf('year'), moment().endOf('year')],
            },
            locale: {
                "format": "DD-MM-YYYY",
                "separator": " - ",
                "applyLabel": "Aceptar",
                "cancelLabel": "Cancelar",
                "fromLabel": "Desde",
                "toLabel": "Hasta",
                "customRangeLabel": "Personalizado",
                "firstDay": 1
            }
        }, cb);

        cb(start, end);
    }

}