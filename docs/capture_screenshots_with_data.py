#!/usr/bin/env python3
"""
Script para capturar screenshots automáticamente del sistema
ADEMÁS de completar formularios con datos de prueba
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
SCREENSHOTS_DIR = "/home/peter/projects/Toca3d/docs/screenshots_with_data"
USERNAME = "amadmin"
PASSWORD = "zz9cd3zrsXe9kU@IBi5A"

# Crear directorio para screenshots
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Apps y sus datos de prueba
APPS_CONFIG = {
    'MAESTROS': {
        'Categorías': {
            'btn_id': 'btn_crear_categoria',
            'form_id_pattern': 'form_categoria_',
            'data': {
                'nombre': 'Electrónica',
                'descripcion': 'Productos electrónicos y tecnología',
                'activo': 'true'
            }
        },
        'Marcas': {
            'btn_id': 'btn_crear_marca',
            'form_id_pattern': 'form_marca_',
            'data': {
                'nombre': 'Samsung',
                'descripcion': 'Marca líder en tecnología',
                'activo': 'true'
            }
        },
        'Porcentajes IVA': {
            'btn_id': 'btn_crear_porcentaje_iva',
            'form_id_pattern': 'form_porcentaje_iva_',
            'data': {
                'porcentaje': '10',
                'descripcion': 'IVA General 10%',
                'activo': 'true'
            }
        },
        'Productos': {
            'btn_id': 'btn_crear_producto',
            'form_id_pattern': 'form_producto_',
            'data': {
                'prod_cod': '',  # Se genera automático
                'ean': '7891234567890',
                'descripcion': 'Smartphone Samsung Galaxy A54',
                'precio': '2500000',
                'costo': '2000000',
                'moneda': 'PYG',
                'stock': '10',
                'exenta': '0',
                'g5': '0',
                'g10': '100',
                'activo': True  # checkbox
            }
        }
    },
    'SIFEN': {
        'Establecimientos': {
            'btn_id': 'btn_crear_eestablecimiento',
            'form_id_pattern': 'form_eestablecimiento_',
            'data': {
                'codigo': '001',
                'denominacion': 'Casa Matriz',
                'direccion': 'Av. España 123',
                'telefono': '021123456',
                'email': 'casa.matriz@empresa.com',
                'activo': 'true'
            }
        },
        'Actividades Económicas': {
            'btn_id': 'btn_crear_actividadeconomica',
            'form_id_pattern': 'form_actividadeconomica_',
            'data': {
                'codigo': '62010',
                'descripcion': 'Desarrollo de software y consultoría',
                'activo': 'true'
            }
        },
        'Tipos de Contribuyente': {
            'btn_id': 'btn_crear_tipocontribuyente',
            'form_id_pattern': 'form_tipocontribuyente_',
            'data': {
                'codigo': '1',
                'descripcion': 'Persona Jurídica',
                'activo': 'true'
            }
        }
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

async def fill_form_field(page, field_name, field_value, form_id_pattern):
    """Llena un campo del formulario"""
    try:
        # Esperar a que el campo esté disponible
        selector = f"[id^='{form_id_pattern}'] [name='{field_name}']"

        # Verificar el tipo de campo
        element = await page.query_selector(selector)
        if not element:
            print(f"      ⚠ Campo {field_name} no encontrado")
            return False

        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
        input_type = await element.evaluate("el => el.type")

        # Llenar según el tipo de campo
        if tag_name == 'select':
            await page.select_option(selector, value=str(field_value))
            print(f"      ✓ Select {field_name} = {field_value}")
        elif input_type == 'checkbox':
            if field_value:
                await page.check(selector)
            else:
                await page.uncheck(selector)
            print(f"      ✓ Checkbox {field_name} = {field_value}")
        elif tag_name == 'textarea':
            await page.fill(selector, str(field_value))
            print(f"      ✓ Textarea {field_name} = {field_value}")
        else:
            await page.fill(selector, str(field_value))
            print(f"      ✓ Input {field_name} = {field_value}")

        return True
    except Exception as e:
        print(f"      ⚠ Error llenando campo {field_name}: {str(e)}")
        return False

async def main(apps_by_menu):
    """Función principal"""
    print("="*60)
    print("CAPTURA AUTOMÁTICA CON DATOS DE PRUEBA")
    print("="*60)

    async with async_playwright() as p:
        # Iniciar navegador
        print("\n[2/4] Iniciando Chromium...")
        browser = await p.chromium.launch(
            headless=False,
            channel="chromium"
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        try:
            # Login
            print("\n[3/4] Haciendo login...")
            await page.goto(f"{BASE_URL}/io/glogin/")
            await page.wait_for_selector("#username")
            await page.fill("#username", USERNAME)
            await page.fill("#password", PASSWORD)
            await page.click("#loginBtn")
            await page.wait_for_url(lambda url: "glogin" not in url, timeout=10000)
            await page.wait_for_selector("#appsSidebar", timeout=10000)
            print("✓ Sesión iniciada correctamente")
            await page.wait_for_timeout(2000)

            # Capturar screenshots
            print("\n[4/4] Capturando screenshots y completando formularios...")
            total_captured = 0
            total_forms_filled = 0

            for section, apps_config in APPS_CONFIG.items():
                print(f"\n=== PROCESANDO {section.upper()} ===")

                # Buscar las apps en el menú correspondiente
                for menu_name, apps in apps_by_menu.items():
                    if section.upper() in menu_name.upper() or menu_name.upper() in section.upper():

                        for idx, app in enumerate(apps, 1):
                            # Verificar si esta app está en la configuración
                            matching_config = None
                            for app_name, config in apps_config.items():
                                if app_name.lower() in app['friendly_name'].lower() or app['friendly_name'].lower() in app_name.lower():
                                    matching_config = (app_name, config)
                                    break

                            if not matching_config:
                                continue

                            app_name, config = matching_config

                            try:
                                print(f"\n  → Cargando: {app['friendly_name']}")

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
                                await page.wait_for_timeout(4000)

                                # Esperar a que desaparezcan los loaders
                                try:
                                    await page.wait_for_selector(".spinner-border", state="hidden", timeout=10000)
                                except:
                                    pass

                                await page.wait_for_timeout(2000)
                                await page.evaluate("window.scrollTo(0, 0)")
                                await page.wait_for_timeout(500)

                                # Tomar screenshot de la lista vacía
                                section_dir = os.path.join(SCREENSHOTS_DIR, section.lower().replace(' ', '_'))
                                os.makedirs(section_dir, exist_ok=True)

                                filename = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_01_lista_vacia.png"
                                filepath = os.path.join(section_dir, filename)
                                await page.screenshot(path=filepath, full_page=False)
                                print(f"    ✓ Screenshot lista vacía: {filepath}")
                                total_captured += 1

                                # Abrir formulario y completarlo
                                if config['btn_id']:
                                    offcanvas_opened = False
                                    try:
                                        print(f"    → Abriendo formulario...")
                                        await page.click(f"#{config['btn_id']}")
                                        await page.wait_for_selector("#offcanvasGlobalUi.show", timeout=5000)
                                        offcanvas_opened = True
                                        await page.wait_for_timeout(2000)

                                        # Tomar screenshot del formulario vacío
                                        filename_form_empty = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_02_form_vacio.png"
                                        filepath_form_empty = os.path.join(section_dir, filename_form_empty)
                                        await page.screenshot(path=filepath_form_empty, full_page=False)
                                        print(f"    ✓ Screenshot formulario vacío: {filepath_form_empty}")
                                        total_captured += 1

                                        # Completar campos
                                        print(f"    → Completando campos...")
                                        for field_name, field_value in config['data'].items():
                                            await fill_form_field(page, field_name, field_value, config['form_id_pattern'])
                                            await page.wait_for_timeout(300)

                                        # Tomar screenshot del formulario completo
                                        await page.wait_for_timeout(1000)
                                        filename_form_filled = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_03_form_lleno.png"
                                        filepath_form_filled = os.path.join(section_dir, filename_form_filled)
                                        await page.screenshot(path=filepath_form_filled, full_page=False)
                                        print(f"    ✓ Screenshot formulario lleno: {filepath_form_filled}")
                                        total_captured += 1

                                        # Guardar formulario
                                        print(f"    → Guardando formulario...")
                                        # Buscar el botón de guardar dentro del formulario
                                        submit_button = await page.query_selector(f"[id^='{config['form_id_pattern']}'] button[type='submit']")
                                        if submit_button:
                                            await submit_button.click()
                                        else:
                                            print(f"    ⚠ No se encontró botón submit")

                                        # Esperar a que se procese
                                        await page.wait_for_timeout(3000)

                                        # Verificar si hay mensajes de éxito o error
                                        try:
                                            # Esperar a que el offcanvas se cierre (señal de éxito)
                                            await page.wait_for_selector("#offcanvasGlobalUi:not(.show)", timeout=5000)
                                            offcanvas_opened = False
                                            print(f"    ✓ Formulario guardado exitosamente")
                                            total_forms_filled += 1
                                        except:
                                            print(f"    ⚠ El formulario podría no haberse guardado correctamente")

                                        # Esperar a que recargue la tabla
                                        await page.wait_for_timeout(2000)

                                        # Tomar screenshot de la lista con datos
                                        await page.evaluate("window.scrollTo(0, 0)")
                                        await page.wait_for_timeout(500)

                                        filename_list_filled = f"{idx:02d}_{app['friendly_name'].lower().replace(' ', '_')}_04_lista_con_datos.png"
                                        filepath_list_filled = os.path.join(section_dir, filename_list_filled)
                                        await page.screenshot(path=filepath_list_filled, full_page=False)
                                        print(f"    ✓ Screenshot lista con datos: {filepath_list_filled}")
                                        total_captured += 1

                                    except Exception as e:
                                        print(f"    ⚠ Error al completar formulario: {str(e)}")
                                    finally:
                                        # SIEMPRE cerrar el offcanvas si quedó abierto
                                        if offcanvas_opened:
                                            try:
                                                print(f"    → Cerrando offcanvas...")
                                                await page.evaluate("var offcanvasEl = document.getElementById('offcanvasGlobalUi'); if(offcanvasEl && offcanvasEl.classList.contains('show')) { var bsOffcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl); if(bsOffcanvas) bsOffcanvas.hide(); }")
                                                await page.wait_for_timeout(1000)
                                            except:
                                                pass

                            except Exception as e:
                                print(f"    ✗ Error al procesar {app['friendly_name']}: {str(e)}")

            print("\n" + "="*60)
            print(f"✅ PROCESO COMPLETADO")
            print(f"   Screenshots capturados: {total_captured}")
            print(f"   Formularios completados: {total_forms_filled}")
            print(f"   Guardados en: {SCREENSHOTS_DIR}")
            print("="*60)

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            print("\nCerrando navegador...")
            await browser.close()

if __name__ == "__main__":
    print("\n[1/4] Obteniendo lista de Apps desde la base de datos...")
    apps_by_menu = get_apps_from_db()

    print(f"✓ Se encontraron {sum(len(apps) for apps in apps_by_menu.values())} apps activas")
    print(f"✓ Organizadas en {len(apps_by_menu)} menús")

    asyncio.run(main(apps_by_menu))
