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
from django.http import HttpResponse, FileResponse, JsonResponse
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
    """Serve frontend assets with SPA fallback. Always return an HttpResponse."""
    import mimetypes

    # 1) Resolve the candidate file relative to FRONTEND_DIR
    if path in ('', '/'):  # root
        candidate = 'index.html'
    else:
        normalized = path.lstrip('/')
        root, ext = os.path.splitext(normalized)
        # Prefer pretty URL .html first, then literal path, then SPA index
        candidates = []
        if not ext:
            candidates.append(f"{normalized.rstrip('/')}.html")
        candidates.append(normalized)
        candidates.append('index.html')

        candidate = next(
            (c for c in candidates if os.path.exists(os.path.join(settings.FRONTEND_DIR, c)) and not os.path.isdir(os.path.join(settings.FRONTEND_DIR, c))),
            'index.html'
        )

    file_path = os.path.join(settings.FRONTEND_DIR, candidate)

    # 2) If file exists, stream it back with proper content type
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        mime, _ = mimetypes.guess_type(file_path)
        mime = mime or ('text/html' if candidate.endswith('.html') else 'application/octet-stream')
        # Binary for images and other binaries
        binary_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot')
        if candidate.endswith(binary_exts):
            return FileResponse(open(file_path, 'rb'), content_type=mime)
        # Text-like files
        with open(file_path, 'rb') as f:
            return HttpResponse(f.read(), content_type=mime)

    # 3) Fallback minimal page to avoid 500 on Render when frontend isn't present
    fallback_html = f"""
    <!doctype html>
    <html>
        <head>
            <meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>Business Nexus</title>
            <link rel='stylesheet' href='/static/css/style.css'>
        </head>
        <body style='padding:24px;font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#0f172a;color:#e5e7eb'>
            <h1>Business Nexus</h1>
            <p>Frontend file not found at <code>{file_path}</code>.</p>
            <p>FRONTEND_DIR: <code>{settings.FRONTEND_DIR}</code></p>
            <p>Make sure the <code>frontend</code> folder is deployed and accessible, or set <code>STATICFILES_DIRS</code> correctly.</p>
            <p><a href='/login_simple/' class='button'>Go to Login</a></p>
        </body>
    </html>
    """
    return HttpResponse(fallback_html, content_type='text/html')

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
    path('healthz', lambda r: JsonResponse({'ok': True}), name='healthz'),
    # Debug: quickly inspect where the frontend is being served from
    path('debug/frontend-dir', lambda r: JsonResponse({
        'FRONTEND_DIR': settings.FRONTEND_DIR,
        'exists': os.path.isdir(settings.FRONTEND_DIR),
        'has_index': os.path.exists(os.path.join(settings.FRONTEND_DIR, 'index.html'))
    })),
    path('debug/frontend-dir/', lambda r: JsonResponse({
        'FRONTEND_DIR': settings.FRONTEND_DIR,
        'exists': os.path.isdir(settings.FRONTEND_DIR),
        'has_index': os.path.exists(os.path.join(settings.FRONTEND_DIR, 'index.html'))
    })),
    
    # Finally, serve frontend (SPA) catch-all at the end so APIs/admin still work
    re_path(r'^$', serve_frontend, name='home'),
    re_path(r'^(?P<path>.*)$', serve_frontend),
]
