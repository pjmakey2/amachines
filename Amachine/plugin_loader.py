"""
Resuelve que apps de plugins instalar, sin importar Django (lo usa settings.py).

Lee `name` y `dependencies` de cada <App>/plugin.py con ast y agrega, antes de cada plugin pedido,
los plugins de los que depende. Asi una instalacion que pide 'Egreso' recibe tambien 'Tesoreria'
aunque su .env no lo nombre.
"""
import ast
from pathlib import Path


def _leer_plugin(plugin_py: Path) -> dict:
    datos = {'name': '', 'dependencies': []}
    for nodo in ast.walk(ast.parse(plugin_py.read_text(encoding='utf-8'))):
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1 and isinstance(nodo.targets[0], ast.Name) \
                and nodo.targets[0].id in datos and isinstance(nodo.value, (ast.Constant, ast.List)):
            datos[nodo.targets[0].id] = ast.literal_eval(nodo.value)
    return datos


def resolver_plugins(base_dir: Path, pedidos: list, core_apps: list) -> list:
    """Apps a instalar, en orden de dependencias. Ignora dependencias que ya son core o que no existen como app."""
    plugins = {p.parent.name: _leer_plugin(p) for p in Path(base_dir).glob('*/plugin.py')}
    app_de = {datos['name']: app for app, datos in plugins.items() if datos['name']}
    resultado = []

    def agregar(app, visitando=()):
        if app in resultado or app in core_apps or app in visitando:
            return
        for dep in plugins.get(app, {}).get('dependencies', []):
            if dep in app_de:
                agregar(app_de[dep], visitando + (app,))
        resultado.append(app)

    for app in pedidos:
        agregar(app)
    return resultado
