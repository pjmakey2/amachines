var qelem = (selector) => document.querySelector(selector);
var qelems = (selector) => document.querySelectorAll(selector);
var jfy = (obj) => JSON.stringify(obj) 
var jpar = (obj) => JSON.parse(obj) 
const DINNERW = 844;

var log = {
  success: (msg) => console.log(`%c✓ ${msg}`, 'color: #22c55e; font-weight: bold;'),
  error: (msg) => console.log(`%c✗ ${msg}`, 'color: #ef4444; font-weight: bold;'),
  info: (msg) => console.log(`%cℹ ${msg}`, 'color: #3b82f6; font-weight: bold;'),
  warning: (msg) => console.log(`%c⚠ ${msg}`, 'color: #f59e0b; font-weight: bold;'),
};

OptsIO = {
    getToken: ()=>{
        return localStorage.getObj('token');
    },
    setToken: (token)=>{
        return localStorage.setObj('token', token);
    },
    getCookie: (name)=>{
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    getTmpl: ({url, container, template, dattrs, loadertarget = {}, raw = false, 
        model_app_name = undefined,
        model_name = undefined,
        pk = undefined,
        dbcon = undefined,
        surround = undefined,
        rpt_view = undefined,
        responseType = 'text',
        specific_qdict = undefined,
    }) => {
        //call first dashboard
        pps = { 'tmpl': template }
        if ((model_app_name !== undefined) & (model_name !== undefined) & (pk !== undefined)) {
            pps['model_app_name'] = model_app_name
            pps['model_name'] = model_name
            pps['pk'] = pk
        }
        if (dbcon !== undefined) {
            pps['dbcon'] = dbcon
        }
        if (surround !== undefined) {
            pps['surround'] = surround
        }        
        if (dattrs) {
            pps['dattrs'] = jfy(dattrs);
        }
        if (rpt_view) {
            pps['rpt_view'] = true;
            return axios.get(url, { params: pps })
        }

        if (specific_qdict) {
            pps['specific_qdict'] = jfy(specific_qdict)
        }

        if (loadertarget.hasOwnProperty('msg_block')) {
            if (!loadertarget.hasOwnProperty('dele')) {
                loadertarget['dele'] = container
            }
            console.log('call lodader', loadertarget);
            //UiB.BlockLoaderSpecifyAjax(loadertarget)
            UiB.StartLoaderSpecifyAjax(loadertarget);
        } else {
            UiB.StartLoaderAjax();
        }
        
        if (raw) {
            return axios.get(url, { params: pps, responseType: responseType })
        }
        
        return axios.get(url, { params: pps, responseType: responseType })
            .then((rsp) => OptsIO.setInnerHTML(document.querySelector(container), rsp.data) )
            .catch((err) => UiB.MsgError(err))
            .finally(() => {
                UiB.kILLLoaderAjax()
                $('#kt_app_header_menu .menu-title').html('');
            });
    },
    

    setInnerHTML: (elm, html) => {
        // Método mejorado para insertar HTML y ejecutar scripts (inline y externos)

        // Crear un contenedor temporal para parsear el HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // Extraer todos los scripts ANTES de insertar el contenido
        const scripts = tempDiv.querySelectorAll('script');
        const scriptElements = Array.from(scripts);

        // Remover scripts del HTML temporal
        scriptElements.forEach(script => script.remove());

        // Insertar el HTML sin scripts
        elm.innerHTML = tempDiv.innerHTML;

        // Ejecutar scripts en orden
        scriptElements.forEach(oldScript => {
            const newScript = document.createElement('script');

            // Copiar todos los atributos
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });

            // Manejar scripts externos vs inline
            if (oldScript.src) {
                // Script externo: copiar src y agregar al head
                newScript.src = oldScript.src;
                document.head.appendChild(newScript);
            } else {
                // Script inline: copiar contenido y agregar al contenedor
                newScript.textContent = oldScript.textContent;
                elm.appendChild(newScript);
            }
        });

        return elm;
    },
    s4generate: () => {
        return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
    },
    getuuid: () => {
        return OptsIO.s4generate() + OptsIO.s4generate() + '-' + OptsIO.s4generate() + '-' + OptsIO.s4generate() + '-' +
            OptsIO.s4generate() + '-' + OptsIO.s4generate() + OptsIO.s4generate() + OptsIO.s4generate();
    },
    gen_tracking_string: ()=> {
        // ---------------------------------------------------------------
        var anio, mes, dia, hora, minuto, segundo, milisegundo;
        var tracking;
        var objetoFecha, objetoTracking;
        // ---------------------------------------------------------------
        objetoFecha = new Date();
        anio = objetoFecha.getUTCFullYear();
        mes = objetoFecha.getUTCMonth() + 1;
        dia = objetoFecha.getUTCDate();
        hora = objetoFecha.getUTCHours();
        minuto = objetoFecha.getUTCMinutes();
        segundo = objetoFecha.getUTCSeconds();
        milisegundo = objetoFecha.getUTCMilliseconds();

        tracking = "" + anio;
        tracking = tracking.substring(2);
        tracking = "NT" + tracking;

        if (mes < 10) tracking += "0" + mes;
        else tracking += mes;

        if (dia < 10) tracking += "0" + dia;
        else tracking += dia;

        if (hora < 10) tracking += "0" + hora;
        else tracking += hora;

        if (minuto < 10) tracking += "0" + minuto;
        else tracking += minuto;

        if (segundo < 10) tracking += "0" + segundo;
        else tracking += segundo;

        tracking += milisegundo;
        return tracking;
    }
}

