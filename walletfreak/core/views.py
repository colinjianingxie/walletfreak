from django.shortcuts import render, redirect
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .services import db
import firebase_admin
from firebase_admin import auth
from django.core.mail import send_mail
from django.contrib import messages

@login_required
def get_firebase_token(request):
    """
    Generate a Firebase Custom Token for the logged-in user.
    This allows the frontend to authenticate with Firebase using the Django session.
    """
    try:
        uid = request.session.get('uid')
        if not uid:
            return JsonResponse({'error': 'No Firebase UID in session'}, status=400)
            
        # Create a custom token for this UID
        # note: auth.create_custom_token returns bytes in some versions, string in others.
        # Ensure it's decoded if bytes.
        custom_token = auth.create_custom_token(uid)
        
        if isinstance(custom_token, bytes):
            custom_token = custom_token.decode('utf-8')
            
        return JsonResponse({'token': custom_token})
    except Exception as e:
        print(f"Error generating custom token: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def home(request):
    # Redirect to dashboard if user is authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Fetch personalities for the landing page
    personalities = cache.get('home_personalities')
    if not personalities:
        try:
            personalities = db.get_personalities()
            cache.set('home_personalities', personalities, 60 * 60)  # Cache for 1 hr
        except Exception as e:
            print(f"Warning: Failed to fetch personalities: {e}")
            personalities = []
        
    # Fetch published blog posts for the landing page
    blog_posts = cache.get('home_latest_blog_posts')
    if not blog_posts:
        try:
            blog_posts = db.get_blogs(status='published', limit=3)  # Get latest 3 published blog posts
            cache.set('home_latest_blog_posts', blog_posts, 60 * 60) # Cache for 1 hr
        except Exception as e:
            print(f"Warning: Failed to fetch blog posts: {e}")
            blog_posts = []
        
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


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_content = request.POST.get('message')
        
        # Construct email content
        # Subject: Contact Email from <name>: <email>
        subject = f"Contact Email from {name}: {email}"
        
        text_content = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_content}"
        
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>New Contact Request</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="white-space: pre-wrap;">{message_content}</p>
        </div>
        """
        
        try:
            # Use Firestore Trigger Email via db service instead of direct SMTP
            # This matches check_unused_benefits.py implementation
            result = db.send_email_notification(
                to='colin@walletfreak.com',
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if result:
                messages.success(request, "Thanks for reaching out! We'll be in touch shortly.")
            else:
                # If result is None, something failed in queuing
                print("Failed to queue email to Firestore.")
                messages.error(request, "There was an error sending your message. Please try again later.")
                
        except Exception as e:
            # Print the full error to console for debugging
            print(f"Error sending email: {e}") 
            messages.error(request, "There was an error sending your message. Please try again later.")
            
        return redirect('contact')
        
    return render(request, 'contact.html')


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
        call_command('check_unused_benefits', send_email=True, stdout=out)
        
        return JsonResponse({
            'status': 'success', 
            'output': out.getvalue()
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def run_cleanup_cron(request):
    """
    Cron endpoint to clean up sent emails.
    Protected by secret.
    """
    import os
    from django.core.management import call_command
    from io import StringIO
    from django.http import JsonResponse
    
    cron_secret = os.environ.get('CRON_SECRET', 'temp_insecure_secret_change_me')
    request_secret = request.GET.get('secret')
    
    if request_secret != cron_secret:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)
        
    try:
        out = StringIO()
        call_command('cleanup_sent_emails', stdout=out)
        return JsonResponse({'status': 'success', 'output': out.getvalue()})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def pricing(request):
    context = {
        'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
        'price_monthly': settings.STRIPE_PRICE_MONTHLY,
        'price_yearly': settings.STRIPE_PRICE_YEARLY,
    }
    return render(request, 'core/pricing.html', context)


def privacy_policy(request):
    context = {
         'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'core/privacy_policy.html', context)


def terms_of_service(request):
    context = {
         'firebase_config': settings.FIREBASE_CLIENT_CONFIG,
    }
    return render(request, 'core/terms_of_service.html', context)
