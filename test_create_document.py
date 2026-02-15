"""
Script para testear la creación completa de un documento Sifen desde CLI

Uso:
    python manage.py shell < test_create_document.py
"""

from django.contrib.auth import get_user_model
from Sifen.models import DocumentHeader, Etimbrado, Business
from Sifen.mng_sifen import MSifen
from OptsIO.io_json import to_json, from_json
import json
from datetime import date

# Obtener usuario
User = get_user_model()
userobj = User.objects.first()
print(f"✓ Usuario: {userobj.username}\n")

# Obtener Timbrado activo
timbrado = Etimbrado.objects.first()
if not timbrado:
    print("❌ No hay timbrados en la base de datos")
    exit()

print(f"📋 Timbrado: {timbrado.timbrado}")

# Datos de ejemplo para crear un documento FE
uc_fields = {
    'source': 'MANUAL',
    'doc_tipo': 'FE',
    'doc_tipo_cod': 1,
    'timbrado_id': timbrado.id,
    'doc_establecimiento': 1,
    'doc_expedicion': 1,
    'doc_numero': 999999,  # Número temporal, será reemplazado
    'pdv_ruc': '80016036',
    'pdv_ruc_dv': 0,
    'pdv_nombrefactura': 'CLIENTE DE PRUEBA CLI',
    'pdv_celular': '0981123456',
    'pdv_email': 'test@example.com',
    'doc_moneda': 'GS',
    'doc_cre_tipo_cod': 1,  # Contado
    'pdv_type_business': 'B2C',
    'doc_tipo_pago_cod': 1,  # Efectivo
    'details': [
        {
            'prod_unidad_medida_desc': '77',  # Unidad
            'prod_descripcion': 'Producto de prueba desde CLI',
            'precio_unitario': 10000,
            'cantidad': 2,
            'porcentaje_iva': 10
        },
        {
            'prod_unidad_medida_desc': '77',
            'prod_descripcion': 'Segundo producto de prueba',
            'precio_unitario': 5000,
            'cantidad': 1,
            'porcentaje_iva': 10
        }
    ]
}

print(f"\n📦 Datos del documento a crear:")
print(json.dumps(uc_fields, indent=2))

# Preparar qdict simulando llamada desde io_maction
qdict = {
    'dbcon': 'default',
    'uc_fields': to_json(uc_fields),  # Convertir a JSON string
    'userobj': userobj
}

# Crear instancia de MSifen y ejecutar creación
try:
    print(f"\n⚙️  Ejecutando create_documentheader...")
    msifen = MSifen()

    result = msifen.create_documentheader(
        userobj=userobj,
        qdict=qdict
    )

    print(f"\n✓ Resultado de creación:")
    print(json.dumps(result, indent=2, default=str))

    # El resultado es una tupla/lista, el primer elemento tiene el success y record_id
    if isinstance(result, (list, tuple)) and len(result) > 0:
        first_result = result[0]
    else:
        first_result = result

    # Si se creó exitosamente, intentar generar PDF
    if isinstance(first_result, dict) and first_result.get('success'):
        doc_id = first_result.get('record_id') or first_result.get('id')
        print(f"\n✅ Documento creado con ID: {doc_id}")

        print(f"\n⚙️  Generando PDF del documento recién creado...")

        pdf_result = msifen.generando_documentheader(
            userobj=userobj,
            qdict={
                'dbcon': 'default',
                'id': doc_id
            }
        )

        print(f"\n✓ Resultado de generación PDF:")
        print(json.dumps(pdf_result, indent=2, default=str))

        if pdf_result.get('success'):
            print(f"\n✅ PDF generado exitosamente!")
            print(f"📄 PDF: {pdf_result.get('ek_pdf_file')}")
            print(f"🌐 HTML: {pdf_result.get('ek_html_file')}")
            print(f"📱 QR: {pdf_result.get('ek_qr_img')}")

            # Verificar el documento creado
            doc = DocumentHeader.objects.get(pk=doc_id)
            print(f"\n📊 Detalles del documento creado:")
            print(f"  Tipo: {doc.doc_tipo}")
            print(f"  Número: {doc.doc_establecimiento:03d}-{doc.doc_expedicion:03d}-{doc.doc_numero:07d}")
            print(f"  Cliente: {doc.pdv_nombrefactura}")
            print(f"  Total: {doc.doc_total}")
            print(f"  IVA: {doc.doc_iva}")
            print(f"  Estado: {doc.doc_estado}")
        else:
            print(f"\n❌ Error generando PDF: {pdf_result.get('error')}")
    else:
        print(f"\n❌ Error creando documento: {result.get('error')}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test completado")
print("="*60)
