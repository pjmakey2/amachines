from django.urls import re_path
from OptsIO import consumers

websocket_urlpatterns = [
    re_path(r'ws/tasks/$', consumers.TaskNotificationConsumer.as_asgi()),
]
