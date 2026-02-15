"""
Script para testear la creación de Notas de Crédito (NC) desde CLI

Uso:
    python manage.py shell < test_create_nc.py
"""

from django.contrib.auth import get_user_model
from Sifen.models import DocumentHeader, Etimbrado
from Sifen.mng_sifen import MSifen
from OptsIO.io_json import to_json, from_json
import json

# Obtener usuario
User = get_user_model()
userobj = User.objects.first()
print(f"✓ Usuario: {userobj.username}\n")

# Buscar una factura (FE) para referenciar
try:
    factura = DocumentHeader.objects.filter(
        doc_tipo='FE'
    ).exclude(
        ek_cdc__isnull=True
    ).exclude(
        ek_cdc=''
    ).first()

    if not factura:
        print("❌ No hay facturas con CDC en la base de datos")
        print("💡 Debes crear primero una factura (FE) con CDC antes de crear una NC")
        exit()

    print(f"📄 Factura encontrada para referenciar:")
    print(f"  ID: {factura.id}")
    print(f"  Número: {factura.doc_establecimiento:03d}-{factura.doc_expedicion:03d}-{factura.doc_numero:07d}")
    print(f"  CDC: {factura.ek_cdc}")
    print(f"  Cliente: {factura.pdv_nombrefactura}")
    print(f"  RUC: {factura.pdv_ruc}-{factura.pdv_ruc_dv}")
    print(f"  Total: {factura.doc_total}")
    print(f"  Moneda: {factura.doc_moneda}")

except Exception as e:
    print(f"❌ Error buscando factura: {e}")
    exit()

# Obtener Timbrado activo
timbrado = Etimbrado.objects.first()
if not timbrado:
    print("❌ No hay timbrados en la base de datos")
    exit()

print(f"\n📋 Timbrado: {timbrado.timbrado}")

# Datos para crear una NC
uc_fields = {
    'source': 'MANUAL',
    'doc_tipo': 'NC',
    'doc_tipo_cod': 2,
    'doc_relacion_cdc': factura.ek_cdc,  # CDC de la factura a la que referencia
    'doc_motivo': 'Devolución',  # o 'Bonificación' o 'Crédito incobrable'
    'timbrado_id': timbrado.id,
    'doc_establecimiento': factura.doc_establecimiento,
    'doc_expedicion': factura.doc_expedicion,
    'doc_numero': 999999,  # Será reemplazado por el siguiente número

    # Datos del cliente (copiar de la factura)
    'pdv_ruc': factura.pdv_ruc,
    'pdv_ruc_dv': factura.pdv_ruc_dv,
    'pdv_nombrefactura': factura.pdv_nombrefactura,
    'pdv_celular': factura.pdv_celular,
    'pdv_email': factura.pdv_email,
    'doc_moneda': factura.doc_moneda,
    'doc_cre_tipo_cod': factura.doc_cre_tipo_cod,
    'pdv_type_business': factura.pdv_type_business,
    'doc_tipo_pago_cod': factura.doc_tipo_pago_cod,

    # Líneas de detalle (productos a devolver/acreditar)
    'details': [
        {
            'prod_unidad_medida_desc': '77',
            'prod_descripcion': 'Devolución producto 1',
            'precio_unitario': 5000,
            'cantidad': 1,
            'porcentaje_iva': 10
        }
    ]
}

print(f"\n📦 Datos de la NC a crear:")
print(json.dumps(uc_fields, indent=2))

# Preparar qdict
qdict = {
    'dbcon': 'default',
    'uc_fields': to_json(uc_fields),  # Convertir a JSON string
    'userobj': userobj
}

# Crear NC
try:
    print(f"\n⚙️  Ejecutando create_documentheader para NC...")
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

    # Si se creó exitosamente, generar PDF
    if isinstance(first_result, dict) and first_result.get('success'):
        nc_id = first_result.get('record_id') or first_result.get('id')
        print(f"\n✅ NC creada con ID: {nc_id}")

        # Verificar la NC creada
        nc = DocumentHeader.objects.get(pk=nc_id)
        print(f"\n📊 Detalles de la NC creada:")
        print(f"  Tipo: {nc.doc_tipo}")
        print(f"  Número: {nc.doc_establecimiento:03d}-{nc.doc_expedicion:03d}-{nc.doc_numero:07d}")
        print(f"  CDC Factura relacionada: {nc.doc_relacion_cdc}")
        print(f"  Motivo: {nc.doc_motivo}")
        print(f"  Cliente: {nc.pdv_nombrefactura}")
        print(f"  Total: {nc.doc_total}")
        print(f"  Estado: {nc.doc_estado}")

        print(f"\n⚙️  Generando PDF de la NC...")

        pdf_result = msifen.generando_documentheader(
            userobj=userobj,
            qdict={
                'dbcon': 'default',
                'id': nc_id
            }
        )

        print(f"\n✓ Resultado de generación PDF:")
        print(json.dumps(pdf_result, indent=2, default=str))

        if pdf_result.get('success'):
            print(f"\n✅ PDF de NC generado exitosamente!")
            print(f"📄 PDF: {pdf_result.get('ek_pdf_file')}")
            print(f"🌐 HTML: {pdf_result.get('ek_html_file')}")
            print(f"📱 QR: {pdf_result.get('ek_qr_img')}")
        else:
            print(f"\n❌ Error generando PDF: {pdf_result.get('error')}")
    else:
        print(f"\n❌ Error creando NC: {result.get('error')}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test completado")
print("="*60)
