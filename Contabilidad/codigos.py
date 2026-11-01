"""
Codigos de cuenta de largo fijo por niveles.

El formato del negocio dice cuantos niveles hay y cuantos digitos tiene cada uno, ej '3.3.3.3.3.3':
    '3'          -> 003.000.000.000.000.000  (nivel 1)
    '3.1.3'      -> 003.001.003.000.000.000  (nivel 3)
    '003.001'    -> 003.001.000.000.000.000  (nivel 2)
Un segmento en cero significa "no baja mas": el nivel es la cantidad de segmentos distintos de cero al inicio.
El padre es el mismo codigo con el ultimo segmento no nulo puesto en cero. Como todos los codigos tienen el mismo
largo, ordenar por texto ordena el plan.
"""
import re

FORMATO_DEFAULT = '3.3.3.3.3.3'
RE_FORMATO = re.compile(r'^[1-9](\.[1-9])*$')


def anchos(formato: str) -> list:
    return [int(x) for x in formato.split('.')]


def validar_formato(formato: str) -> str:
    """'' si el formato es valido; si no, el motivo."""
    if not RE_FORMATO.match(formato or ''):
        return "Formato inválido: use los dígitos de cada nivel separados por punto, ej: 3.3.3.3.3.3"
    if len(anchos(formato)) < 2:
        return "El formato necesita al menos dos niveles"
    return ''


def normalizar(entrada: str, formato: str) -> str:
    """
    Codigo completo a partir de una entrada corta o completa. Lanza ValueError con el motivo si no encaja
    en el formato (mas niveles, un segmento demasiado grande, o un cero seguido de un segmento con valor).
    """
    ws = anchos(formato)
    partes = [p.strip() for p in str(entrada or '').strip().split('.') if p.strip() != '']
    if not partes or not all(p.isdigit() for p in partes):
        raise ValueError("El código solo admite números separados por punto, ej: 3.1.3")
    if len(partes) > len(ws):
        raise ValueError(f"El formato tiene {len(ws)} niveles y el código {len(partes)}")
    valores = [int(p) for p in partes] + [0] * (len(ws) - len(partes))
    if valores[0] == 0:
        raise ValueError("El primer nivel no puede ser cero")
    vistos_cero = False
    for v, w in zip(valores, ws):
        if v >= 10 ** w:
            raise ValueError(f"El segmento {v} no entra en {w} dígito(s)")
        if vistos_cero and v:
            raise ValueError("No puede haber un nivel con valor después de un nivel en cero")
        vistos_cero = vistos_cero or v == 0
    return '.'.join(str(v).zfill(w) for v, w in zip(valores, ws))


def nivel(codigo: str) -> int:
    n = 0
    for seg in codigo.split('.'):
        if int(seg) == 0:
            break
        n += 1
    return n


def padre(codigo: str):
    """Codigo del padre (ultimo nivel con valor puesto en cero) o None si es de primer nivel."""
    segs = codigo.split('.')
    n = nivel(codigo)
    if n <= 1:
        return None
    segs[n - 1] = '0' * len(segs[n - 1])
    return '.'.join(segs)


def corto(codigo: str) -> str:
    """Forma corta sin ceros a la izquierda ni niveles vacios: 003.001.003.000.000.000 -> 3.1.3"""
    return '.'.join(str(int(seg)) for seg in codigo.split('.')[:nivel(codigo)])
