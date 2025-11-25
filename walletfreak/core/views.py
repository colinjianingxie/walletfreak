from django.shortcuts import render
from django.conf import settings
from .services import db

def home(request):
    # Fetch personalities for the landing page
    # In a real scenario, we might want to cache this or just fetch a few
    personalities = []
    try:
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Firestore query timed out")
        
        # Set 3 second timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3)
        
        try:
            personalities = db.get_personalities()
        finally:
            signal.alarm(0)  # Cancel the alarm
            
    except TimeoutError:
        print("Warning: Firestore query timed out, using empty personalities list")
    except Exception as e:
        print(f"Warning: Failed to fetch personalities: {e}")
        
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
