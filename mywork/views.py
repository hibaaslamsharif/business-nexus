from django.shortcuts import render
from django.http import HttpResponse, FileResponse
import os
from django.conf import settings

def serve_frontend(request, path=''):
    """Serve frontend files with proper content types"""
    if path == '':
        path = 'index.html'
    
    file_path = os.path.join(settings.FRONTEND_DIR, path)
    
    # Check if file exists
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        # If file doesn't exist, serve index.html for SPA routing
        file_path = os.path.join(settings.FRONTEND_DIR, 'index.html')
    
    # Determine content type
    content_type = 'text/html'
    if path.endswith('.css'):
        content_type = 'text/css'
    elif path.endswith('.js'):
        content_type = 'application/javascript'
    elif path.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        content_type = f'image/{path.split(".")[-1]}'
    
    with open(file_path, 'rb') as f:
        return HttpResponse(f.read(), content_type=content_type)
