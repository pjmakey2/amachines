"""
Presets de tema de la tienda: un CSS listo por rubro + colores/tipografia por defecto + estructura.

Un TemaTienda elige un preset y opcionalmente pisa sus colores; el CSS del preset se carga despues
del base (tienda.css) y antes del CSS propio del tema. Agregar un preset = un archivo en
static/Ecommerce/temas/<clave>.css + una entrada aca.
"""

PRESETS = {
    'clasico': {
        'nombre': 'Clásico', 'rubro': 'General',
        'descripcion': 'Cabecera oscura, grilla simple y portada con imagen. Sirve para cualquier rubro.',
        'colores': {'primario': '#111827', 'acento': '#2563eb', 'fondo': '#ffffff', 'texto': '#1f2937'},
        'fuente': "'Inter', system-ui, sans-serif", 'fuentes_google': 'Inter:wght@400;500;600;700',
        'sidebar': False, 'hero': 'banner',
    },
    'minimal': {
        'nombre': 'Minimal', 'rubro': 'Moda / diseño',
        'descripcion': 'Blanco y negro, tipografía grande, barra de anuncio roja, filtros laterales y badges de oferta.',
        'colores': {'primario': '#0a0a0a', 'acento': '#e63946', 'fondo': '#ffffff', 'texto': '#171717'},
        'fuente': "'Inter', system-ui, sans-serif", 'fuentes_google': 'Inter:wght@400;500;600;700;800',
        'sidebar': True, 'hero': 'banner',
    },
    'bazaar': {
        'nombre': 'Bazaar', 'rubro': 'Electrónica / marketplace',
        'descripcion': 'Buscador protagonista, botón de categorías, portada dividida con tarjetas promocionales.',
        'colores': {'primario': '#1f2937', 'acento': '#2563eb', 'fondo': '#f6f8fb', 'texto': '#1f2937'},
        'fuente': "'Outfit', system-ui, sans-serif", 'fuentes_google': 'Outfit:wght@400;500;600;700',
        'sidebar': True, 'hero': 'split',
    },
    'fresco': {
        'nombre': 'Fresco', 'rubro': 'Almacén / alimentos',
        'descripcion': 'Verde y tarjetas pastel, categorías con ícono y carrusel de promociones de producto.',
        'colores': {'primario': '#14532d', 'acento': '#22c55e', 'fondo': '#ffffff', 'texto': '#1f2937'},
        'fuente': "'Outfit', system-ui, sans-serif", 'fuentes_google': 'Outfit:wght@400;500;600;700',
        'sidebar': True, 'hero': 'carrusel',
    },
    'hogar': {
        'nombre': 'Hogar', 'rubro': 'Muebles / decoración',
        'descripcion': 'Tonos cálidos, portada grande con llamado a la acción amarillo y tarjetas laterales.',
        'colores': {'primario': '#1e293b', 'acento': '#f5b301', 'fondo': '#faf8f5', 'texto': '#1e293b'},
        'fuente': "'Inter', system-ui, sans-serif", 'fuentes_google': 'Inter:wght@400;500;600;700',
        'sidebar': True, 'hero': 'split',
    },
}
PRESET_DEFAULT = 'clasico'
PRESET_CHOICES = [(k, f"{v['nombre']} — {v['rubro']}") for k, v in PRESETS.items()]


def get_preset(clave: str) -> dict:
    return PRESETS.get(clave) or PRESETS[PRESET_DEFAULT]
