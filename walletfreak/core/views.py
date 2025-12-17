from django.shortcuts import render, redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .services import db

def home(request):
    # Redirect to dashboard if user is authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')

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


@csrf_exempt
def run_notification_cron(request):
    """
    Cron endpoint to trigger unused benefit notifications.
    Protected by a simple secret query param.
    Usage: /cron/emails/?secret=YOUR_CRON_SECRET
    """
    import os
    from django.core.management import call_command
    
    # Simple security check
    # In production, set CRON_SECRET env var
    # Default to a known value for local dev or if unset (Not recommended for prod without env var)
    cron_secret = os.environ.get('CRON_SECRET', 'temp_insecure_secret_change_me')
    
    request_secret = request.GET.get('secret')
    
    if request_secret != cron_secret:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        
    try:
        # Run the command
        # We catch output to return it
        from io import StringIO
        out = StringIO()
        call_command('check_unused_credits', send_email=True, stdout=out)
        
        return JsonResponse({
            'status': 'success', 
            'output': out.getvalue()
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
