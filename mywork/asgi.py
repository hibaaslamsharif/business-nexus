"""
ASGI config for mywork project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywork.settings')

# Initialize Django
django.setup()

# Import for ASGI application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from mywork.jwt_auth_middleware import JwtAuthMiddlewareStack
from django.urls import re_path, path
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from chat.consumers import ChatConsumer

# Get default Django ASGI application
django_asgi_app = get_asgi_application()

# Import WebSocket URL patterns from chat app
from chat.urls import websocket_urlpatterns as chat_ws_urls

# Create ASGI application with both HTTP and WebSocket support
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddlewareStack(
            URLRouter(
                chat_ws_urls
            )
        )
    ),
})