fMenu = {
    NSPA: ()=> {
        localStorage.setItem('lastMenu', jfy({
            url: 'NSPA',
            container: '',
            template: '',
            specific_qdict: undefined
        }));
    },
    Draw: (url, container, template, ele, specific_qdict) => {
        // Save the last visited endpoint and container to localStorage
        
        if (!ele) {
            dtmpl = undefined
        } else {
            dtmpl = ele.getAttribute('data-tmpl')
        }
        localStorage.setItem('lastMenu', jfy({
            url: url,
            container: container,
            template: template,
            ele:  dtmpl,
            specific_qdict: specific_qdict
        }));
        //mbl = UiB.BlockLoaderSpecifyAjax(
        //    {
        //        dele: '#kt_app_sidebar_menu_wrapper',
        //        msg_block: '...'
        //    }
        //)
        //mbl.block();
        pars = {
            url: url,
            container: container,
            template: template,
            loadertarget: {
                'msg_block': 'Cargando...',
                'dele': container
            },
            dattrs: {
                from_menu: true
            }
        }
        if (specific_qdict) {
            pars['specific_qdict'] = UiN.base64ToJson(specific_qdict);
        }
        OptsIO.getTmpl(pars).then(()=>{
            //mbl.destroy();
            //mbl.release();
            try {
                qelem('[v-cloak]').style.visibility = 'visible'
            } catch { null }
            if (ele) {
                $('a.menu-link').removeClass('active');
                $(ele).addClass('active');
                ham_b = qelem('#hambu-menu')
                if (ham_b) {
                    $('#kt_app_sidebar_mobile_toggle').click();
                    // qelem('#kt_app_sidebar').classList.remove('drawer-on');
                    // qelem('body').removeAttribute("data-kt-drawer-app-sidebar", "on");
                    // qelem('body').removeAttribute("data-kt-drawer", "on");
                    // $('#kt_app_sidebar_mobile_toggle').removeClass('active')
                    // $('#kt_app_sidebar_mobile_toggle').removeClass('btn-active-color-primary')
                }
                
                mp = qelem(`.${ele.getAttribute('data-main_menu')}`);
                if (mp) {
                    mp.classList.add('active');
                }
            }
            dov = qelem('.drawer-overlay')
            if(dov) {
                dov.remove();
            }
            KTScroll.createInstances();
            history.replaceState(null, '', '/');
        }).then(()=>{
            if (Stream) {
                ktracks = Stream.getTracks();
                ktracks.forEach(track => track.stop());
                Stream = undefined;
            }
            if (balanzaPesoID > 0){
                console.log(`Limpiando intervalo ${balanzaPesoID}`);
                clearInterval(balanzaPesoID)
            }
        })
    },
    forceMobile: ()=> {
        console.log('Forzando UI MOBILE')
        $(".dinamic_styles").text("@media (min-width:992px){[data-kt-app-sidebar-minimize=on]{--bs-app-sidebar-width:0px;--bs-app-sidebar-gap-start:0px;--bs-app-sidebar-gap-end:0px;--bs-app-sidebar-gap-top:0px;--bs-app-sidebar-gap-bottom:0px}[data-kt-app-sidebar-minimize=on][data-kt-app-sidebar-hoverable=true] .app-sidebar:not(:hover) .app-sidebar-menu .menu-content,[data-kt-app-sidebar-minimize=on][data-kt-app-sidebar-hoverable=true] .app-sidebar:not(:hover) .app-sidebar-menu .menu-title{opacity:100;transition:opacity .3s!important}}");
        $('#kt_app_sidebar').addClass('drawer drawer-start')
        qelem('#kt_app_sidebar').style.width = '300px';
        qelem('body').removeAttribute("data-kt-drawer-app-sidebar", "on");
        qelem('body').removeAttribute("data-kt-drawer", "on");
        $('#kt_app_sidebar_logo').addClass('d-none');
        $('#hambu-menu').removeClass('d-lg-none');
        $('.app-header-menu').remove();
        $('.app-main').css('padding-left',  0);
        $('.app-main').css('padding-right',  0);
        $('.app-content').css('max-width',  'none');
        $('.app-content').css('padding-top',  '20px');
        $('.app-content').css('padding-bottom',  '20px');
        $('.app-content').css('padding-left',  0);
        $('.app-content').css('padding-right',  0);
    },
    hasTouchSupport: () => {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }
}

