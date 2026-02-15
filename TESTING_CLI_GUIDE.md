# Guía de Testing CLI para Sifen

Esta guía explica cómo testear los métodos de Sifen directamente desde la línea de comandos sin necesidad de usar el frontend.

## Scripts disponibles

### 1. `test_sifen_pdf.py` - Generar PDF de documento existente

Toma un documento existente y genera su PDF/HTML/QR.

```bash
python manage.py shell < test_sifen_pdf.py
```

**Qué hace:**
- Lista los primeros 5 documentos en la BD
- Selecciona el primero
- Llama a `generando_documentheader()`
- Genera PDF, HTML y QR
- Muestra las rutas de los archivos generados

### 2. `test_create_document.py` - Crear documento FE completo

Crea un documento de tipo Factura Electrónica (FE) desde cero.

```bash
python manage.py shell < test_create_document.py
```

**Qué hace:**
- Crea un documento FE con datos de prueba
- Llama a `create_documentheader()`
- Genera automáticamente el PDF
- Muestra todos los detalles del documento creado

### 3. `test_create_nc.py` - Crear Nota de Crédito (NC)

Crea una Nota de Crédito referenciando una factura existente.

```bash
python manage.py shell < test_create_nc.py
```

**Qué hace:**
- Busca una factura aprobada (FE)
- Crea una NC referenciando esa factura
- Genera el PDF de la NC
- Muestra la relación entre NC y factura

## Uso interactivo (Django Shell)

Para un control más fino, puedes usar el shell de Django de forma interactiva:

```bash
python manage.py shell
```

### Ejemplo 1: Generar PDF de documento específico

```python
from django.contrib.auth import get_user_model
from Sifen.mng_sifen import MSifen

# Obtener usuario
User = get_user_model()
user = User.objects.first()

# Crear instancia y generar PDF
msifen = MSifen()
result = msifen.generando_documentheader(
    userobj=user,
    qdict={'dbcon': 'default', 'id': 123}  # Cambiar ID
)

print(result)
```

### Ejemplo 2: Crear documento FE paso a paso

```python
from django.contrib.auth import get_user_model
from Sifen.models import Etimbrado
from Sifen.mng_sifen import MSifen

User = get_user_model()
user = User.objects.first()
timbrado = Etimbrado.objects.first()

# Preparar datos
uc_fields = {
    'source': 'MANUAL',
    'doc_tipo': 'FE',
    'doc_tipo_cod': 1,
    'timbrado_id': timbrado.id,
    'doc_establecimiento': 1,
    'doc_expedicion': 1,
    'pdv_ruc': '80016036',
    'pdv_ruc_dv': 0,
    'pdv_nombrefactura': 'CLIENTE TEST',
    'pdv_celular': '0981123456',
    'pdv_email': 'test@test.com',
    'doc_moneda': 'GS',
    'doc_cre_tipo_cod': 1,
    'pdv_type_business': 'B2C',
    'doc_tipo_pago_cod': 1,
    'details': [
        {
            'prod_unidad_medida_desc': '77',
            'prod_descripcion': 'Producto test',
            'precio_unitario': 10000,
            'cantidad': 1,
            'porcentaje_iva': 10
        }
    ]
}

# Crear documento
msifen = MSifen()
result = msifen.create_documentheader(
    userobj=user,
    qdict={
        'dbcon': 'default',
        'uc_fields': uc_fields,
        'userobj': user
    }
)

print(result)

# Si fue exitoso, generar PDF
if result.get('success'):
    pdf = msifen.generando_documentheader(
        userobj=user,
        qdict={'dbcon': 'default', 'id': result['id']}
    )
    print(pdf)
```

### Ejemplo 3: Crear NC referenciando factura

