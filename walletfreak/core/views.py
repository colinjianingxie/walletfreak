from django.shortcuts import render
from django.conf import settings
from .services import db

def home(request):
    # Fetch personalities for the landing page
    personalities = []
    try:
        personalities = db.get_personalities()
    except Exception as e:
        print(f"Warning: Failed to fetch personalities: {e}")
        
    # Fetch blog posts for the landing page
    blogs = []
    try:
        blogs = db.get_blogs()[:3]  # Get latest 3 blog posts
    except Exception as e:
        print(f"Warning: Failed to fetch blog posts: {e}")
        
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
        'personalities': personalities,
        'blogs': blogs
    }
    return render(request, 'landing.html', context)

def quiz(request):
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'quiz.html', context)

def features(request):
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'features.html', context)
