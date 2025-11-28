from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from firebase_admin import auth, firestore
from core.services import db

def login_view(request):
    # Redirect to dashboard if already authenticated
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('dashboard')
    return render(request, 'accounts/login.html')

@csrf_exempt
def firebase_login(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
        
        if not id_token:
            return JsonResponse({'status': 'error', 'message': 'No token provided'}, status=400)

        # Verify the token with Firebase
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        
        # Split name
        first_name = ''
        last_name = ''
        if name:
            parts = name.split(' ', 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]
        
        # Get or create Django user
        user, created = User.objects.get_or_create(username=uid)
        
        # Always update name and email
        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        if created:
            user.set_unusable_password()
        user.save()
            
        # Create or Update Firestore profile
        # Check if exists to preserve other fields like personality and is_super_staff
        existing_profile = db.get_user_profile(uid)
        
        if not existing_profile:
            # New user - set defaults
            user_data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_super_staff': False,  # Default for new users
                'created_at': firestore.SERVER_TIMESTAMP
            }
            db.create_user_profile(uid, user_data)
        else:
            # Existing user - only update name/email, preserve is_super_staff and other fields
            user_data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
            # Use merge=True to preserve existing fields like is_super_staff
            db.db.collection('users').document(uid).set(user_data, merge=True)


        # Check if user has admin permissions and sync with Django
        updated_profile = db.get_user_profile(uid)
        if updated_profile:
            is_super_staff = updated_profile.get('is_super_staff', False)
            if is_super_staff is True or is_super_staff == 'true' or is_super_staff == True:
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
        
        # Log the user in
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        
        # Store UID in session for easy access
        request.session['uid'] = uid
        
        # Force session save to prevent race condition
        request.session.save()
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        print(f"Login error: {e}")  # Log error to console for debugging
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def logout_view(request):
    """Logout from both Django and clear Firebase session"""
    try:
        # Clear Firebase UID from session if it exists
        if 'uid' in request.session:
            del request.session['uid']
    except:
        pass
    
    # Django logout (clears Django session and user)
    logout(request)
    
    return JsonResponse({'status': 'success'})

def logout_redirect(request):
    """Logout and redirect to home"""
    try:
        # Clear Firebase UID from session if it exists
        if 'uid' in request.session:
            del request.session['uid']
    except:
        pass
    
    # Django logout (clears session and logs out user)
    logout(request)
    
    from django.shortcuts import redirect
    return redirect('home')

from django.contrib.auth.decorators import login_required

@login_required
def profile(request):
    uid = request.session.get('uid')
    user_profile = db.get_user_profile(uid)
    
    # Get user's active cards count
    active_cards = db.get_user_cards(uid, status='active')
    cards_count = len(active_cards)
    
    # Calculate total value from benefits (placeholder)
    total_value = 0
    for card in active_cards:
        card_def = db.get_card_by_slug(card['card_id'])
        if card_def and 'benefits' in card_def:
            for benefit in card_def['benefits']:
                if benefit.get('dollar_value'):
                    total_value += benefit.get('dollar_value', 0)
    
    context = {
        'user_profile': user_profile,
        'cards_count': cards_count,
        'total_value': total_value,
        'score': 740,  # Placeholder - would calculate based on actual data
        'utilization': 68,  # Placeholder - would calculate from actual usage
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def settings(request):
    uid = request.session.get('uid')
    user_profile = db.get_user_profile(uid)
    
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'accounts/settings.html', context)
