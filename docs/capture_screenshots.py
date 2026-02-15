#!/usr/bin/env python3
"""
Script para capturar screenshots automáticamente del sistema
usando Selenium con Chromium y el modelo Apps
"""

import os
import sys
import time
import django

# Configurar Django
sys.path.insert(0, '/home/peter/projects/Toca3d')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Toca3d.settings')
django.setup()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from OptsIO.models import Apps

# Configuración
BASE_URL = "http://localhost:8002"
SCREENSHOTS_DIR = "/home/peter/projects/Toca3d/docs/screenshots"
USERNAME = "amadmin"
PASSWORD = "zz9cd3zrsXe9kU@IBi5A"

# Crear directorio para screenshots
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Apps que queremos capturar (según los módulos solicitados)
APPS_TO_CAPTURE = {
    'SIFEN': [
        'Facturar',
        'Notas de Crédito',
        'Timbrados',
        'Establecimientos',
        'Numeración',
        'Crear Timbrado',
        'Gestión Números',
        'Actividades Económicas',
        'Tipos de Contribuyente'
    ],
    'MAESTROS': [
        'Categorías',
        'Marcas',
        'Porcentajes IVA',
        'Productos'
    ],
    'PERFIL DE USUARIO': [
        'Perfil',
        'Negocios',
        'Editar Negocio Activo'
    ],
    'SISTEMA': [
        'Configuración de Negocio'
    ]
}

def setup_driver():
    """Configurar el driver de Chromium"""
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Comentar para ver el navegador en acción
    # options.add_argument("--headless")

    # Usar webdriver-manager para obtener el driver correcto
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)

    return driver

def take_screenshot(driver, name, section="general"):
    """Tomar screenshot y guardar en carpeta organizada"""
    section_dir = os.path.join(SCREENSHOTS_DIR, section.lower().replace(' ', '_'))
    os.makedirs(section_dir, exist_ok=True)

    # Esperar a que la página cargue completamente
    time.sleep(3)

    # Scroll al inicio de la página
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    filepath = os.path.join(section_dir, f"{name}.png")
    driver.save_screenshot(filepath)
    print(f"✓ Screenshot guardado: {filepath}")

    return filepath

def login(driver):
    """Hacer login en el sistema"""
    print("\n=== INICIANDO SESIÓN ===")
    driver.get(f"{BASE_URL}/io/glogin/")

    # Esperar a que aparezca el formulario de login
    wait = WebDriverWait(driver, 10)

    # Buscar campos de login
    username_field = wait.until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    password_field = driver.find_element(By.ID, "password")

    # Ingresar credenciales
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)

    # El formulario usa AJAX, así que usamos Enter en el password field
    password_field.send_keys("\n")

    # Esperar a que el AJAX complete y redirija
    print("  Esperando respuesta del login...")
    time.sleep(4)

    # Esperar a que la URL cambie (redirección después del login)
    wait.until(lambda d: d.current_url != f"{BASE_URL}/io/glogin/")

    print(f"  ✓ Redirigido a: {driver.current_url}")

    # Esperar a que cargue la página
    time.sleep(3)

    # Esperar a que esté en la página principal
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "appsSidebar") or d.find_element(By.CLASS_NAME, "main-content")
        )
        print("✓ Sesión iniciada correctamente")
    except:
        print(f"⚠ Página cargada, continuando... URL: {driver.current_url}")

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

def capture_app_screenshot(driver, app, section, index):
    """Capturar screenshot de una app específica"""
    try:
        print(f"  → Cargando: {app['friendly_name']}")

        # Ejecutar JavaScript para abrir la app (como lo hace AMAppsUi.html)
        js_code = f"""
        async function loadApp() {{
            const app = {{
                id: {app['id']},
                friendly_name: '{app['friendly_name']}',
                url: '{app['url']}',
                menu: '{app['menu']}',
                icon: '{app['icon']}'
            }};

            // Llamar a openApp (definida en AMAppsUi.html)
            if (typeof openApp === 'function') {{
                await openApp(app);
            }} else {{
                console.error('openApp no está definida');
            }}
        }}
        loadApp();
        """

        driver.execute_script(js_code)

        # Esperar a que el contenido cargue
        time.sleep(5)

        # Esperar a que desaparezcan los loaders
        try:
            WebDriverWait(driver, 15).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, "spinner-border"))
            )
        except:
            pass

        # Esperar un poco más para que los scripts se ejecuten
        time.sleep(2)

        # Nombre del archivo
        filename = f"{index:02d}_{app['friendly_name'].lower().replace(' ', '_')}"
        take_screenshot(driver, filename, section)

        return True

    except Exception as e:
        print(f"  ✗ Error al capturar {app['friendly_name']}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def capture_screenshots_by_section(driver, apps_by_menu):
    """Capturar screenshots organizados por sección"""
    total_captured = 0

    for section, app_names in APPS_TO_CAPTURE.items():
        print(f"\n=== CAPTURANDO {section.upper()} ===")

        captured_count = 0

        # Buscar las apps en el menú correspondiente
        for menu_name, apps in apps_by_menu.items():
            # Verificar si este menú corresponde a la sección
            if section.upper() in menu_name.upper() or menu_name.upper() in section.upper():

                for idx, app in enumerate(apps, 1):
                    # Verificar si esta app está en la lista de apps a capturar
                    if any(name.lower() in app['friendly_name'].lower() or
                           app['friendly_name'].lower() in name.lower()
                           for name in app_names):

                        if capture_app_screenshot(driver, app, section, idx):
                            captured_count += 1
                            total_captured += 1

        if captured_count == 0:
            print(f"  ⚠ No se encontraron apps para {section}")

    return total_captured

def main():
    """Función principal"""
    print("="*60)
    print("CAPTURA AUTOMÁTICA DE SCREENSHOTS")
    print("="*60)

    driver = None

    try:
        # Obtener apps de la base de datos
        print("\n[1/4] Obteniendo lista de Apps desde la base de datos...")
        apps_by_menu = get_apps_from_db()

        print(f"✓ Se encontraron {sum(len(apps) for apps in apps_by_menu.values())} apps activas")
        print(f"✓ Organizadas en {len(apps_by_menu)} menús:")
        for menu, apps in apps_by_menu.items():
            print(f"  - {menu}: {len(apps)} apps")

        # Inicializar driver
        print("\n[2/4] Iniciando Chromium...")
        driver = setup_driver()

        # Login
        print("\n[3/4] Haciendo login...")
        login(driver)

        # Capturar screenshots
        print("\n[4/4] Capturando screenshots...")
        total = capture_screenshots_by_section(driver, apps_by_menu)

        print("\n" + "="*60)
        print(f"✅ CAPTURA COMPLETADA: {total} screenshots")
        print(f"Screenshots guardados en: {SCREENSHOTS_DIR}")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\nCerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    main()
