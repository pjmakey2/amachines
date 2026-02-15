import os
import shutil
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender='Sifen.Business')
def process_business_css(sender, instance, **kwargs):
    """
    Signal para procesar el CSS del negocio cuando se guarda:
    1. Lee el contenido del archivo CSS y lo guarda en css_invoice_content
    2. Copia el archivo CSS a static/amui/{business_id}.css
    """
    if instance.css_invoice:
        # Leer contenido del CSS y guardarlo en css_invoice_content
        css_content = None
        if instance.css_invoice.name:
            try:
                instance.css_invoice.seek(0)
                css_content = instance.css_invoice.read().decode('utf-8')
            except Exception:
                # Si falla la lectura directa, intentar desde el path
                try:
                    with open(instance.css_invoice.path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                except Exception:
                    pass

        # Actualizar css_invoice_content si cambió
        if css_content and css_content != instance.css_invoice_content:
            # Usar update para evitar recursión de la señal
            from Sifen.models import Business
            Business.objects.filter(pk=instance.pk).update(css_invoice_content=css_content)

        # Copiar CSS a static/amui/{business_id}.css
        static_css_dir = os.path.join(settings.BASE_DIR, 'static', 'amui')
        os.makedirs(static_css_dir, exist_ok=True)

        static_css_path = os.path.join(static_css_dir, f'{instance.id}.css')

        try:
            shutil.copy(instance.css_invoice.path, static_css_path)
        except Exception as e:
            print(f'Error copying CSS file: {e}')
    else:
        # Si se eliminó el CSS, limpiar el contenido y el archivo estático
        if instance.css_invoice_content:
            from Sifen.models import Business
            Business.objects.filter(pk=instance.pk).update(css_invoice_content=None)

        # Eliminar archivo CSS estático si existe
        static_css_path = os.path.join(settings.BASE_DIR, 'static', 'amui', f'{instance.id}.css')
        if os.path.exists(static_css_path):
            try:
                os.remove(static_css_path)
            except Exception:
                pass
