"""
Eventos de negocio de los documentos electronicos.

El cierre de una venta es su aprobacion por SIFEN, que se escribe desde varios caminos
(tracking de lotes, consulta de CDC...). `emitir_eventos_documentos` se llama al final de esos
procesos y emite, una sola vez por documento, 'sifen.documento.aprobado' / 'sifen.documento.cancelado'.
Si ningun plugin escucha esos eventos no hace nada.
"""
from datetime import date, timedelta

from OptsIO import events
from OptsIO.models import BusinessEvent
from Sifen.models import Business, DocumentHeader

EVENTOS = {'Aprobado': 'sifen.documento.aprobado', 'Cancelado': 'sifen.documento.cancelado'}


def emitir_eventos_documentos(dias: int = 45, doc_ids=None) -> int:
    if not any(events.get_handlers(e) for e in EVENTOS.values()):
        return 0
    docs = DocumentHeader.objects.filter(ek_estado__in=list(EVENTOS))
    docs = docs.filter(pk__in=doc_ids) if doc_ids else docs.filter(doc_fecha__gte=date.today() - timedelta(days=dias))
    docs = list(docs.only('id', 'ek_estado', 'ek_bs_ruc', 'doc_tipo', 'doc_numero', 'doc_fecha'))
    ya_emitidos = set(BusinessEvent.objects.filter(
        event_type__in=list(EVENTOS.values()), source_app='Sifen', source_model='documentheader',
        source_id__in=[d.pk for d in docs]).values_list('event_type', 'source_id'))
    negocios = {b.ruc: b for b in Business.objects.filter(ruc__in={d.ek_bs_ruc for d in docs})}
    emitidos = 0
    for doc in docs:
        evento = EVENTOS[doc.ek_estado]
        if (evento, doc.pk) in ya_emitidos or doc.ek_bs_ruc not in negocios:
            continue
        events.emit(evento, doc, business=negocios[doc.ek_bs_ruc],
                    payload={'doc_tipo': doc.doc_tipo, 'numero': doc.doc_numero, 'fecha': str(doc.doc_fecha)})
        emitidos += 1
    return emitidos
