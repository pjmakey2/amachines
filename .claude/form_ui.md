# Documentación de Form UI

Leer  /home/peter/projects/Amachine/static/amui/form_ui.js y repasar cada parametros para saber como funciona cada metodo de este archivo.

## form_serials = Serialización de formularios
    get_form_fields: Obtiene el atributo name de los campos del formulario
    form_to_json: Obtiene el name y value de los campos del formulario en un objeto json
    form_files: Obtiene los archivos del formulario en un array
    form_from_json: Convierte una estructura json a un formulario html
    base64_to_binary: Convierte imágenes b64 a objetos File
    form_empty_localStorage: remueve un item del localStorage,
    form_to_localStorage: Guarda datos del formulario en localStorage,
    form_from_localStorage: Carga datos del formulario desde localStorage

## form_search = Buscar y poblar tipos select desde el backend
    ### se_select Método para crear un select2 para buscar su contenido desde una llamada ajax al backend
        surl = URL al servicio backend, siempre iom
        dele = Selector del elemento select
        app_name = Nombre de la app del modelo a consultar
        model_name = Nombre del modelo a consultar
        field_display = Lo que el usuario vería en el dropdown del select (las opciones),
        field_id = Cuál de los campos se consideraría como el id de la opción,
                   Nota que esto es un array
        db_fields = Lista de campos a recuperar del modelo,
        db_methods = Lista de métodos a recuperar del modelo,
        qs_be = Query inicial para filtrar los resultados, esto se adjuntará a los parámetros de búsqueda,
        sterm = Lista de campos donde buscar lo que el usuario escribe,
        theme = Tema a usar,
        ml = Longitud mínima para empezar a buscar,
        multiple = Si el select2 es múltiple,
        dbcon = Qué conexión de base de datos usar,
        dejoin = Si hay más de un campo del modelo para mostrar, este sería el concatenador,
        round_v = Si cada campo del modelo que se mostrará necesita ser rodeado por lo que se especifica aquí, ejemplo: round_v = ['(', ')'],
        templateResult = Método personalizado para mostrar el resultado,
        templateSelection = Método personalizado para mostrar lo seleccionado,
        width = ancho del elemento,
        allowClear = Si el usuario puede limpiar la selección,
        placeholder = Placeholder a mostrar,
        distinct = Método distinct a aplicar a la lista de items especificados aquí,
        headers = Headers a adjuntar a la llamada ajax, siempre tenemos que pasar el header csrf
                  'X-CSRFToken': OptsIO.getCookie('csrftoken')
        dropdownParent = Si renderizas el select2 en un modal, necesitas especificar el elemento padre aquí,
        sort = Opciones de ordenamiento a aplicar al queryset,
               Ejemplo: sort: [
                  {'dataIndx': 'codigo', 'dir': 'up'},
                ],
        specific_search = Define un método personalizado para hacer la búsqueda en el backend,
                   Ejemplo: specific_search: {
                        'module': 'apps.ReceptionPackages',
                        'package': 'mng_packages',
                        'attr': 'MPackages',
                        'mname': 'search_client',
                    }

        clean = Si el select se limpiará antes de poblar,
    ### se_populate Método para crear un select2 desde una llamada ajax al backend, esto no es una búsqueda ajax, sino un poblado ajax
        surl = URL al servicio backend, siempre iom
        dele = Selector del elemento select
        app_name = Nombre de la app del modelo a consultar
        model_name = Nombre del modelo a consultar
        field_display = Lo que el usuario vería en el dropdown del select (las opciones),
        field_id = Cuál de los campos se consideraría como el id de la opción,
                   Nota que esto es un array
        db_fields = Lista de campos a recuperar del modelo,
        db_methods = Lista de métodos a recuperar del modelo,
        qs_be = Query inicial para filtrar los resultados, esto se adjuntará a los parámetros de búsqueda,
        qexc = Objeto en formato para pasar al método .exclude del queryset,
                Ejemplo: qexc = {'anulado': true }
        theme = Tema a usar,
        ml = Longitud mínima para empezar a buscar,
        multiple = Si el select2 es múltiple,
        dbcon = Qué conexión de base de datos usar,
        dejoin_id = Si definimos múltiples ids este sería el concatenador,
        dejoin = Si hay más de un campo del modelo para mostrar, este sería el concatenador,
        round_v = Si cada campo del modelo que se mostrará necesita ser rodeado por lo que se especifica aquí, ejemplo: round_v = ['(', ')'],
        templateResult = Método personalizado para mostrar el resultado,
        templateSelection = Método personalizado para mostrar lo seleccionado,
        createTag = Permitir tags en el select2,
        width = ancho del elemento,
        allowClear = Si el usuario puede limpiar la selección,
        clean = Si el select se limpiará antes de poblar,
        distinct = Método distinct a aplicar a la lista de items especificados aquí,
        sort = Opciones de ordenamiento a aplicar al queryset,
               Ejemplo: sort: [
                  {'dataIndx': 'codigo', 'dir': 'up'},
                ],
        headers = Headers a adjuntar a la llamada ajax, siempre tenemos que pasar el header csrf
                  'X-CSRFToken': OptsIO.getCookie('csrftoken')
        init_select2 = Si el elemento select se inicializaría como instancia select2,
        on_focusopen = Si el select2 se abriría al hacer focus,
        dropdownParent = Si renderizas el select2 en un modal, necesitas especificar el elemento padre aquí,
        dropdownCssClass = Clase css personalizada para el dropdown,
        containerCssClass = Clase css personalizada para el contenedor,
        closeOnSelect = Si el select2 se cerraría cuando se selecciona una opción,
        dropdownAutoWidth = Define si el dropdown tendría ancho automático,
        first_selected = Si la primera opción se seleccionaría automáticamente,
        focus_after_selected = Hacer focus de nuevo en el elemento después de la selección,
        type_after_selected = Qué tipo de elemento si es select convencional o select2,
        initialize_empty = Inicializar el elemento sin una opción seleccionada,
        startRow = Inicio del índice de registro a recuperar del backend,
        endRow = Cuántos registros recuperar del backend,
        tags = Permitir tags en el select2,
        check_cache = Si el registro vendría primero del caché,
        specific_populate = Define un método personalizado para hacer el poblado en el backend,
                   Ejemplo: specific_populate: {
                        'module': 'apps.ReceptionPackages',
                        'package': 'mng_packages',
                        'attr': 'MPackages',
                        'mname': 'search_client',
                    }
    ### search_select_multiple Crea un select múltiple convencional con capacidades de búsqueda
        sel = selector del select
        iel = input que se usaría como caja de búsqueda
        bel = si alguna opción tiene que estar deshabilitada,
        search_attr = Qué tipo de data-attribute buscar en las opciones


## form_ui = Generación y controles de formulario
    ### generate_bs5: Genera un formulario bootstrap 5 desde una estructura json
    ### set_readonly: Pone el formulario en modo solo lectura

### form_select características para elementos select
    ### clear_select2: Limpia todas las opciones de un elemento select2
    ### remove_option_value: Remueve una opción de un elemento select por su valor

### form_input características para elementos input
    ### on_enter_func: Previene enviar un formulario cuando se presiona enter en un campo input, en su lugar llama una función personalizada
    calculate_dv: Calcula un dígito verificador para un número dado
}

### form_validation características para validación de formularios
    ### just_number: Permite solo números con hasta tres decimales
    ### just_number_integer: Permite solo números enteros
    ### justNumberAndLetters: Solo números y letras de a-z y A-Z
    ### justLetters: Permite solo letras de a-z y A-Z
    ### password_strengthp: Evalúa la fortaleza de una contraseña
}

### form_controls Controles específicos de formulario
    ### filter_date_range: Librería de date picker para aplicar a un elemento input
