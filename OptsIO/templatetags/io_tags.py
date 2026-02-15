try:
    from urlparse import urljoin
except:
    from urllib.parse import urljoin
from django.template.defaulttags import URLNode
from django.templatetags.static import StaticNode, do_static as base_static
from django.template.defaulttags import url as baseurl
from django.conf import settings
from django import template
from random import randint
import json




register = template.Library()

@register.filter(name="to_json")
def to_json(value):
    """Convert Python object to JSON string"""
    return json.dumps(value)

@register.simple_tag(name="rr")
def rr() -> int:
    return randint(1, 100)

@register.simple_tag(takes_context=True, name="business_logo")
def business_logo(context):
    """Get active business logo URL or default logo"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            # Get user profile
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                # Get active business
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    if business.logo:
                        return business.logo.url
    except Exception:
        pass
    return settings.STATIC_URL + 'images/amachine_logo.png'

@register.simple_tag(name="first_business_logo")
def first_business_logo():
    """
    Get the first business logo URL (for login page before authentication).
    Returns None if no business exists or no logo is configured.
    """
    try:
        from Sifen.models import Business
        business = Business.objects.filter(logo__isnull=False).exclude(logo='').first()
        if business and business.logo:
            return business.logo.url
    except Exception:
        pass
    return None

@register.simple_tag(name="first_business_name")
def first_business_name():
    """
    Get the first business name (for login page before authentication).
    Returns default name if no business exists.
    """
    try:
        from Sifen.models import Business
        business = Business.objects.first()
        if business:
            return business.name
    except Exception:
        pass
    return 'Amachine ERP'

@register.simple_tag(takes_context=True, name="business_logo_path")
def business_logo_path(context):
    """Get active business logo path (for PDF generation) or default logo path"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        import os
        request = context.get('request')
        if request and request.user.is_authenticated:
            # Get user profile
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                # Get active business
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    if business.logo:
                        return business.logo.path
    except Exception:
        pass
    # Return default logo path
    from django.contrib.staticfiles import finders
    default_logo = finders.find('images/amachine_logo.png')
    if default_logo:
        return default_logo
    return ''

@register.simple_tag(takes_context=True, name="business_name")
def business_name(context):
    """Get active business name or default name"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            # Get user profile
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                # Get active business
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    return user_business.businessobj.name
    except Exception:
        pass
    return 'Alta Machines'

@register.simple_tag(takes_context=True, name="business_email")
def business_email(context):
    """Get active business email or default email"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            # Get user profile
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                # Get active business
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    return user_business.businessobj.correo
    except Exception:
        pass
    return 'info@altamachines.com'

@register.simple_tag(takes_context=True, name="business_web")
def business_web(context):
    """Get active business website or default website"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            # Get user profile
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                # Get active business
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    if user_business.businessobj.web:
                        return user_business.businessobj.web
    except Exception:
        pass
    return 'https://altamachines.com'

@register.simple_tag(takes_context=True, name="business_favicon")
def business_favicon(context):
    """Get active business favicon URL or fallback to logo"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    # Usar favicon si existe, sino usar logo
                    if business.favicon:
                        return business.favicon.url
                    elif business.logo:
                        return business.logo.url
    except Exception:
        pass
    return settings.STATIC_URL + 'images/amachine_logo.png'

@register.simple_tag(takes_context=True, name="business_logo_invoice_path")
def business_logo_invoice_path(context):
    """Get active business invoice logo path (for PDF generation) or fallback to logo"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        import os
        request = context.get('request')
        if request and request.user.is_authenticated:
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    # Usar logo_invoice si existe, sino usar logo
                    if business.logo_invoice:
                        return business.logo_invoice.path
                    elif business.logo:
                        return business.logo.path
    except Exception:
        pass
    # Return default logo path
    from django.contrib.staticfiles import finders
    default_logo = finders.find('images/amachine_logo.png')
    if default_logo:
        return default_logo
    return ''

@register.simple_tag(takes_context=True, name="business_css_invoice_inline")
def business_css_invoice_inline(context):
    """Get active business custom CSS for invoices (inline style tag)"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        from django.utils.safestring import mark_safe
        request = context.get('request')
        if request and request.user.is_authenticated:
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    if business.css_invoice_content:
                        return mark_safe(f'<style>{business.css_invoice_content}</style>')
    except Exception:
        pass
    return ''

