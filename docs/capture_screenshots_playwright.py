#!/usr/bin/env python3
"""
Script para capturar screenshots automáticamente del sistema
usando Playwright (más robusto que Selenium)
"""

import os
import sys
import time
import asyncio
import django

# Configurar Django
sys.path.insert(0, '/home/peter/projects/Toca3d')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from playwright.async_api import async_playwright
from OptsIO.models import Apps

# Configuración
BASE_URL = "http://localhost:8002"
SCREENSHOTS_DIR = "/home/peter/projects/Toca3d/docs/screenshots"
USERNAME = "amadmin"
PASSWORD = "zz9cd3zrsXe9kU@IBi5A"

# Crear directorio para screenshots
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Apps que queremos capturar con su botón de crear
APPS_TO_CAPTURE = {
    'SIFEN': {
        'Facturar': 'btn_crear_documentheader',
        'Notas de Crédito': 'btn_crear_documentnc',
        'Timbrados': 'btn_crear_etimbrado',
        'Establecimientos': 'btn_crear_eestablecimiento',
        'Numeración': 'btn_crear_enumbers',
        'Crear Timbrado': None,  # Ya es formulario de creación
        'Gestión Números': 'btn_crear_enumbers',
        'Actividades Económicas': 'btn_crear_actividad_economica',
        'Tipos de Contribuyente': 'btn_crear_tipo_contribuyente'
    },
    'MAESTROS': {
        'Categorías': 'btn_crear_categoria',
        'Marcas': 'btn_crear_marca',
        'Porcentajes IVA': 'btn_crear_porcentaje_iva',
        'Productos': 'btn_crear_producto'
    },
    'PERFIL DE USUARIO': {
        'Perfil': None,  # Vista de perfil
        'Negocios': 'btn_crear_business',
        'Editar Negocio Activo': None  # Formulario directo
    },
    'SISTEMA': {
        'Configuración de Negocio': None  # Formulario de configuración
    }
}

def get_apps_from_db():
    """Obtener apps activas del modelo Apps agrupadas por menú"""
    apps = Apps.objects.filter(active=True).order_by('menu', 'prioridad')

    apps_by_menu = {}
    for app in apps:
        menu = app.menu or 'Otros'
        if menu not in apps_by_menu:
            apps_by_menu[menu] = []
        apps_by_menu[menu].append({
            'id': app.id,
            'menu': menu,
            'friendly_name': app.friendly_name,
            'url': app.url,
            'icon': app.icon,
            'menu_icon': app.menu_icon
        })

    return apps_by_menu

