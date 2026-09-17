from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from OptsIO import events
from OptsIO.models import BusinessEvent, BusinessEventDelivery

CALLS = []


def handler_ok(event):
    CALLS.append(('ok', event.pk))
    return {'ok': True}


def handler_flaky(event):
    CALLS.append(('flaky', event.pk))
    if len([c for c in CALLS if c[0] == 'flaky']) == 1:
        raise RuntimeError('fallo transitorio')


REGISTRY = {
    'test.op.aprobado': ['OptsIO.test_events.handler_ok'],
    '*.aprobado': ['OptsIO.test_events.handler_flaky'],
}


@mock.patch.object(events, '_registry', lambda: REGISTRY)
@mock.patch.object(events, 'dispatch', lambda event_id: True)
class EventBusTest(TestCase):
    def setUp(self):
        CALLS.clear()
        self.source = User.objects.create(username='src')

    def test_emit_es_idempotente(self):
        e1 = events.emit('test.op.aprobado', self.source)
        e2 = events.emit('test.op.aprobado', self.source)
        self.assertEqual(e1.pk, e2.pk)
        self.assertEqual(BusinessEvent.objects.count(), 1)
        e3 = events.emit('test.op.aprobado', self.source, key_suffix='cuota-2')
        self.assertNotEqual(e1.pk, e3.pk)

    def test_reintento_no_repite_handlers_exitosos(self):
        event = events.emit('test.op.aprobado', self.source)
        r1 = events.process_event(event.pk)
        self.assertEqual(r1['status'], 'error')
        r2 = events.process_event(event.pk)
        self.assertEqual(r2['status'], 'done')
        r3 = events.process_event(event.pk)
        self.assertTrue(r3.get('skipped'))
        self.assertEqual([c[0] for c in CALLS], ['ok', 'flaky', 'flaky'])
        self.assertEqual(BusinessEventDelivery.objects.filter(status='done').count(), 2)

    def test_process_pending_barre_errores(self):
        event = events.emit('test.op.aprobado', self.source)
        events.process_event(event.pk)
        result = events.process_pending()
        self.assertEqual(result, {'processed': 1, 'done': 1, 'error': 0})