UiB = {
    BlockLoaderSpecifyAjax: ({ dele, msg_block = 'Cargando...' }) => {
        msg_block = 'Procesando...'
        bbui = new KTBlockUI(document.querySelector(dele), 
            {
                message: `<div class="blockui-message"><span class="spinner-border text-primary"></span> ${msg_block}</div>`,
                overlayClass: "bg-primary bg-opacity-25",
        
            });
        return bbui;
        
    },
    StartLoaderSpecifyAjax: ({ dele, msg_block = 'Cargando...' }) => {
        console.log(dele)
        target = qelem(dele);
        target.innerHTML = `
        <div class="d-flex justify-content-center">
            <div style="width: 4rem; height: 4rem;"  class="spinner-border text-primary" role="status">
                <span class="sr-only"></span>
            </div>
            
        </div>`;
        // let blockUI = new KTBlockUI(target, {
        //     message: `<div class="blockui-message"><span class="spinner-border text-primary"></span> ${msg_block}</div>`,
        //     overlayClass: "bg-primary bg-opacity-25",

        // });
        // blockUI.block();
        // blockUI.destroy();
    },
    StartLoaderAjax: ({ duration = 5000 } = {}) => {
        // Populate the page loading element dynamically.
        // Optionally you can skipt this part and place the HTML
        // code in the body element by refer to the above HTML code tab.
        const loadingEl = document.createElement("div");
        document.body.prepend(loadingEl);
        loadingEl.classList.add("page-loader");
        loadingEl.classList.add("position-absolute");
        loadingEl.classList.add("w-100");
        loadingEl.classList.add("h-100");
        loadingEl.classList.add("bg-dark");
        loadingEl.classList.add("bg-opacity-25");
        loadingEl.classList.add("z-3");
        loadingEl.classList.add("d-flex");
        loadingEl.classList.add("justify-content-center");
        loadingEl.innerHTML = `
            <span style="width: 4rem; height: 4rem;" class="spinner-border text-primary mt-1 p-2" role="status"></span>
            <span class="text-gray-800 fs-6 fw-semibold mt-5"></span>
            `;
        //Set and inactive close behaviour after 79 seconds
        setTimeout(function () {
            loadingEl.remove();
        }, duration);
    },
    kILLLoaderAjax: () => {
        qelems('.page-loader').forEach((ii)=>ii.remove());
    },
    BeMsgHandle: ({rsps, timer = 3000, n_modal = undefined, offcanvasglobal = undefined, not_w=false}) => {
        if (Array.isArray(rsps) === false) {
            if (typeof rsps === 'object' && rsps !== null) {
                if (rsps.hasOwnProperty('msgs')) {
                    rsps = rsps.msgs;
                } else {
                    rsps = [rsps];
                }
            }
        }
        //ssty = 'style="width: 30rem;"';
        ssty = '';
        if (not_w) {
            ssty = '';
        }
        emsg = [];
        let success = true;
        rsps.forEach((ee)=>{
            if (ee.success) {
                if (ee.show_success === false) {
                    return
                }
                emsg.push(`<span class="badge bg-success fs-1 text-wrap" ${ssty} role="alert">
                ${ee.success}
                </span>`)
                
            }
            if (ee.error) {
                // Check if error contains traceback (Python error)
                let errorContent = ee.error;
                if (errorContent.includes('Traceback') || errorContent.includes('File "')) {
                    emsg.push(`<div class="alert alert-danger text-start" role="alert">
                        <h5 class="alert-heading mb-2"><i class="mdi mdi-alert-circle me-2"></i>Error del Sistema</h5>
                        <hr>
                        <pre class="mb-0" style="white-space: pre-wrap; word-wrap: break-word; font-size: 12px; max-height: 400px; overflow-y: auto; background: #2d2d2d; color: #f8f8f2; padding: 10px; border-radius: 5px;">${errorContent}</pre>
                    </div>`)
                } else {
                    emsg.push(`<div class="alert alert-danger fs-4 text-wrap" ${ssty} role="alert">
                        <i class="mdi mdi-alert-circle me-2"></i>${errorContent}
                    </div>`)
                }
                success = false;
                timer = 0;
            }
            if (ee.info) {
                emsg.push(`<div class="badge bg-info fs-1 text-wrap" ${ssty} role="alert">
                ${ee.info}
                </div>`)
            }
        })
        Swal.fire({
            title: "",
            html: emsg.join(''),
            showConfirmButton: !success,
            confirmButtonText: 'Cerrar',
            timer: success ? timer : 0,
            timerProgressBar: success,
            width: success ? 'auto' : '800px',
            customClass: {
                confirmButton: 'btn btn-secondary'
            }
        }).then(()=>{
            if ((success) && (offcanvasglobal)) {
                $('#offcanvasGlobalUiBody').html('');
                $('#btn-offcanvas-global-close').click();
                return
            }
            if ((success) && (n_modal)) {
                const my_modal = document.querySelector(`${n_modal}`)
                const modalobj = bootstrap.Modal.getInstance(my_modal) // Retrieve a Carousel instance
                modalobj.dispose();
                qelem(`${n_modal}`).remove();
                return
            }
        });
    },
    NotBlockingBeMsgHandle: ({rsps, target, timer = 2000, not_w = false}) => {
        emsg = [];
        let success = false;
        // sty = 'style="width: 30rem;"';
        sty = '';
        if (not_w) {
            sty = '';
        }
        rsps.forEach((ee)=>{
            if (ee.success) {
                if (ee.show_success === false) {
                    return
                }
                emsg.push(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                <span class="badge bg-success fs-1 text-wrap" ${sty}>${ee.success}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`)
                success = true;
            }
            if (ee.error) {
                emsg.push(`<div class="alert alert-danger alert-dismissible fade show" role="alert">
                <span class="badge bg-danger fs-1 text-wrap" ${sty}>${ee.error}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`)
                timer = 0
            }
            if (ee.info) {
                emsg.push(`<div class="alert alert-info alert-dismissible fade show" role="alert">
                <span class="badge bg-info fs-1 text-wrap" ${sty}>${ee.info}</span>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`)
            }
        })
        qelem(target).innerHTML = emsg.join('');
        if (timer > 0) {
            setTimeout(()=>{
                if (target) {
                    qelem(target).innerHTML = '';
                }
            }, timer)
        }
    },
    MsgSwall: ({msg, ttype='info', confirm_btn='Aceptar', cancel_btn='Cancelar', timer= undefined, c_class=''}) => {
        return Swal.fire({
            html: msg,
            width: 600,
            icon: ttype,
            buttonsStyling: false,
            showCancelButton: cancel_btn ? true : false,
            confirmButtonText: confirm_btn,
            cancelButtonText: cancel_btn,
            focusConfirm: true,
            timer: timer,
            heightAuto: false,
            customClass: {
                confirmButton: `btn btn-primary btn-sweet-confirmation ${c_class} fs-1`,
                cancelButton: `btn btn-danger ${c_class} fs-1`
            }
        })
    },
    MsgSuccess: (msg) => {
        Toastify({
            className: "toastify-success",
            text: msg,
            duration: 2000,
            close: false,
            gravity: "top", // `top` or `bottom`
            position: "center", // `left`, `center` or `right`
            stopOnFocus: false, // Prevents dismissing of toast on hover
            style: {
              background: "#076904",
              'font-size': "16px",
              'font-weight': '500'
            },
            onClick: function(){} // Callback after click
          }).showToast();
          $('.toastify-success').eq(-1).css("margin-top", "50px");
    },
    MsgError: (msg) => {
        Toastify({
            className: "toastify-error",
            text: msg,
            duration: 3000,
            close: false,
            gravity: "top", // `top` or `bottom`
            position: "center", // `left`, `center` or `right`
            stopOnFocus: false, // Prevents dismissing of toast on hover
            style: {
              background: "#F34C4C",
              'font-size': "16px",
              'font-weight': '500'
            },
            onClick: function(){} // Callback after click
          }).showToast();
          $('.toastify-error').eq(-1).css("margin-top", "50px");
    },
    MsgInfo: (msg) => {
        Toastify({
            className: "toastify-info",
            text: msg,
            duration: 3000,
            close: false,
            gravity: "top", // `top` or `bottom`
            position: "center", // `left`, `center` or `right`
            stopOnFocus: false, // Prevents dismissing of toast on hover
            style: {
              background: "#6694F8",
              'font-size': "16px",
              'font-weight': '500'
            },
            onClick: function(){} // Callback after click
          }).showToast();
          $('.toastify-info').eq(-1).css("margin-top", "50px");
    },
    MsgWarning: (msg) => {
        Toastify({
            className: "toastify-warning",
            text: msg,
            duration: 3000,
            close: false,
            gravity: "top", // `top` or `bottom`
            position: "center", // `left`, `center` or `right`
            stopOnFocus: false, // Prevents dismissing of toast on hover
            style: {
              background: "#EE9663",
             'font-size': "16px",
             'font-weight': '500'
            },
            onClick: function(){} // Callback after click
          }).showToast();
          $('.toastify-warning').eq(-1).css("margin-top", "50px");
    },
    formatDate: ({dateobj, format= 'YYYY-MM-DD'})=>{
        if (format == 'YYYY-MM-DD') {
            return dateobj.getFullYear() + "-" +((dateobj.getMonth()+1).toString().length != 2 ? "0" + (dateobj.getMonth() + 1) : (dateobj.getMonth()+1)) + "-" + (dateobj.getDate().toString().length != 2 ?"0" + dateobj.getDate() : dateobj.getDate());
        }
        if (format == 'DD/MM/YYYY') {
            return (dateobj.getDate().length != 2 ?"0" + dateobj.getDate() : dateobj.getDate()) + '/' + ((dateobj.getMonth()+1).length != 2 ? "0" + (dateobj.getMonth() + 1) : (dateobj.getMonth()+1)) + '/' + dateobj.getFullYear();
        }        
        
    },
    drawModal: ({title, content, target, nid, size = 'am_modal', show = true, set_focus='data-bs-focus="true"'})=>{
        if (nid === undefined) {
            nid = OptsIO.s4generate();
        }
        ms = `
        <div ${set_focus} class="modal fade" id="${nid}" tabindex="-1" aria-labelledby="${nid}Label" aria-hidden="true">
            <div class="modal-dialog ${size}">
            <div>
                <h1 class="modal-title fs-5" id="${nid}Label">${title}</h1>
                
            </div>
            <div class="modal-content">
                <button type="button" class="btn-close btn btn-danger" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                <div class="modal-body" id="modal_${nid}">
                   ${content}
                </div>
            </div>
            </div>
        </div>
        `
        OptsIO.setInnerHTML(qelem(target), ms);
        myModal = new bootstrap.Modal(`#${nid}`, {});
        if (show === true){
            myModal.show();
        }
        let myModalEl = document.getElementById(nid);
        myModalEl.addEventListener('hidden.bs.modal', event => {
            OptsIO.setInnerHTML(qelem(target), '');
            console.log(`Cleanning modal ${nid}`);
        })
        
    },
    offCanvasListener(offCanvasId) {
        let myOffCanvas = document.getElementById(offCanvasId);
    
        const hideCanvas = () => {
            let openedCanvas = bootstrap.Offcanvas.getInstance(myOffCanvas);
            setTimeout(() => {
                openedCanvas.hide();
            }, 1000);
            event.target.removeEventListener('mouseleave', hideCanvas);
        }
        const listenToMouseLeave = (event) => {
            event.target.addEventListener('mouseleave', hideCanvas);
        }
        
        myOffCanvas.addEventListener('shown.bs.offcanvas', listenToMouseLeave);
    }
}

UiN = {
    formatNumberU: (value) => value.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,"),
    formatNumber: (value) => value.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1,"),
    formatNumberP: (value) => value.toString() .replace('.', ',').replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1."),
    formatPercen: (value) => value.toFixed(2).toString() + '%',
    abbreviateNumber: (num, fixed) => {
        if (num === null) { return null; } // terminate early
        if (num === 0) { return '0'; } // terminate early
        fixed = (!fixed || fixed < 0) ? 0 : fixed; // number of decimal places to show
        var b = (num).toPrecision(2).split("e"), // get power
            k = b.length === 1 ? 0 : Math.floor(Math.min(b[1].slice(1), 14) / 3), // floor at decimals, ceiling at trillions
            c = k < 1 ? num.toFixed(0 + fixed) : (num / Math.pow(10, k * 3) ).toFixed(1 + fixed), // divide by power
            d = c < 0 ? c : Math.abs(c), // enforce -0 is 0
            e = d + ['', 'K', 'M', 'MM', 'MMM'][k]; // append power
        return e;
    },
    abbreviateNumberAbs: (num, fixed) => {
        if (num === null) { return null; } // terminate early
        if (num === 0) { return '0'; } // terminate early
        fixed = (!fixed || fixed < 0) ? 0 : fixed; // number of decimal places to show
        var b = (num).toPrecision(2).split("e"), // get power
            k = b.length === 1 ? 0 : Math.floor(Math.min(b[1].slice(1), 14) / 3), // floor at decimals, ceiling at trillions
            c = k < 1 ? num.toFixed(0 + fixed) : (num / Math.pow(10, k * 3) ).toFixed(1 + fixed), // divide by power
            d = c < 0 ? c : Math.abs(c), // enforce -0 is 0
            e = num / [0, 1000000, 1000000, 1000000, 1000000000][k]; // append power
        if (k <= 1) {
            e = parseFloat(e, 2);
        } else {
            e = parseInt(e);
        }
        return UiN.formatNumberP(e);
    },
    roundPrice: (inv, pos) => {
        const base = Math.pow(10, pos);
        bt = inv / base
        n = Math.abs(bt); // Change to positive
        dp = n - Math.floor(bt)
        dp = dp*10
        // if (dp < 5) {
        //     return Math.round(bt) * base;
        // }
        //return inv
        return Math.round(bt) * base;
    },
    roundPrice50: (amount) => {
        // Determine if the amount is an integer or a float
        if (typeof amount === 'number' && !Number.isInteger(amount)) {
            // Separate the integer and decimal parts
            let integerPart = Math.floor(amount);
            let decimalPart = amount - integerPart;
            // Handle rounding based on the decimal part
            if (decimalPart > 0) {
                if (decimalPart > 0.5) {
                    return integerPart + 0.50;
                } else if (decimalPart < 0.5) {
                    return integerPart + 0.00;
                } else {
                    return amount;
                }
            }
            // Round the integer part to the nearest multiple of 50
            let roundedInteger = Math.floor(integerPart / 50) * 50;
            // Round the decimal part to the nearest 0.50
            let roundedDecimal = decimalPart < 0.50 ? 0.0 : 0.50;
            return roundedInteger + roundedDecimal;
        } else {  // If the amount is an integer
            return Math.floor(amount / 50) * 50;
        }
    },
    _roundToNearest100: (amount) => {
        if (typeof amount === 'number' && !Number.isInteger(amount)) {
            // Separate the integer and decimal parts
            let integerPart = Math.floor(amount);
            let decimalPart = amount - integerPart;
            if (decimalPart > 0) {
                return amount;
            }
        }
        return Math.round(amount / 100) * 100;
    },
    base64ToJson: (b64) => {
        try {
            const jsonStr = atob(b64);
            return jpar(jsonStr);
        } catch (e) {
            console.error("Invalid Base64 JSON string", e);
            return null;
        }
    }
}

UeMoji = {
    ToUnicodeSeq: (emoji) => {
        return Array.from(emoji).map(char => char.codePointAt(0).toString(16)).join('-');
    },

    SeqToEmoji: (unicodeSequence) => {
        return unicodeSequence.split('-').map(part => String.fromCodePoint(parseInt(part, 16))).join('');
    }
}

function localStorageExtension() {
    Storage.prototype.setObj = function(key, obj) {
        return this.setItem(key, LZString.compress(jfy(obj)));
    };
    Storage.prototype.getObj = function(key) {
        if (!this.getItem(key)) {return false;};
        return jpar(LZString.decompress(this.getItem(key)));
    };

    Storage.prototype.setExpiration = function(key, obj, ttl) {
        let now = new Date()
        // `item` is an object which contains the original value
        // as well as the time when it's supposed to expire
        let item = {
            vvv: obj,
            expiry: now.getTime() + ttl,
        }
        localStorage.setItem(key, JSON.stringify(item))
    };

    Storage.prototype.getExpiration = function(key) {
        let itemStr = localStorage.getItem(key)
        // if the item doesn't exist, return null
        if (!itemStr) {
            return null
        }
        let item = JSON.parse(itemStr)
        let now = new Date()
        // compare the expiry time of the item with the current time
        if (now.getTime() > item.expiry) {
            // If the item is expired, delete the item from storage
            // and return null
            localStorage.removeItem(key)
            return null
        }
        return item.vvv
    }
}

