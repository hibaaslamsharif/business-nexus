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
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import RegisterView, LoginView, ProfileDetailView, ProfileUpdateView, chat_view, chat_simple_view
from users.api_views import UserListView, UserDeleteView, UserStatsView, EntrepreneursListView, InvestorsListView
from users.collaboration_views import SendCollaborationRequestView, CollaborationRequestListView, UpdateCollaborationRequestView
from chat.api_views import SendMessageView
from chat.views import ChatHistoryView

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Auth API endpoints
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/login/', LoginView.as_view(), name='api_login'),

    # User Management API
    path('api/users/list/', UserListView.as_view(), name='api_users_list'),
    path('api/users/delete/<int:user_id>/', UserDeleteView.as_view(), name='api_user_delete'),
    path('api/users/stats/', UserStatsView.as_view(), name='api_users_stats'),
    path('api/entrepreneurs/', EntrepreneursListView.as_view(), name='api_entrepreneurs'),
    path('api/investors/', InvestorsListView.as_view(), name='api_investors'),

    # Chat API
    path('api/chat/<int:user_id>/', ChatHistoryView.as_view(), name='api_chat_history'),
    path('api/send-message/', SendMessageView.as_view(), name='api_send_message'),
    
    # Collaboration API
    path('api/send-request/', SendCollaborationRequestView.as_view(), name='api_send_request'),
    path('api/requests/', CollaborationRequestListView.as_view(), name='api_requests_list'),
    path('api/request/<int:request_id>/', UpdateCollaborationRequestView.as_view(), name='api_update_request'),

    # Pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('dashboard_investor/', TemplateView.as_view(template_name='dashboard_investor.html'), name='dashboard_investor'),
    path('dashboard_entrepreneur/', TemplateView.as_view(template_name='dashboard_entrepreneur.html'), name='dashboard_entrepreneur'),
    path('profile/<int:id>/', TemplateView.as_view(template_name='profile.html'), name='profile_view'),
    path('profile/edit/', TemplateView.as_view(template_name='profile_edit.html'), name='profile_edit'),
    path('chat/<int:user_id>/', chat_view, name='chat'),
    path('chat_simple/<int:user_id>/', chat_simple_view, name='chat_simple'),
    path('register_simple/', TemplateView.as_view(template_name='register_simple.html'), name='register_simple'),
    path('login_simple/', TemplateView.as_view(template_name='login_simple.html'), name='login_simple'),
    path('admin/', TemplateView.as_view(template_name='admin.html'), name='admin_panel'),
]
