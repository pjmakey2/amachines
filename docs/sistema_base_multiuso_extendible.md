Este debe ser un proyecto que se puede usar segun el cliente.

Es decir quiero crear un sistema el cual tenga por defecto.

 * El setup (que ya lo estas haciendo ahora)
 * Configuracion inicial del negocio.
    Para los Modelos ya existe el archivo /home/peter/projects/Amachine/Sifen/rf/CODIGO DE REFERENCIA GEOGRAFICA.xlsx y un mainline para popular los mismos ( Pero esos se deben de ponder ver o hacer desde el setup, despues de configurar la base de datos ).n
       * Geografias(models.Model):
       * AreasPoliticas(models.Model):
       * Paises(models.Model):
       * Departamentos(models.Model):
       * Distrito(models.Model):
       * Ciudades(models.Model):
       * Barrios(models.Model):
    Mismo caso para desde /home/peter/projects/Amachine/Sifen/rf/actividades_economicas_utf8.csv
        * ActividadEconomica(models.Model):
    Para el siguiente este es 1 = Fisica 2 = Juridica
        class TipoContribuyente(models.Model):
    Esto ya lo debe llenar el usuario
        class Business(models.Model):
    El seguiiente popular mediante el proceso de lectura de clientes        
        class Clientes(models.Model):
        class Categoria(models.Model):
        class Marca(models.Model):
        class Medida(models.Model):
        class PorcentajeIva(models.Model):
        class Producto(models.Model):
        class MetodosPago(models.Model):

    Fijamete bien en (mng_sifen_mainline.py) mng_sifen.py  para ver que procesos ya actualizan ciertos modelos y mostrar el proceso de actualizacion mediante el setup.

    Tal vez el proceso de sync_rucs, debe ser un proceso que corra por celery, y se muestra el avance mediante un websocket ya que puede llegar a tardar un poco.


        
Y siguiendo la linea que este debe ser un proyecto que tenga como base unos modulos y se adapte segun el cliente, si es que no le es suficiente los modulos bases, que me recomiendas ? 

* Actualizar el sistema mediante un mecanismo de plugins ? 
   Si es asi como se harian las customizaciones ?
* Crear una rama por cada cliente ? 
* Crear el sistema como un proyecto nuevo a parte por cada cliente ? 
    Si es asi como se harian las customizaciones ?

Como se suele proceder usualmente en este tipo de casos ? 