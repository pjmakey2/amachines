"""
Aritmetica monetaria segura.

OptsIO.io_serial fija getcontext().prec = 10 en el hilo que lo importa; con 10 digitos
significativos un saldo mayor a 9.999.999.999 se redondea al sumar en Python. Todo metodo
que opere montos debe correr con @precision_monetaria.
"""
from decimal import Decimal, ROUND_HALF_UP, localcontext
from functools import wraps

Q6 = Decimal('0.000001')


def precision_monetaria(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with localcontext() as ctx:
            ctx.prec = 28
            ctx.rounding = ROUND_HALF_UP
            return func(*args, **kwargs)
    return wrapper


def iva_incluido(monto: Decimal, divisor: int) -> Decimal:
    """IVA contenido en un monto IVA incluido: divisor 11 para el 10%, 21 para el 5%."""
    with localcontext() as ctx:
        ctx.prec = 28
        return (Decimal(monto) / divisor).quantize(Q6, rounding=ROUND_HALF_UP)
