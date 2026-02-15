"""
Script para testear la generación de PDF de documentos Sifen desde CLI

Uso:
    python manage.py shell < test_sifen_pdf.py

O de forma interactiva:
    python manage.py shell
    >>> exec(open('test_sifen_pdf.py').read())
"""

from django.contrib.auth import get_user_model
from Sifen.models import DocumentHeader
from Sifen.mng_sifen import MSifen
from OptsIO.io_json import to_json, from_json
import json

# Obtener usuario (ajustar según tu base de datos)
User = get_user_model()
try:
    userobj = User.objects.first()
    print(f"✓ Usuario obtenido: {userobj.username}")
except Exception as e:
    print(f"✗ Error obteniendo usuario: {e}")
    exit()

# Obtener un DocumentHeader existente (ajustar el ID según tu BD)
try:
    # Listar primeros 5 documentos disponibles
    docs = list(DocumentHeader.objects.all()[:5])
    print(f"\n📄 Documentos disponibles:")
    for doc in docs:
        print(f"  ID: {doc.id} | Tipo: {doc.doc_tipo} | Número: {doc.doc_numero} | Cliente: {doc.pdv_nombrefactura}")

    # Seleccionar el primero o especificar ID
    if len(docs) == 0:
        print("✗ No hay documentos en la base de datos")
        exit()

    doc_id = docs[0].id

    print(f"\n🎯 Usando documento ID: {doc_id}")

except Exception as e:
    print(f"✗ Error obteniendo documento: {e}")
    exit()

# Preparar parámetros simulando la llamada desde el frontend
qdict = {
    'dbcon': 'default',
    'id': doc_id
}

print(f"\n📦 Parámetros a pasar:")
print(f"  userobj: {userobj.username}")
print(f"  qdict: {json.dumps(qdict, indent=2)}")

# Crear instancia de MSifen y ejecutar método
try:
    print(f"\n⚙️  Ejecutando generando_documentheader...")
    msifen = MSifen()

    result = msifen.generando_documentheader(
        userobj=userobj,
        qdict=qdict
    )

    print(f"\n✓ Resultado obtenido:")
    print(json.dumps(result, indent=2, default=str))

    # Verificar si se generaron archivos
    if result.get('success'):
        print(f"\n✅ PDF generado exitosamente!")
        if result.get('ek_pdf_file'):
            print(f"📄 PDF: {result['ek_pdf_file']}")
        if result.get('ek_html_file'):
            print(f"🌐 HTML: {result['ek_html_file']}")
        if result.get('ek_qr_img'):
            print(f"📱 QR: {result['ek_qr_img']}")
    else:
        print(f"\n❌ Error en la generación:")
        print(f"  {result.get('error', 'Error desconocido')}")

except Exception as e:
    print(f"\n❌ Error ejecutando método: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test completado")
print("="*60)
