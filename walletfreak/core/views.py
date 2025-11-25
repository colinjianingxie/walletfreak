from django.shortcuts import render
from django.conf import settings
from .services import db

def home(request):
    # Fetch personalities for the landing page
    # In a real scenario, we might want to cache this or just fetch a few
    try:
        personalities = db.get_personalities()
    except Exception:
        personalities = []
        
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
        'personalities': personalities
    }
    return render(request, 'landing.html', context)

def quiz(request):
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'quiz.html', context)
