from django.urls import path, re_path
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.views import TokenRefreshView
from .views import dtmpl, iom, set_auth, set_logout, show_media_file, \
                glogin, api_dtmpl, api_iom, api_isauth, glogout, hub_ui, base, gregister

urlpatterns = [
    path('set_auth/', set_auth, name='set_auth'),
    path('set_logout/', set_logout, name='set_logout'),
    path('iom/', login_required(iom), name='iom'),
    path('dtmpl/', login_required(dtmpl), name='dtmpl'),
    path('api_dtmpl/', api_dtmpl, name='api_dtmpl'),
    path('api_iom/', api_iom, name='api_iom'),
    path('api_isauth/', api_isauth, name='api_isauth'),
    path('api_refresh/', TokenRefreshView.as_view(), name='api_refresh'),
    path('glogin/', glogin, name='glogin'),
    path('glogout/', glogout, name='glogout'),
    path('register/', gregister, name='gregister'),
    re_path(r'show_media_file/(?P<filename>[0-9\w|\/\.\-]+)', show_media_file, name='show_media_file'),
    # Vista principal de apps (launcher/sidebar)
    path('apps/', login_required(base), name='apps'),
]