async def main(apps_by_menu):
    """Función principal"""
    print("="*60)
    print("CAPTURA AUTOMÁTICA DE SCREENSHOTS CON PLAYWRIGHT")
    print("="*60)

    async with async_playwright() as p:
        # Iniciar navegador
        print("\n[2/4] Iniciando Chromium...")
        browser = await p.chromium.launch(
            headless=False,  # Mostrar navegador
            channel="chromium"
        )

        # Crear contexto y página
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Login
            print("\n[3/4] Haciendo login...")
            print("=== INICIANDO SESIÓN ===")

            await page.goto(f"{BASE_URL}/io/glogin/")

            # Esperar a que cargue el formulario
            await page.wait_for_selector("#username")

            # Llenar formulario
            await page.fill("#username", USERNAME)
            await page.fill("#password", PASSWORD)

            # Click en botón de login
            await page.click("#loginBtn")

            # Esperar a que redirija (la URL cambiará)
            print("  Esperando respuesta del login...")
            await page.wait_for_url(lambda url: "glogin" not in url, timeout=10000)

            print(f"  ✓ Redirigido a: {page.url}")

            # Esperar a que cargue el dashboard
            await page.wait_for_selector("#appsSidebar", timeout=10000)
            print("✓ Sesión iniciada correctamente")

            # Esperar un momento para que todo se estabilice
            await page.wait_for_timeout(2000)

            # Capturar screenshots
            print("\n[4/4] Capturando screenshots...")
            total_captured = 0

            for section, apps_config in APPS_TO_CAPTURE.items():
                print(f"\n=== CAPTURANDO {section.upper()} ===")

                captured_count = 0

                # Buscar las apps en el menú correspondiente
                for menu_name, apps in apps_by_menu.items():
                    # Verificar si este menú corresponde a la sección
                    if section.upper() in menu_name.upper() or menu_name.upper() in section.upper():

                        for idx, app in enumerate(apps, 1):
                            # Verificar si esta app está en la lista de apps a capturar
                            matching_app = None
                            for app_name, btn_id in apps_config.items():
                                if app_name.lower() in app['friendly_name'].lower() or app['friendly_name'].lower() in app_name.lower():
                                    matching_app = (app_name, btn_id)
                                    break

                            if not matching_app:
                                continue

                            try:
                                app_name, btn_crear_id = matching_app
                                print(f"  → Cargando: {app['friendly_name']}")

                                # Ejecutar JavaScript para abrir la app
                                js_code = """
                                    (async function() {
                                        const app = {
                                            id: %d,
                                            friendly_name: '%s',
                                            url: '%s',
                                            menu: '%s',
                                            icon: '%s'
                                        };

                                        if (typeof openApp === 'function') {
                                            await openApp(app);
                                        }
                                    })();
                                """ % (app['id'], app['friendly_name'], app['url'], app['menu'], app['icon'])

                                await page.evaluate(js_code)

                                # Esperar a que el contenido cargue
                                await page.wait_for_timeout(4000)

                                # Esperar a que desaparezcan los loaders
                                try:
                                    await page.wait_for_selector(".spinner-border", state="hidden", timeout=10000)
                                except:
                                    pass

                                # Esperar un poco más para que los scripts se ejecuten
                                await page.wait_for_timeout(2000)

                                # Scroll al inicio
                                await page.evaluate("window.scrollTo(0, 0)")
                                await page.wait_for_timeout(500)

                                # Tomar screenshot de la lista
                                section_dir = os.path.join(SCREENSHOTS_DIR, section.lower().replace(' ', '_'))
                                os.makedirs(section_dir, exist_ok=True)

                                filename = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_lista.png"
                                filepath = os.path.join(section_dir, filename)

                                await page.screenshot(path=filepath, full_page=False)
                                print(f"    ✓ Screenshot lista guardado: {filepath}")

                                captured_count += 1
                                total_captured += 1

                                # Si hay botón de crear, capturar también el formulario
                                if btn_crear_id:
                                    try:
                                        print(f"    → Abriendo formulario de creación...")

                                        # Hacer clic en el botón de crear
                                        await page.click(f"#{btn_crear_id}")

                                        # Esperar a que aparezca el offcanvas
                                        await page.wait_for_selector("#offcanvasGlobalUi.show", timeout=5000)
                                        await page.wait_for_timeout(2000)

                                        # Scroll al inicio del formulario
                                        await page.evaluate("document.querySelector('#offcanvasGlobalUi .offcanvas-body').scrollTop = 0")
                                        await page.wait_for_timeout(500)

                                        # Tomar screenshot del formulario
                                        filename_form = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_form.png"
                                        filepath_form = os.path.join(section_dir, filename_form)

                                        await page.screenshot(path=filepath_form, full_page=False)
                                        print(f"    ✓ Screenshot formulario guardado: {filepath_form}")

                                        captured_count += 1
                                        total_captured += 1

                                        # Cerrar el offcanvas
                                        await page.evaluate("bootstrap.Offcanvas.getInstance(document.getElementById('offcanvasGlobalUi')).hide()")
                                        await page.wait_for_timeout(1000)

                                    except Exception as e:
                                        print(f"    ⚠ No se pudo capturar formulario: {str(e)}")

                            except Exception as e:
                                print(f"    ✗ Error al capturar {app['friendly_name']}: {str(e)}")

                if captured_count == 0:
                    print(f"  ⚠ No se encontraron apps para {section}")

            print("\n" + "="*60)
            print(f"✅ CAPTURA COMPLETADA: {total_captured} screenshots")
            print(f"Screenshots guardados en: {SCREENSHOTS_DIR}")
            print("="*60)

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            print("\nCerrando navegador...")
            await browser.close()

if __name__ == "__main__":
    # Obtener apps de la base de datos ANTES de entrar al contexto async
    print("\n[1/4] Obteniendo lista de Apps desde la base de datos...")
    apps_by_menu = get_apps_from_db()

    print(f"✓ Se encontraron {sum(len(apps) for apps in apps_by_menu.values())} apps activas")
    print(f"✓ Organizadas en {len(apps_by_menu)} menús:")
    for menu, apps in apps_by_menu.items():
        print(f"  - {menu}: {len(apps)} apps")

    # Ejecutar la parte async
    asyncio.run(main(apps_by_menu))
