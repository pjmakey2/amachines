from celery import shared_task

from Egreso.mng_egreso import MEgreso


@shared_task
def generar_gastos_recurrentes():
    """Corre una vez al dia por Celery beat: genera los gastos recurrentes que vencen hoy o antes."""
    return MEgreso().generar_recurrentes()
