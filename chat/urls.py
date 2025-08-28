from django.urls import path
from . import views
from .api_views import SendMessageView, ChatHistoryView, UnreadCountView, MarkConversationReadView, PresenceView, UnreadByUserView
from django.urls import re_path

app_name = 'chat'

# WebSocket URL patterns (for Channels)
from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<other_user_id>\w+)/$', ChatConsumer.as_asgi()),
]

# HTTP URL patterns (for Django REST Framework)
urlpatterns = [
    path('simple/<int:user_id>/', views.simple_chat_view, name='simple_chat'),
    
    # API Endpoints
    # Place specific routes BEFORE the catch-all user_id route to avoid shadowing
    path('api/messages/send/', SendMessageView.as_view(), name='send_message'),
    path('api/messages/unread-count/', UnreadCountView.as_view(), name='unread_count'),
    path('api/messages/unread-by-user/', UnreadByUserView.as_view(), name='unread_by_user'),
    path('api/messages/mark-read/', MarkConversationReadView.as_view(), name='mark_conversation_read'),
    # Chat history for a specific user (restrict to int to prevent matching words like 'unread-count')
    path('api/messages/<int:user_id>/', ChatHistoryView.as_view(), name='chat_history'),
    path('api/presence/', PresenceView.as_view(), name='presence'),
]
