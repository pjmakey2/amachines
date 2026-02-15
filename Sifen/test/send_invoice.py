from celery.execute import send_task
from OptsIO.io_json import to_json, from_json
docobj = DocumentHeader.objects.all().last()
send_task('Sifen.tasks.send_invoice',
    kwargs={
        'username': 111111,
        'qdict': {
            'dbcon': 'default',
            'docpk': docobj.id,
            'dattrs': to_json({
                'full': 1,
        })
    }
})
