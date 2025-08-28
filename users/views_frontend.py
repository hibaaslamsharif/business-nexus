import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.views.static import serve

def index_view(request):
    """Serve the main frontend page"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Try to serve index.html from the frontend directory
    index_path = os.path.join(settings.FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')
    return render(request, 'index.html')

def serve_frontend(request, path=''):
    """Serve frontend static files"""
    path = os.path.join(settings.FRONTEND_DIR, path)
    if os.path.exists(path):
        return FileResponse(open(path, 'rb'))
    return HttpResponse('Not found', status=404)

@login_required
def dashboard_redirect(request):
    """Redirect to the appropriate dashboard based on user role"""
    if request.user.role == 'investor':
        return render(request, 'dashboard_investor.html')
    else:
        return render(request, 'dashboard_entrepreneur.html')
