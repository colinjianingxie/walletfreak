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
            # Generate unique username
            username = db.generate_unique_username(first_name, last_name, uid)
            
            user_data = {
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
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


    
    personalities = db.get_personalities()
    
    # Determine best fit personality
    matched_personality = db.determine_best_fit_personality(active_cards)
    
    # Sync with DB if different (self-healing)
    if matched_personality:
        current_assigned = user_profile.get('assigned_personality')
        matched_id = matched_personality.get('id')
        
        if current_assigned != matched_id:
             # Calculate score for completeness
             user_card_slugs = set(c.get('card_id') for c in active_cards)
             personality_cards = set()
             for slot in matched_personality.get('slots', []):
                 personality_cards.update(slot.get('cards', []))
             overlap = len(user_card_slugs.intersection(personality_cards))
             
             db.update_user_personality(uid, matched_id, score=overlap)
             # Update local user_profile for context to be consistent immediately (though context uses 'user_profile' obj)
             user_profile['assigned_personality'] = matched_id
             user_profile['personality_score'] = overlap
    
    notification_preferences = db.get_user_notification_preferences(uid)

    context = {
        'user_profile': user_profile,
        'personalities': personalities,
        'matched_personality': matched_personality,
        'notification_preferences': notification_preferences,
    }
    return render(request, 'accounts/profile.html', context)



@csrf_exempt
@login_required
def ajax_update_notifications(request):
    """AJAX endpoint to update notification preferences"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        preferences = data.get('preferences')
        
        if not preferences:
            return JsonResponse({'status': 'error', 'message': 'No preferences provided'}, status=400)
            
        uid = request.session.get('uid')
        db.update_user_notification_preferences(uid, preferences)
        
        # Calculate Next Email Time
        next_email_formatted = "Pending..."
        try:
            from datetime import timedelta
            import datetime
            
            # Fetch fresh profile to get last sent time
            user = db.get_user_profile(uid)
            last_sent = user.get('last_benefit_email_sent_at')
            
            # Get freq from prefs
            benefit_prefs = preferences.get('benefit_expiration', {})
            freq_days = benefit_prefs.get('repeat_frequency', 7)
            
            # Convert to float for potentially small values (Test Mode)
            freq_days = float(freq_days)
            
            now = datetime.datetime.now(datetime.timezone.utc)
            
            if not last_sent:
                # Never sent, so it will send on next run (e.g. tomorrow morning or soon)
                # For UX, we can say "Within 24 hours" or "Soon"
                next_email_formatted = "Within 24 hours"
            else:
                # Calculate next run
                # last_sent is likely a datetime (from Firestore)
                next_run = last_sent + timedelta(days=freq_days)
                
                # Format
                if next_run <= now:
                     next_email_formatted = "Within 24 hours"
                else:
                    # Format as readable string
                    # e.g. "Dec 18, 2025 at 10:00 AM"
                    # Convert to local time if possible, but server time is easier
                    next_email_formatted = next_run.strftime("%b %d, %Y at %I:%M %p")
                    
        except Exception as e:
            print(f"Error calculating next email: {e}")
            next_email_formatted = "Unknown"
        
        return JsonResponse({'status': 'success', 'next_email_formatted': next_email_formatted})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@login_required
def ajax_sync_profile(request):
    """AJAX endpoint to sync profile changes from frontend"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    try:
        data = json.loads(request.body)
        uid = request.session.get('uid')
        
        # Handle Email Update
        if 'email' in data:
            email = data.get('email')
            request.user.email = email
            request.user.save()
            db.update_user_email(uid, email)
            
        # Handle Name Update
        if 'first_name' in data and 'last_name' in data:
            first_name = data.get('first_name').strip()
            last_name = data.get('last_name').strip()
            
            if not first_name:
                 return JsonResponse({'status': 'error', 'message': 'First name is required'}, status=400)
                 
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()
            
            db.update_user_name(uid, first_name, last_name)
            
        # Handle Username Update
        if 'username' in data:
            username = data.get('username').strip()
            # Simple validation
            if len(username) < 3:
                return JsonResponse({'status': 'error', 'message': 'Username must be at least 3 characters'}, status=400)
            
            # Regex validation (alphanumeric and underscore only)
            import re
            if not re.match(r'^[a-zA-Z0-9_]+$', username):
                return JsonResponse({'status': 'error', 'message': 'Username can only contain letters, numbers, and underscores'}, status=400)
                
            # Check uniqueness
            if db.is_username_taken(username, exclude_uid=uid):
                return JsonResponse({'status': 'error', 'message': 'Username is already taken'}, status=400)
            
            # Update in Firestore
            try:
                db.update_user_username(uid, username)
            except ValueError as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
                
        # Handle Avatar Update
        if 'avatar_slug' in data:
            avatar_slug = data.get('avatar_slug')
            if avatar_slug:
                photo_url = f"/static/images/personalities/{avatar_slug}.png"
                try:
                    db.update_user_avatar(uid, photo_url)
                except Exception as e:
                     return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def auth_action(request):
    """View to handle Firebase Auth actions (reset password, verify email)"""
    return render(request, 'accounts/auth_action.html')
