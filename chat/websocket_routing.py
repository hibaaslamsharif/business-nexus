from django.urls import re_path
from . import consumers

# WebSocket URL patterns for Socket.IO
websocket_urlpatterns = [
    re_path(r'socket.io/', consumers.SocketIOConsumer.as_asgi()),
]

# This will be used in asgi.py
