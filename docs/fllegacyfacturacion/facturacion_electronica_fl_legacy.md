Ahora como primer plugin hay que crear un modulo especifico para que un cliente lo use.

El plugin debe de llamarse "FLFacturacionLegacy"


Para esto debes de leer el proyecto (y las documentaciones del mismo) en /home/peter/projects/frontlinerSistema.

Base de datos = mysql 

Nombre = frontlin_db

 Este sistema tiene un flujo de facturacion el cual es el siguiente.

 Mediante esta interfaz (http://localhost:81/Paquete/entregar.php)

 El usuario busca los paquetes a entregar por cliente, los selecciona y da al boton "Generar ticket"

  * /home/peter/projects/Amachine/docs/fllegacyfacturacion/entregar_paquete.png

 Esto genera un acuse de recibo que se puede ver en. 
   
  * http://localhost:81/administrar_facturas.php
  * /home/peter/projects/Amachine/docs/fllegacyfacturacion/administrar_facturas.png

 Luego cargando el cliente o el acuse de recibo en 
  * http://localhost:81/facturar.php
  * /home/peter/projects/Amachine/docs/fllegacyfacturacion/facturar.png

 El usuario carga el pago del cliente ya sea.

   * Efectivo, Tarjeta de credito, Tarjeta Debito, Cheque.

 Luego da al boton "Confirmar Pago/Entrega", luego de sale el mensaje.

   * /home/peter/projects/Amachine/docs/fllegacyfacturacion/confirmar_facturar.png

 Luego el usuario carga "Factura Nro." y da al boton "Factura" y se abre un invoice a imprimir.

 Toda esta parte debe ser aplicada (replicada) en el plugin, pero con la diferencia de al momento de facturar no se debe de cargar manualmente el numero de factura, sino que debe de traerse automatico y se debe utilizar los metodos de creacion y generacion de factura de mng_sifen.

 Es decir el proceso debe ser igual al de shopify, pero obviamente muchiso mas simple.

 Obs: Los metodos de mng_sifen no deben de ser alterados.

Si lo haz entendido, dame la explicacion de lo que hay que hacer.