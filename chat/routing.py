from django.urls import re_path
from . import consumers

from . import consumers_notify

websocket_urlpatterns = [
    # Allows connection to ws://127.0.0.1:8000/ws/chat/Lounge/
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers_notify.NotificationConsumer.as_asgi()),
]