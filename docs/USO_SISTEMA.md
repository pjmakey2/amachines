# Manual de Usuario - Sistema de Facturación Electrónica

**Versión 1.0**
**Fecha: Noviembre 2025**

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [SIFEN - Facturación Electrónica](#sifen---facturación-electrónica)
   - [Facturar](#facturar)
   - [Notas de Crédito](#notas-de-crédito)
   - [Timbrados](#timbrados)
   - [Establecimientos](#establecimientos)
   - [Numeración](#numeración)
   - [Crear Timbrado](#crear-timbrado)
   - [Gestión de Números](#gestión-de-números)
   - [Actividades Económicas](#actividades-económicas)
   - [Tipos de Contribuyente](#tipos-de-contribuyente)
3. [Maestros](#maestros)
   - [Categorías](#categorías)
   - [Marcas](#marcas)
   - [Porcentajes IVA](#porcentajes-iva)
   - [Productos](#productos)
4. [Perfil de Usuario](#perfil-de-usuario)
   - [Perfil](#perfil)
   - [Negocios](#negocios)
   - [Editar Negocio Activo](#editar-negocio-activo)
5. [Sistema](#sistema)
   - [Configuración de Negocio](#configuración-de-negocio)

---

## Introducción

Este manual describe el uso del Sistema de Facturación Electrónica integrado con SIFEN (Sistema Integrado de Facturación Electrónica Nacional) de Paraguay. El sistema permite la emisión de facturas electrónicas, notas de crédito, gestión de productos y configuración de negocios.

---

## SIFEN - Facturación Electrónica

### Facturar

La interfaz de facturación permite crear documentos electrónicos (facturas) que serán enviados a SIFEN para su validación y aprobación.

**Acceso:** Menu SIFEN > Facturar

**Funcionalidades principales:**
- **Crear nueva factura:** Hacer clic en el botón "Crear" para iniciar una nueva factura
- **Selección de cliente:** Buscar y seleccionar el cliente o crear uno innominado
- **Agregar productos:**
  - Buscar productos desde el catálogo del sistema
  - Agregar productos manuales (tags) con descripción personalizada
- **Distribución tributaria:** Para cada producto se distribuye el monto entre:
  - Exenta (0%)
  - Gravada 5% (con IVA 5%)
  - Gravada 10% (con IVA 10%)
- **Campos del documento:**
  - Tipo de documento (FE - Factura Electrónica)
  - Moneda (Guaraníes o Dólares)
  - Fecha de emisión
  - Condición de venta (Contado/Crédito)
  - Medio de pago
- **Tabla de detalles:** Muestra todos los productos agregados con sus totales
- **Totales del documento:**
  - Subtotal Exenta
  - Subtotal Gravada 5%
  - IVA 5%
  - Subtotal Gravada 10%
  - IVA 10%
  - Total a pagar

**Proceso de emisión:**
1. Completar datos del cliente
2. Agregar productos al detalle
3. Distribuir montos tributarios
4. Verificar totales
5. Guardar el documento
6. El sistema envía automáticamente a SIFEN
7. Esperar aprobación de SIFEN
8. Descargar e imprimir el documento aprobado

**Estados del documento:**
- **Pendiente:** Recién creado, no enviado a SIFEN
- **Aprobado:** Validado y aprobado por SIFEN (color verde)
- **Rechazado:** Rechazado por SIFEN (color naranja)
- **Inutilizado:** Documento anulado (color beige)

---

### Notas de Crédito

Las notas de crédito se utilizan para anular total o parcialmente una factura electrónica previamente emitida.

**Acceso:** Menu SIFEN > Notas de Crédito

**Funcionalidades principales:**
- **Crear nota de crédito:** Botón "Crear"
- **Seleccionar factura a anular:** Se debe referenciar la factura original
- **Agregar detalles:** Similar al proceso de facturación
- **Distribución tributaria:** Mismo proceso que en facturación
- **Motivo de anulación:** Describir la razón de la nota de crédito

**Importante:**
- Una nota de crédito debe referenciar siempre a una factura aprobada
- El monto de la NC no puede exceder el monto de la factura original
- La distribución tributaria debe coincidir con la factura original

---

### Timbrados

El timbrado es la autorización otorgada por la SET (Subsecretaría de Estado de Tributación) para emitir documentos fiscales electrónicos.

**Acceso:** Menu SIFEN > Timbrados

**Funcionalidades principales:**
- **Listar timbrados:** Visualizar todos los timbrados registrados
- **Ver detalles:** Hacer clic en el ícono de ojo para ver información completa
- **Crear timbrado:** Botón "Crear"
- **Borrar timbrado:** Seleccionar y hacer clic en "Borrar"
- **Buscar:** Campo de búsqueda rápida

**Campos del timbrado:**
- Número de timbrado (otorgado por SET)
- Establecimiento asociado
- Fecha de inicio de vigencia
- Fecha de fin de vigencia
- Estado (Activo/Inactivo)

---

### Establecimientos

Gestión de establecimientos físicos o puntos de emisión de la empresa.

**Acceso:** Menu SIFEN > Establecimientos

**Funcionalidades principales:**
- **Crear establecimiento:** Botón "Crear"
- **Editar:** Hacer clic en el ícono de ojo
- **Eliminar:** Seleccionar y usar botón "Borrar"

**Datos del establecimiento:**
- Código de establecimiento (3 dígitos)
- Denominación
- Dirección
- Teléfono
- Email
- Estado (Activo/Inactivo)

---

### Numeración

Gestión de puntos de expedición dentro de cada establecimiento.

**Acceso:** Menu SIFEN > Numeración

**Funcionalidades principales:**
- **Crear punto de expedición:** Botón "Crear"
- **Asignar numeración:** Definir rangos de numeración
- **Estado:** Activar/desactivar puntos

**Datos de numeración:**
- Establecimiento
- Punto de expedición (3 dígitos)
- Número actual
- Número final del rango
- Tipo de documento asociado

---

### Crear Timbrado

Interfaz dedicada para la creación rápida de timbrados.

**Acceso:** Menu SIFEN > Crear Timbrado

**Proceso:**
1. Ingresar número de timbrado (proporcionado por SET)
2. Seleccionar establecimiento
3. Definir fecha de inicio
4. Definir fecha de vencimiento
5. Guardar

**Validaciones:**
- El número de timbrado debe ser único
- Las fechas deben ser coherentes (inicio < fin)
- Debe estar asociado a un establecimiento existente

---

### Gestión de Números

Control detallado de la numeración de documentos por establecimiento y punto de expedición.

**Acceso:** Menu SIFEN > Gestión Números

**Funcionalidades:**
- Visualizar numeración actual
- Modificar rangos
- Reiniciar numeración (con precaución)
- Asociar timbrados a numeración

---

### Actividades Económicas

Catálogo de actividades económicas según clasificación de la SET.

**Acceso:** Menu SIFEN > Actividades Económicas

**Funcionalidades principales:**
- **Listar actividades:** Ver todas las actividades registradas
- **Crear actividad:** Botón "Crear"
- **Editar:** Modificar actividades existentes
- **Buscar:** Por código o descripción

**Datos de actividad económica:**
- Código de actividad
- Descripción
- Estado (Activo/Inactivo)

---

### Tipos de Contribuyente

Clasificación de tipos de contribuyentes según normativa tributaria paraguaya.

**Acceso:** Menu SIFEN > Tipos de Contribuyente

**Tipos comunes:**
- Persona física
- Persona jurídica
- Empresa unipersonal
- Entidad sin fines de lucro

**Funcionalidades:**
- Listar tipos
- Crear nuevo tipo
- Editar existentes
- Activar/desactivar

---

## Maestros

### Categorías

Organización de productos por categorías para mejor gestión del inventario.

**Acceso:** Menu MAESTROS > Categorías

**Funcionalidades principales:**
- **Crear categoría:** Botón "Crear"
- **Editar:** Hacer clic en el ícono de ojo
- **Eliminar:** Seleccionar y usar botón "Borrar"
- **Buscar:** Campo de búsqueda por nombre o descripción

**Campos:**
- Nombre de la categoría
- Descripción
- Estado (Activo/Inactivo)

**Uso:**
Las categorías se utilizan para agrupar productos relacionados, facilitando:
- Búsquedas rápidas
- Reportes por categoría
- Organización del catálogo

---

### Marcas

Gestión de marcas de productos.

**Acceso:** Menu MAESTROS > Marcas

**Funcionalidades principales:**
- **Crear marca:** Botón "Crear"
- **Editar:** Ícono de ojo
- **Eliminar:** Seleccionar y "Borrar"
- **Buscar:** Por nombre o descripción

**Campos:**
- Nombre de la marca
- Descripción
- Estado (Activo/Inactivo)

---

### Porcentajes IVA

Configuración de los porcentajes de IVA aplicables a los productos.

**Acceso:** Menu MAESTROS > Porcentajes IVA

**Porcentajes estándar en Paraguay:**
- 0% - Exenta
- 5% - IVA reducido
- 10% - IVA general

**Funcionalidades:**
- Visualizar porcentajes disponibles
- Crear nuevos porcentajes (si es necesario)
- Editar descripciones
- Activar/desactivar

**Campos:**
- Porcentaje (número)
- Descripción
- Estado (Activo/Inactivo)

---

### Productos

Catálogo completo de productos y servicios que comercializa la empresa.

**Acceso:** Menu MAESTROS > Productos

**Funcionalidades principales:**
- **Crear producto:** Botón "Crear"
- **Ver/Editar:** Hacer clic en el ícono de ojo
- **Eliminar:** Seleccionar productos y usar botón "Borrar"
- **Buscar:** Por código, descripción o código de barras (EAN)

**Tabla de productos:**
Muestra las siguientes columnas:
- **Foto:** Imagen del producto (si existe)
- **Código:** Código interno del producto
- **Descripción:** Nombre del producto
- **Precio:** Precio unitario con moneda
- **Categoría:** Categoría asignada
- **Marca:** Marca del producto
- **Stock:** Cantidad disponible
- **Activo:** Estado del producto (Sí/No)

**Formulario de producto:**
- Código de producto
- Código de barras (EAN)
- Descripción
- Precio unitario
- Moneda (Guaraníes/Dólares)
- Porcentaje de IVA
- Categoría
- Marca
- Stock inicial
- Unidad de medida
- Foto del producto (opcional)
- Estado (Activo/Inactivo)

**Gestión de fotos:**
- Se pueden cargar imágenes en formatos: JPG, PNG, GIF
- Tamaño máximo: 5MB
- Vista previa automática al seleccionar imagen
- Las fotos se muestran en la grilla principal

---

## Perfil de Usuario

### Perfil

Gestión de la información personal del usuario del sistema.

**Acceso:** Menu PERFIL DE USUARIO > Perfil

**Información del perfil:**
- Nombre de usuario
- Nombre completo
- Email
- Foto de perfil
- Configuraciones personales

**Funcionalidades:**
- Actualizar información personal
- Cambiar foto de perfil
- Modificar contraseña
- Configurar preferencias

**Nota:** La foto de perfil se muestra en el toolbar superior del sistema.

---

### Negocios

Gestión de negocios asociados al usuario. Un usuario puede tener acceso a múltiples negocios.

**Acceso:** Menu PERFIL DE USUARIO > Negocios

**Funcionalidades principales:**
- **Ver negocios asignados:** Lista de todos los negocios a los que tiene acceso
- **Asignar nuevo negocio:** Asociar el usuario a un negocio adicional
- **Cambiar negocio activo:** Seleccionar con cuál negocio trabajar
- **Ver detalles:** Información completa del negocio

**Información de negocio:**
- Nombre del negocio
- RUC
- Razón social
- Dirección
- Teléfono
- Email
- Estado (Activo/Inactivo)

**Negocio activo:**
- Solo un negocio puede estar activo a la vez
- Todas las operaciones se realizan en el contexto del negocio activo
- El cambio de negocio activo afecta inmediatamente al sistema

---

### Editar Negocio Activo

Modificación rápida de la información del negocio con el que se está trabajando actualmente.

**Acceso:** Menu PERFIL DE USUARIO > Editar Negocio Activo

**Datos editables:**
- Nombre comercial
- Razón social
- RUC (solo lectura)
- Dirección
- Teléfono
- Email
- Logo del negocio
- Configuraciones de facturación
- Certificado digital (para SIFEN)

**Importante:**
- Los cambios afectan inmediatamente a la facturación
- El RUC no puede modificarse (dato fiscal)
- El certificado digital debe estar vigente para emitir documentos

---

## Sistema

### Configuración de Negocio

Configuraciones globales y parámetros del negocio para el correcto funcionamiento del sistema.

**Acceso:** Menu SISTEMA > Configuración de Negocio

**Secciones de configuración:**

#### 1. Datos Generales
- Nombre del negocio
- RUC
- Razón social
- Dirección fiscal
- Teléfono
- Email
- Sitio web

#### 2. Configuración SIFEN
- URL del servicio SIFEN (Producción/Testing)
- Certificado digital (.pfx)
- Contraseña del certificado
- ID CSC (Código de Seguridad del Contribuyente)
- Modo de operación (Test/Producción)

#### 3. Configuración de Facturación
- Serie de documentos por defecto
- Establecimiento por defecto
- Punto de expedición por defecto
- Moneda principal
- Tipo de cambio (si usa múltiples monedas)
- Redondeo de totales

#### 4. Configuración de Impresión
- Formato de impresión (A4, Ticket, etc.)
- Mostrar logo en documentos
- Pie de página personalizado
- Número de copias por defecto

#### 5. Notificaciones
- Email para notificaciones
- Alertas de vencimiento de timbrados
- Notificaciones de rechazo de documentos
- Alertas de stock bajo

**Validaciones importantes:**
- El certificado digital debe estar vigente
- La URL de SIFEN debe ser correcta según el ambiente (Test/Producción)
- El ID CSC debe coincidir con el proporcionado por SET

---

## Flujo de Trabajo Recomendado

### Configuración inicial (Primera vez)
1. Configurar datos del negocio (SISTEMA > Configuración)
2. Cargar certificado digital SIFEN
3. Crear establecimientos
4. Crear puntos de expedición
5. Cargar timbrados vigentes
6. Configurar actividades económicas
7. Crear categorías de productos
8. Crear marcas
9. Cargar productos

### Operación diaria
1. Seleccionar negocio activo (si tiene múltiples negocios)
2. Crear facturas según ventas
3. Verificar aprobación de SIFEN
4. Imprimir/enviar documentos aprobados
5. Crear notas de crédito si es necesario
6. Actualizar stock de productos

### Mantenimiento periódico
- Verificar vigencia de timbrados
- Actualizar precios de productos
- Renovar certificado digital antes de vencimiento
- Revisar numeración de documentos
- Actualizar información de clientes

---

## Preguntas Frecuentes

**¿Qué hago si SIFEN rechaza un documento?**
- Revisar el motivo del rechazo en el mensaje de error
- Verificar datos del cliente (RUC, nombre)
- Verificar distribución tributaria
- Corregir y reenviar

**¿Puedo eliminar una factura aprobada?**
- No. Una factura aprobada por SIFEN no puede eliminarse
- Debe emitirse una Nota de Crédito para anularla

**¿Cómo cambio de negocio activo?**
- Ir a PERFIL DE USUARIO > Negocios
- Seleccionar el negocio deseado
- Hacer clic en "Activar"

**¿Qué hago si se vence un timbrado?**
- Solicitar nuevo timbrado a la SET
- Cargar el nuevo timbrado en SIFEN > Crear Timbrado
- Asociarlo al establecimiento correspondiente

**¿Puedo usar el sistema sin conexión a internet?**
- No. El sistema requiere conexión para validar con SIFEN
- Los documentos deben enviarse a SIFEN para su aprobación

---

## Soporte Técnico

Para asistencia técnica o reportar problemas:
- Email: soporte@sistema.com
- Teléfono: +595 XXX XXXXXX
- Horario: Lunes a Viernes, 8:00 - 18:00

---

**Fin del Manual de Usuario**

*Este documento está sujeto a actualizaciones según evolucione el sistema.*