@register.simple_tag(takes_context=True, name="business_css_invoice_url")
def business_css_invoice_url(context):
    """Get URL for business custom CSS file for invoices (user's active business)"""
    try:
        from OptsIO.models import UserProfile, UserBusiness
        request = context.get('request')
        if request and request.user.is_authenticated:
            profile = UserProfile.objects.filter(username=request.user.username).first()
            if profile:
                user_business = UserBusiness.objects.filter(
                    userprofileobj=profile,
                    active=True
                ).select_related('businessobj').first()

                if user_business and user_business.businessobj:
                    business = user_business.businessobj
                    # Retornar URL del CSS estático específico del negocio
                    return f'{settings.STATIC_URL}amui/{business.id}.css'
    except Exception:
        pass
    return ''

@register.simple_tag(name="business_css_by_ruc")
def business_css_by_ruc(ruc):
    """Get URL for business custom CSS file by RUC (for documents)"""
    try:
        from Sifen.models import Business
        import os
        if ruc:
            business = Business.objects.filter(ruc=ruc).first()
            if business:
                # Verificar si el archivo CSS existe
                css_path = os.path.join(settings.BASE_DIR, 'static', 'amui', f'{business.id}.css')
                if os.path.exists(css_path):
                    return f'{settings.STATIC_URL}amui/{business.id}.css'
    except Exception:
        pass
    return ''

@register.simple_tag(name="business_css_inline_by_ruc")
def business_css_inline_by_ruc(ruc):
    """Get business custom CSS content inline (wrapped in <style> tag) by RUC"""
    try:
        from Sifen.models import Business
        from django.utils.safestring import mark_safe
        import os
        if ruc:
            business = Business.objects.filter(ruc=ruc).first()
            if business:
                # Verificar si el archivo CSS existe
                css_path = os.path.join(settings.BASE_DIR, 'static', 'amui', f'{business.id}.css')
                if os.path.exists(css_path):
                    with open(css_path, 'r') as f:
                        css_content = f.read()
                    return mark_safe(f'<style>\n/* Custom CSS for Business {business.id} */\n{css_content}\n</style>')
    except Exception:
        pass
    return ''

class AbsoluteURLNode(URLNode):
    def render(self, context):
        path = super(AbsoluteURLNode, self).render(context)
        FDOMAIN = settings.FDOMAIN
        # if hasattr(context, 'request'):
            # if re.search('android', context.request.META['HTTP_USER_AGENT'].lower()):
            #     FDOMAIN = 'http://webapps.aconcagua.com.py:8000'
        return urljoin(FDOMAIN, path)

@register.tag
def url_full(parser, token, node_cls=AbsoluteURLNode):
    """Just like {% url %} but ads the domain of the current site."""
    node_instance = baseurl(parser, token)
    return node_cls(view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar)

class AbsoluteStaticNode(StaticNode):
    def render(self, context):
        # Resolve the static path using StaticNode's render
        path = super(AbsoluteStaticNode, self).render(context)
        # Use FDOMAIN from settings
        FDOMAIN = getattr(settings, "FDOMAIN", "")
        # Optional: you could adjust per user-agent here if needed
        # if hasattr(context, "request"):
        #     if re.search("android", context.request.META["HTTP_USER_AGENT"].lower()):
        #         FDOMAIN = "http://webapps.fl.com.py:8000"
        return urljoin(FDOMAIN, path)

@register.tag
def static_full(parser, token, node_cls=AbsoluteStaticNode):
    """
    Just like {% static %} but prefixes the domain defined in settings.FDOMAIN.
    Usage: {% static_full "path/to/file.css" %}
    """
    node_instance = base_static(parser, token)
    return node_cls(varname=node_instance.varname, path=node_instance.path)

