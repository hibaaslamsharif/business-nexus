from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(views.dashboard_view), name='dashboard'),  # Root URL points to dashboard
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', login_required(views.dashboard_view), name='dashboard'),
    path('profile/', login_required(views.profile_view), name='profile'),
    path('profile/edit/', login_required(views.ProfileUpdateView.as_view()), name='profile_edit'),
]
