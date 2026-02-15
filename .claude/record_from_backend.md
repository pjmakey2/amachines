# Cómo obtener registros del backend en formato json.

## Usa este método para obtener registros del backend
## Esto es similar a graphql

Lee primero OptsIO.io_serial.seModel para entender la funcionalidad central.

    tdata = new FormData();
    tdata.append('module','OptsIO');  //Esto siempre tiene que ser este valor
    tdata.append('package','io_serial'); //Esto siempre tiene que ser este valor
    tdata.append('attr', 'IoS'); //Esto siempre tiene que ser este valor
    tdata.append('mname', 'seModel') //Esto siempre tiene que ser este valor
    tdata.append('model_app_name', 'FL_Structure'); //Aquí es donde especificas el app_name de Django
    tdata.append('model_name', 'Clientes'); //Aquí es donde especificas el modelo del cual obtendrás el registro.
    tdata.append('fields', jfy([
        'clientecodigo', 'clientemail', 'sucursal__sucursal'
    ])); //Aquí especificas qué campos quieres obtener, debes preguntar esto.
    tdata.append('methods', jfy([
        'normalize_name', 'get_ruc'
    ])); //También podemos obtener métodos del modelo, debes preguntar esto.
    tdata.append('dbcon', 'default'); //qué base de datos definida usamos, por defecto es "default"
    tdata.append('mquery', jfy([{'field': 'clientecodigo', 'value':  17460 }])); // Construye query para aplicar al .filter del queryset
    axios.post('{% url "iom" %}', tdata, {headers: {'X-CSRFToken': OptsIO.getCookie('csrftoken')}}).then((rsp)=>{ //llama cosas
        dd = rsp.data.qs // esto es un array de los registros
        //Haz cosas
    })

## Como los formularios usualmente guardar y/o actualizan los datos.
 
 ##Formulario ver ejemplo /home/peter/projects/Amachine/templates/Sifen/DocumentHeaderCreateUi.html

   El formulario usualmente interactua con /home/peter/projects/Amachine/OptsIO/io_maction.py

   Por que ? 

      class IOMaction:
        def process_record(self, *args, **kwargs) -> dict:

    Tiene la particularidad que procesa los metodos segun la definicion hecha en el backend.

    1. Donde primero se lee si es que hay la definicion de b_vals.
       Metodos que corren antes del metodo de guardado y/o actualizado.

       Es posible para que se valida ciertos datos explicitos y/o implicitos referentes al registro que se quiere guardar.
    2. c_a contiene la definicion del metodo principal, que es el que guardar y/o actuliza el registro

    3. a_vals mismo que b_vals pero en inversa, metodos que se ejecutan despues del guardado y/o actualizacion del registros.

    Ejemplo.
      

        fdata.append('uc_fields', jfy(edata));
        fdata.append('b_vals', jfy([
            {
                'module': 'Sifen',
                'package': 'mng_sifen',
                'attr': 'MSifen',
                'mname': 'validate_ruc',
                'cont': false, //Si devuelve error el metodo, el proceso de guardado y/o actualizacion se detiene cuando cont esta igual a false
                'show_success': true
            },
            {
                'module': 'Sifen',
                'package': 'mng_sifen',
                'attr': 'MSifen',
                'mname': 'inform_bad_ruc',
                'cont': false,  //Si devuelve error el metodo, el proceso de guardado y/o actualizacion se detiene cuando cont esta igual a false
                'show_success': true
            },
        ]));
        fdata.append('c_a', jfy([
            {
                'module': 'Sifen',
                'package': 'mng_sifen',
                'attr': 'MSifen',
                'mname': 'create_documentheader',
                'cont': false,
                'show_success': true
            },
        ]));
        fdata.append('a_vals', jfy([
            {
                'module': 'Sifen',
                'package': 'mng_sifen',
                'attr': 'MSifen',
                'mname': 'inform_client',
                'cont': false, //Irrelevante por que ya se ejecuto a_vals y c_a
                'show_success': true
            },
        ]));
        axios.post(
            '{% url "iom" %}',
            fdata,
            { headers: {
                'X-CSRFToken': OptsIO.getCookie('csrftoken')
                }
            })
        .then((rsp)=>{
            msgs = rsp.data.msgs;
        ...
 ## Directo
        let fdata = new FormData();
        fdata.append('module', 'Sifen');
        fdata.append('package', 'mng_sifen');
        fdata.append('attr', 'MSifen');
        fdata.append('mname', 'validate_ruc');
        fdata.append('ruc', ruc);

        axios.post(
            '{% url "iom" %}',
            fdata,
            { headers: {
                'X-CSRFToken': OptsIO.getCookie('csrftoken')
                }
            })
        .then((rsp)=>{
            rdata = rsp.data;
        ...