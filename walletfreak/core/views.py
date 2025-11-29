from django.shortcuts import render, redirect
from django.conf import settings
from .services import db

def home(request):
    # Fetch personalities for the landing page
    personalities = []
    try:
        personalities = db.get_personalities()
    except Exception as e:
        print(f"Warning: Failed to fetch personalities: {e}")
        
    # Fetch published blog posts for the landing page
    blog_posts = []
    try:
        blog_posts = db.get_blogs(status='published', limit=3)  # Get latest 3 published blog posts
    except Exception as e:
        print(f"Warning: Failed to fetch blog posts: {e}")
        
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
        'personalities': personalities,
        'blog_posts': blog_posts
    }
    return render(request, 'landing.html', context)


def features(request):
    # Redirect to dashboard if user is authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'features.html', context)
