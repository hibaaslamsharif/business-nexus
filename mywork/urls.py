"""
URL configuration for mywork project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView, RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.static import serve
from django.http import HttpResponse, FileResponse
import os

# Import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from chat.urls import websocket_urlpatterns as chat_websocket_urls
from users.views import RegisterView, LoginView
from users.api_views import UserListView, UserDeleteView, UserStatsView, EntrepreneursListView, InvestorsListView
from users.collaboration_views import SendCollaborationRequestView, CollaborationRequestListView, UpdateCollaborationRequestView
from users.views import (
    dashboard_view, chat_view, chat_simple_view,
    ProfileDetailView, ProfileUpdateView, public_profile_view,
    ProfileViewsListView, ProfileViewsMarkSeenView,
)
from .views import serve_frontend

# Serve frontend files
def serve_react(request, path=''):
    if path != '' and os.path.exists(os.path.join(settings.FRONTEND_DIR, path)):
        return serve(request, path, document_root=settings.FRONTEND_DIR)
    return serve(request, 'index.html', document_root=settings.FRONTEND_DIR)

def serve_frontend(request, path=''):
    """Serve frontend files with proper content types and pretty URL support"""
    # Default to index.html
    if path in ('', '/'):  
        candidate = 'index.html'
    else:
        # Normalize and try to resolve pretty URLs to .html files
        normalized = path.lstrip('/')
        # If it's a directory-style path (no extension), try .html
        root, ext = os.path.splitext(normalized)
        candidates = [normalized]
        if not ext:
            candidates.insert(0, f"{normalized.rstrip('/')}.html")
        # Always fall back to index.html for SPA routes
        candidates.append('index.html')

        # Pick the first existing file
        candidate = None
        for c in candidates:
            p = os.path.join(settings.FRONTEND_DIR, c)
            if os.path.exists(p) and not os.path.isdir(p):
                candidate = c
                break
        if candidate is None:
            candidate = 'index.html'

    file_path = os.path.join(settings.FRONTEND_DIR, candidate)

    # Determine content type from selected file
    content_type = 'text/html'
    if candidate.endswith('.css'):
        content_type = 'text/css'
    elif candidate.endswith('.js'):
        content_type = 'application/javascript'
    elif candidate.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        ext = candidate.split('.')[-1]
        content_type = 'image/' + ext

    with open(file_path, 'rb') as f:
        return HttpResponse(f.read(), content_type=content_type)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Named login route for login_required redirects -> send to static login page
    path('login/', RedirectView.as_view(url='/login_simple/'), name='login'),
    # Provide a named logout route for templates; redirect to static login page (JWT clears on client)
    path('logout/', RedirectView.as_view(url='/login_simple/'), name='logout'),
    
    # API endpoints
    path('api/auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # WebSocket
    path('ws/chat/<str:other_user_id>/', include(chat_websocket_urls)),
    
    # Serve static files in development
    # Serve frontend static assets (CSS/JS/images) in dev
    # Direct maps
    re_path(r'^css/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.FRONTEND_DIR, 'css')}),
    re_path(r'^js/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.FRONTEND_DIR, 'js')}),
    # Aliases for /static/css and /static/js must come BEFORE the general /static pattern
    re_path(r'^static/css/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.FRONTEND_DIR, 'css')}),
    re_path(r'^static/js/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.FRONTEND_DIR, 'js')}),
    # General /static route (images or other assets inside /static directory)
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.FRONTEND_DIR, 'static')}),
    
    # WebSocket URLs (keep a single include)
    path('ws/chat/<str:other_user_id>/', include(chat_websocket_urls)),

    # Auth API endpoints
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/login/', LoginView.as_view(), name='api_login'),

    # User Management API
    path('api/users/list/', UserListView.as_view(), name='api_users_list'),
    path('api/users/delete/<int:user_id>/', UserDeleteView.as_view(), name='api_user_delete'),
    path('api/users/stats/', UserStatsView.as_view(), name='api_users_stats'),
    path('api/entrepreneurs/', EntrepreneursListView.as_view(), name='api_entrepreneurs'),
    path('api/investors/', InvestorsListView.as_view(), name='api_investors'),
    path('api/profile/<int:id>/', ProfileDetailView.as_view(), name='api_profile_detail'),
    path('api/profile/', ProfileUpdateView.as_view(), name='api_profile_update'),
    path('api/profile-views/', ProfileViewsListView.as_view(), name='api_profile_views'),
    path('api/profile-views/seen/', ProfileViewsMarkSeenView.as_view(), name='api_profile_views_seen'),

    # Dashboard
    path('dashboard/', login_required(dashboard_view), name='dashboard'),
    
    # Chat URLs - Include all chat-related URLs from the chat app
    path('chat/', include('chat.urls')),  # This includes chat/simple/<int:user_id>/
    # path('api/chat/<int:user_id>/', ChatHistoryView.as_view(), name='api_chat_history'),  # Not implemented
    # path('api/send-message/', SendMessageView.as_view(), name='api_send_message'),  # Not implemented
    
    # Collaboration API
    path('api/send-request/', SendCollaborationRequestView.as_view(), name='api_send_request'),
    path('api/requests/', CollaborationRequestListView.as_view(), name='api_requests_list'),
    path('api/request/<int:request_id>/', UpdateCollaborationRequestView.as_view(), name='api_update_request'),

    # Pages
    path('dashboard_investor/', TemplateView.as_view(template_name='dashboard_investor.html'), name='dashboard_investor'),
    path('dashboard_entrepreneur/', TemplateView.as_view(template_name='dashboard_entrepreneur.html'), name='dashboard_entrepreneur'),
    path('profile/<int:id>/', public_profile_view, name='profile_view'),
    path('profile/edit/', TemplateView.as_view(template_name='profile_edit.html'), name='profile_edit'),
    path('chat_legacy/<int:user_id>/', chat_view, name='chat_legacy'),  # Keeping this as a fallback for any existing links
    path('chat_simple/<int:user_id>/', chat_simple_view, name='chat_simple'),  # Direct chat URL
    path('admin-panel/', TemplateView.as_view(template_name='admin.html'), name='admin_panel'),
    
    # Finally, serve frontend (SPA) catch-all at the end so APIs/admin still work
    re_path(r'^$', serve_frontend, name='home'),
    re_path(r'^(?P<path>.*)$', serve_frontend),
]
