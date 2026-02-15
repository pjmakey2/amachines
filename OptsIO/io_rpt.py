import uuid, codecs, json, os
import pdfkit
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from django.http import QueryDict, HttpRequest
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse, resolve
#from htmlmin.minify import html_minify
#from htmlmin import minify as html_minify
from minify_html import minify as html_minify

import logging


class IoRpt:
    def bulk_rpt_print(self, args: list, kwargs: dict) -> dict:
        rpts = self.bulk_rpt_view(args, kwargs)
        for rpt in rpts.get('rpts'):
            #TODO bulk print with cups
            pass
        return {'succes': 'Done', 'rpts': rpts }

    def bulk_rpt_view(self, args: list, kwargs: dict) -> dict:
        qdict = kwargs.get('qdict').copy()
        rq = kwargs.get('rq')
        pks = qdict.getlist('pk')
        qdict.pop('pk', None)
        rpts = []
        for pk in pks:
            qtmp = qdict.copy()
            qtmp.update({'pk': pk})
            rq['qdict'] = qtmp
            rsp = self.rpt_view(request)
            rpts.append(rsp)
        return {'succes': 'Done', 'rpts': rpts }

    def rpt_view(self, request) -> dict:
        logging.info(f'Params: {request.POST}')
        v, e, z = resolve(reverse('dtmpl'))
        qq = request.GET.copy()
        qq.pop('rpt_view', None)
        request.GET = qq 
        c = v(request)
        g_html = int(qq.get('g_html')) if qq.get('g_html') == 0 else True
        g_pdf = int(qq.get('g_pdf')) if qq.get('g_pdf') == 0 else True
        g_pdf_kit = True if qq.get('g_pdf_kit') == 1 else False
        g_pdf_metro = True if qq.get('g_pdf_metro') == 1 else False
        kt = {
            'rout':c.content,
            'rq':request,
            'g_html': g_html,
            'g_pdf': g_pdf,
            'g_pdf_kit': g_pdf_kit,
            'g_pdf_metro': g_pdf_metro,
        }
        return self.html_to_pdf(**kt)
    
    def html_to_pdf(self, *args: list, g_html=True, g_pdf=True, g_pdf_kit=False, g_pdf_metro=False, **kwargs: dict) -> dict:
        unique_print = int(uuid.uuid4())
        rout: str = kwargs.get('rout')
        rout =  rout.decode('utf-8')
        rq = kwargs.get('rq')
        protocol = 'https'
        cwidth = rq.GET.get('width')
        if rq.META.get('HTTP_REFERER'):
            protocol = rq.META.get('HTTP_REFERER').split(':')[0]
        if settings.DEBUG:
            dhost = 'localhost:8010'
        else:
            dhost = rq.META.get('HTTP_HOST')
        host =  rq.META.get('HTTP_HOST', dhost)

        # Create media/rpt directory if it doesn't exist
        media_rpt_dir = os.path.join(settings.MEDIA_ROOT, 'rpt')
        os.makedirs(media_rpt_dir, exist_ok=True)

        ftmpl = f'{settings.BASE_DIR}/templates/rpts/rpt_{unique_print}.html'
        f = codecs.open(ftmpl, 'wb', encoding='utf-8')
        f.write(rout)
        f.close()
        logging.info(f'Render report {ftmpl} with local file paths')
        # Use file:// paths for both HTML and PDF generation to ensure styles are applied
        rout = render_to_string(ftmpl).replace('/static/', f'file://{settings.STATICFILES_DIRS[0]}/').replace('/media/', f'file://{settings.MEDIA_ROOT}/')

        ehtml = f'{settings.BASE_DIR}/templates/rpts/{unique_print}.html'
        f = codecs.open(ehtml, 'wb', encoding='utf-8')
        f.write(rout)
        f.close()
        #rout_style = render_to_string(ftmpl, {'inline_style': 0}).replace('/static/', f'{protocol}://{host}/static/')
        rout_style = render_to_string(ftmpl, {'inline_style': 0}).replace('/static/', f'file://{settings.STATICFILES_DIRS[0]}')
        ehtml_pdf = False
        if g_html:
            logging.info('Render the html version of the report')
            ehtml_style = f'{settings.BASE_DIR}/templates/tmp/{unique_print}_style.html'
            f = codecs.open(ehtml_style, 'wb', encoding='utf-8')
            f.write(html_minify(rout_style.replace('width: 100%', f'width: {cwidth}')))
            f.close()
            ehtml_pdf = f'{settings.BASE_DIR}/templates/tmp/{unique_print}_pdf.html'
            rout_style = render_to_string(ftmpl, {'inline_style': 0 }).replace('/static/', f'file://{settings.STATICFILES_DIRS[0]}')
            f = codecs.open(ehtml_pdf, 'wb', encoding='utf-8')
            f.write(html_minify(rout_style))
            f.close()
        fname = False
        if g_pdf:
            logging.info('Generate the pdf version with write_pdf')
            html = HTML(filename=ehtml_pdf)
            font_config = FontConfiguration()
            css = CSS(string='''
                 @page {
                     size: A4 landscape;
                     margin: 0.1mm;
                 }
             ''')
            fname = os.path.join(media_rpt_dir, f'{unique_print}.pdf')
            html.write_pdf(fname, stylesheets=[css], font_config=font_config)
        if g_pdf_kit:
            mstyles = [
                #f'{settings.BASE_DIR}/static/css/bootstrap.min.css',
                f'{settings.BASE_DIR}/static/amui/amrpt.css',
                #f'{settings.BASE_DIR}/static/bsicons/bootstrap-icons.min.css',
            ]
            # Agregar CSS personalizado del negocio si existe
            dattrs_str = rq.GET.get('dattrs')
            if dattrs_str:
                try:
                    dattrs_data = json.loads(dattrs_str)
                    business_id = dattrs_data.get('id')
                    if business_id:
                        business_css = f'{settings.BASE_DIR}/static/amui/{business_id}.css'
                        if os.path.exists(business_css):
                            mstyles.append(business_css)
                            logging.info(f'Added business CSS: {business_css}')
                except (json.JSONDecodeError, TypeError):
                    pass
            fname = os.path.join(media_rpt_dir, f'{unique_print}.pdf')
            options = {
                'encoding': "UTF-8",
                'orientation': rq.GET.get('orientation','Portrait'),
                'page-size': rq.GET.get('page-size','B5'),
                "enable-local-file-access": "",
            }
            if rq.GET.get('page-height') and rq.GET.get('page-width'):
                options.update({
                    'page-height': rq.GET.get('page-height'),
                    'page-width': rq.GET.get('page-width'),
                })
            if rq.GET.get('margin-top'):
                options['margin-top'] = rq.GET.get('margin-top')
            if rq.GET.get('margin-right'):
                options['margin-right'] = rq.GET.get('margin-right')
            if rq.GET.get('margin-bottom'):
                options['margin-bottom'] = rq.GET.get('margin-bottom')
            if rq.GET.get('margin-left'):
                options['margin-left'] = rq.GET.get('margin-left')
            if rq.GET.get('no-outline'):
                options['no-outline'] = rq.GET.get('no-outline')
            pdfkit.from_file(ehtml_pdf,
                    fname,
                    options = options,
                    css=mstyles,
                    verbose=True
            )
            logging.info(f'Generate the pdf version with pdfkit options {options} and css {mstyles}')
        if g_pdf_metro:
            mstyles = [
                f'{settings.BASE_DIR}/static/plugins/global/plugins.bundle.css',
	            f'{settings.BASE_DIR}/static/css/style.bundle.css',
	            f'{settings.BASE_DIR}/static/base/custom.css',
            ]
            fname = os.path.join(media_rpt_dir, f'{unique_print}.pdf')
            pdfkit.from_file(ehtml_pdf,
                    fname,
                    # options = {
                    #     'encoding': "UTF-8",
                    #     'orientation': 'Portrait',
                    #     'page-size': 'B5',
                    #     "enable-local-file-access": ""
                    # },
                    css=mstyles
            )
            logging.info(f'Generate the pdf version with pdfkit and css {mstyles}')
        tmpl = rq.GET.get("tmpl")
        logging.info(f'Report from template {tmpl} to pdf {fname}  and html {ehtml_style}')
        return {'exitos': 'Hecho', 'pdf_file': fname, 'html_file': ehtml_style}
    
