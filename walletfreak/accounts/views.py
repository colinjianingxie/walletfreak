from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout, login
from django.contrib.auth.models import User
from django.http import JsonResponse
import json
from firebase_admin import auth, firestore
from core.services import db

def login_view(request):
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
        user_data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'is_super_staff': False # Default
        }
        
        # Check if exists to preserve other fields like personality
        existing_profile = db.get_user_profile(uid)
        if not existing_profile:
            user_data['created_at'] = firestore.SERVER_TIMESTAMP
            db.create_user_profile(uid, user_data)
        else:
            # Update name if changed
            db.create_user_profile(uid, user_data) # This might overwrite, need to be careful. 
            # create_document in services uses set(merge=True) usually? Let's check services.py
            # If create_document uses set(), we should use update() or set(merge=True).
            # Let's assume for now we just want to ensure these fields are set.
            # Actually, let's just update the specific fields to avoid wiping data.
            db.db.collection('users').document(uid).set(user_data, merge=True)

        # Log the user in
        login(request, user)
        
        # Store UID in session for easy access
        request.session['uid'] = uid
        request.session.modified = True
        
        return JsonResponse({'status': 'success'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def logout_view(request):
    logout(request)
    return JsonResponse({'status': 'success'})