```python
from django.contrib.auth import get_user_model
from Sifen.models import DocumentHeader, Etimbrado
from Sifen.mng_sifen import MSifen

User = get_user_model()
user = User.objects.first()

# Buscar factura para referenciar
factura = DocumentHeader.objects.filter(
    doc_tipo='FE',
    doc_estado='Aprobado'
).first()

print(f"Factura: {factura.ek_cdc}")

# Crear NC
timbrado = Etimbrado.objects.first()
uc_fields = {
    'source': 'MANUAL',
    'doc_tipo': 'NC',
    'doc_tipo_cod': 2,
    'doc_relacion_cdc': factura.ek_cdc,
    'doc_motivo': 'Devolución',
    'timbrado_id': timbrado.id,
    'doc_establecimiento': factura.doc_establecimiento,
    'doc_expedicion': factura.doc_expedicion,
    'pdv_ruc': factura.pdv_ruc,
    'pdv_ruc_dv': factura.pdv_ruc_dv,
    'pdv_nombrefactura': factura.pdv_nombrefactura,
    'pdv_celular': factura.pdv_celular,
    'pdv_email': factura.pdv_email,
    'doc_moneda': factura.doc_moneda,
    'doc_cre_tipo_cod': factura.doc_cre_tipo_cod,
    'pdv_type_business': factura.pdv_type_business,
    'doc_tipo_pago_cod': factura.doc_tipo_pago_cod,
    'details': [
        {
            'prod_unidad_medida_desc': '77',
            'prod_descripcion': 'Devolución producto',
            'precio_unitario': 5000,
            'cantidad': 1,
            'porcentaje_iva': 10
        }
    ]
}

msifen = MSifen()
result = msifen.create_documentheader(
    userobj=user,
    qdict={
        'dbcon': 'default',
        'uc_fields': uc_fields,
        'userobj': user
    }
)

print(result)
```

## Verificar archivos generados

Los archivos PDF/HTML/QR se guardan en:

```bash
# Ver últimos PDFs generados
ls -lth media/sifen_docs/*.pdf | head -5

# Ver últimos HTML generados
ls -lth media/sifen_docs/*.html | head -5

# Ver últimos QR generados
ls -lth media/sifen_docs/qr/*.png | head -5
```

## Abrir PDF generado

```bash
# Linux
xdg-open media/sifen_docs/nombre_archivo.pdf

# Ver el path del último PDF generado
ls -t media/sifen_docs/*.pdf | head -1
```

## Debugging

Para ver logs detallados durante la ejecución:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Luego ejecutar tus pruebas
```

## Tips útiles

1. **Ver estructura de un documento:**
   ```python
   from Sifen.models import DocumentHeader
   doc = DocumentHeader.objects.get(pk=123)
   print(vars(doc))
   ```

2. **Ver detalles de un documento:**
   ```python
   from Sifen.models import DocumentDetail
   details = DocumentDetail.objects.filter(headerobj_id=123)
   for d in details:
       print(f"{d.prod_descripcion}: {d.precio_unitario} x {d.cantidad}")
   ```

3. **Listar facturas disponibles para NC:**
   ```python
   from Sifen.models import DocumentHeader
   facturas = DocumentHeader.objects.filter(
       doc_tipo='FE',
       doc_estado='Aprobado'
   )
   for f in facturas:
       print(f"ID: {f.id} | Número: {f.doc_numero} | CDC: {f.ek_cdc}")
   ```

4. **Ver configuración de Sifen:**
   ```python
   from Sifen import fl_sifen_conf
   print(f"BS: {fl_sifen_conf.BS}")
   print(f"RUC: {fl_sifen_conf.RUC}")
   print(f"Logo: {fl_sifen_conf.LOGO}")
   ```

## Troubleshooting

### Error: "No hay timbrados"
Debes crear un timbrado en la base de datos primero.

### Error: "No module named 'Sifen'"
Asegúrate de estar en el directorio del proyecto y usar `python manage.py shell`.

### Error al generar PDF
Verifica que las librerías estén instaladas:
```bash
pip install pdfkit weasyprint
```

### PDF sin logo o estilos
Verifica que las rutas en `fl_sifen_conf.py` sean correctas y que los archivos existan.
