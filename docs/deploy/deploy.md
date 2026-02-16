### Implementacion deployment

-  Revisar el script /home/peter/projects/Amachine/deployment/deploy.sh y actualizarlo para

- Opciones para el script.
   * --user el usuario en el cual se va a realizar la instalacion del sistema (usualmente con acceso sudo, si es que no se utiliza --docker)
   * --server Especifica a que servidor se va a realizar el deploy, que seria un parametro a pasar al github actions
   * --branch Especificar que branch es el que se va a deployar en el servidor mediante git pull
   * --docker Si se especifica esto se hace el deploy en una imagen docker, sino se especifica es nativo, ya que el hardware puede ser limitado.
   * --dominio El dominio el cual se utilizara para configurar let's encrypt
   * --virtualenv Amachine 3.13.0 ( el virtualenv a configurar en el servidor remoto, acompanhado de la version python, mediante pyenv)
   * --env si se especifica este es el path del archivo a utilizar como .env en la raiz del proyecto.
   * --bind_port_gunicorn si se especifica en que puerto va a escuchar el servicio gunicorn, por defecto 8010
   * --bind_port_nginx si se especifica en que puerto hay que configurar la escucha de nginx
   * --prefix_services_names si se especifica el prefijo de los nombres para los archivos y servicios a guardarse en /etc/systemd/system, por defecto prefijo altamachines
   * --migrations si se especifica el script debera correr python manage.py makemigrations y luego python manage.py migrate en el servidor
      
       

Ejemplos.

  deploy.sh --github_action deploy_remote_server \
            --server 165.227.53.87 \
            --user am --branch develop \
            --dominio fl.altamachines.com \
            --virtualenv Amachine --env /home/peter/projects/Amachine/.env_fl \
            --bind_port_gunicorn 8010 \
            --prefix_services_names fl_am \
            --bind_port_nginx 8000

Descripcion del workflow.

   El proceso de deployment ingresa al servidor 165.227.53.87

   Segun la carpeta del proyecto local, crea la misma estructura en el servidor bajo el usuario correspondiente --user 

   Si en local es /home/peter/projects/Amachine, en el servidor es /home/am/projects/Amachine

   Una vez adentro verificar que todas las dependencias esteen instaladas para realizar el deploy.

    * Dependencias
     pyenv, librerias python escenciales, nginx, cerbot, base de datos, redis, memcahed ...etc
    * Instalar la version correspondiente de python para crear el virtualenv
    * Configurar .python-version (con el nombre del virtualenv) dentro del directorio del proyecto para el cambio automatico al virtualenv al entrar al mismo
    * Subir el archivo .env si se especifico --env
    * Ir a la carpeta del proyecto /home/am/projects/Amachine/ y realizar el pull correspondiente del branch especificado en --branch
    * Correr pip install -r requirements.txt
       - Verificar si hay dependencias de la distribucion misma a ser instaladas
    * Ver si la base de datos ya esta creada y el usuario especificado el el .env creado con la clave corresopndiente, segun las variables.
            DB_NAME
            DB_USER
            DB_PASSWORD
            DB_HOST
            DB_PORT
    * Crear los archivos systemctl correspondientes (ver especificacion de --bind_port_gunicorn y --prefix_services_names).
       fl_am.service servicio gunicorn principal (Los workers deben ser configuradas segun el hardware del servidor)
       fl_am_celery.service servicio celery
       fl_am_flower.service celery flower, para tener un monitoreo de tareas ejecutadas
       fl_am_daphne.service, para levantar el servicio del websocket
    * Verificar y levantar los servicios y ver si todo esta corriendo bien.


Lo has entendido ? 