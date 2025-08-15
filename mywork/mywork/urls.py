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
from django.urls import path
from django.views.generic import TemplateView
from users.views import (
    RegisterView, LoginView,
    ProfileDetailView, ProfileUpdateView,
    EntrepreneursListView, InvestorsListView,
    CollaborationRequestCreateView, CollaborationRequestListView, CollaborationRequestUpdateView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth API endpoints
    path('auth/register/', RegisterView.as_view(), name='api_register'),
    path('auth/login/', LoginView.as_view(), name='api_login'),

    # Profiles API
    path('api/profile/<int:id>/', ProfileDetailView.as_view(), name='api_profile_detail'),
    path('api/profile/', ProfileUpdateView.as_view(), name='api_profile_update'),
    path('api/entrepreneurs/', EntrepreneursListView.as_view(), name='api_entrepreneurs'),
    path('api/investors/', InvestorsListView.as_view(), name='api_investors'),

    # Collaboration API
    path('api/request/', CollaborationRequestCreateView.as_view(), name='api_request_create'),
    path('api/requests/', CollaborationRequestListView.as_view(), name='api_request_list'),
    path('api/request/<int:id>/', CollaborationRequestUpdateView.as_view(), name='api_request_update'),

    # Pages
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('dashboard_investor/', TemplateView.as_view(template_name='dashboard_investor.html'), name='dashboard_investor'),
    path('dashboard_entrepreneur/', TemplateView.as_view(template_name='dashboard_entrepreneur.html'), name='dashboard_entrepreneur'),
    path('profile/<int:id>/', TemplateView.as_view(template_name='profile.html'), name='profile_view'),
    path('profile/edit/', TemplateView.as_view(template_name='profile_edit.html'), name='profile_edit'),
]
