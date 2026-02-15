# Amachine - Contexto del proyecto

## Descripción General
Sistema ERP para la empresa Amachine, basado en endpoints reutilizables y que generan contenido o acciones en referencia a los parámetros que se les pasa.

## Consideraciones generales
   Estos puntos son vitables para empezar cualquier proyecto

   Lee todos los archivos .md dentro .claude/ la lectura de los .md dentro de .claude/ debe ser lenta y exhaustiva, aqui esta el disenho de la base estructural del proyecto, asi que cada descripcion de directris definida ahi es crucial que la entiendas y debes de leer todos los archivos .md, sin pasarte por alto ninguno


   1. Ser explícito con verificación:
      - "Lee TODOS los .md en .claude/. Antes de continuar, lista los archivos que leíste."
      - "Confirma que leíste los X archivos antes de proceder"
   2. Pedir confirmación de completitud:
      - "Primero usa Glob o find ./claude/ -name "*.md" -ls para listar todos los .md, luego lee cada uno"
   4. Consecuencia explícita:
      - "Si empiezas sin leer todo, el código estará mal y tendrás que rehacerlo"

## Descripción de endpoints.

La app que maneja los endpoints es OptsIo.
   'set_auth/' = Autentifica a un usuario
   'set_logout/' = Deslogueo a un usuario
   'iom/' = Ejecuta un método dentro de todo todo el proyecto, se define que método se ejecuta según la parametrización recibida desde el FrontEnd, a su vez se puede llamar a llamadas Celery.
   'dtmpl/' = Renderiza los templates de las Apps, puede recibir un registro (instancia de un modelo para ser usada dentro del tempalte como mobj), así como otros parámetros o lógicas
   'api_dtmpl/' = Mismo que dtmpl/ pero acceso vía token
   'api_iom/' = Mismo que iom/ pero acceso vía token
   'api_isauth/' = Utilización en modo token para ver si el usuario por token está autentificado o no
   'api_refresh/' = Utilización en modo token para refrescar el token
   'glogin/' = Interfaz para realizar login al sistema
   'glogout/' = Salir del sistema
    show_media_file/(?P<filename>[0-9\w|\/\.\-]+) = Acceso a archivos generados por el sistema

## Directrices

   - El proyecto usa axios, no uses fetch
   - Muestra el path completo del archivo que vas a editar o crear
   - **URLs Django**: Usar SIEMPRE la convención de Django para URLs en templates:
     - En HTML: `{% url 'nombre_vista' %}`
     - En JavaScript: Pasar la URL via data attribute o action del formulario, ejemplo:
       ```html
       <form id="myForm" action="{% url 'mi_vista' %}" data-other-url="{% url 'otra_vista' %}">
       ```
       ```javascript
       const formUrl = document.getElementById('myForm').action;
       const otherUrl = document.getElementById('myForm').dataset.otherUrl;
       ```
     - NUNCA hardcodear URLs como `/setup/step2/` o `/glogin/`
     - Bajo ningun motivo debes cambiar el comportamiento del sistema cuando creas crud genericos basado en /home/peter/projects/Amachine/.claude/crud_patterm.md, a no ser que sea explicitamente dicho por el que hace el prompt.

## Nombre de archivos.
  - Para la creacion de los modulos se uso el prefijo mng_ luego con la accion o conjunto de acciones que representa y/o maneja ese modulo.
      * mng_apps.py
      * mng_sifen.py
      * ...etc
  - Para los .html siempre terminar con el sufijo Ui justo antes de la extension .html
      * UserProfileUi.html
      * RoleUi.html
      * ...etc


## CRÍTICO: Verificación Antes de Codificar
  **ANTES de escribir CUALQUIER código, DEBES:**
  1. **Leer la documentación de .claude** para la funcionalidad específica que estás implementando
     - `.claude/record_from_backend.md` - para recuperación de datos del backend (seModel)
     - `.claude/crud_patterm.md` - para operaciones CRUD, uso de OptsIO.getTmpl, patrones de formularios
     - `.claude/form_ui.md` - para patrones de elementos de formulario
     - `.claude/table_ui.md` - para patrones de tablas/grids
     - `.claude/javascript_methods.md` - para todos los métodos JavaScript disponibles (OptsIO, UiB, Form, etc.)
  2. **Verificar que los métodos/funciones existen** antes de usarlos:
     - Revisar `.claude/javascript_methods.md` PRIMERO para métodos JavaScript
     - Usar `Grep` para buscar el método/función en el código
     - NUNCA inventar o asumir que existen métodos (como `OptsIO.generateRandomString()`)
  3. **Seguir los patrones existentes** - SIEMPRE mirar las implementaciones de referencia:
     - **Formularios con guardado**: `templates/OptsIO/MenuCreateUi.html` - Referencia para envío de formularios, manejo de mensajes, cierre de offcanvas
     - **Uso de seModel**: `.claude/record_from_backend.md` - Cómo consultar modelos desde el frontend
     - **se_populate/se_select**: `.claude/form_ui.md` - Cómo poblar elementos select
  4. **Verificar la estructura del modelo** antes de filtrar:
     - Leer el archivo del modelo para entender las relaciones
     - Verificar campos ForeignKey y sus nombres
     - No asumir cadenas de relaciones (ej., UserProfile tiene username CharField, NO FK a User)
  5. **Preguntar al usuario** si no estás seguro sobre:
     - Qué método usar
     - Cómo llamar a una función específica
     - Si algo existe en el código
     - Relaciones de modelos o nombres de campos

## Directrices de Calidad de Código
  - SIEMPRE revisar el archivo completo antes de intentar editar, quizás un import ya está declarado o una lógica ya está implementada.
  - **Imports SIEMPRE al inicio del archivo** - NUNCA hacer imports dentro de métodos o funciones. Todos los imports deben estar en la parte superior del archivo.
  - No crear diccionarios intermedios cuando se pueden acceder directamente a los atributos del objeto
  - Leer el contexto COMPLETO de un archivo antes de modificarlo
  - NUNCA inventar métodos o funciones JavaScript - verificar que existen primero
  - NUNCA asumir sintaxis - revisar la documentación en `.claude/` primero


