"""
Middleware to handle Firebase authentication for Django admin access.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import login
from .admin_auth import FirebaseAdminBackend
from .services import FirestoreService

db = FirestoreService()


class FirebaseAdminMiddleware:
    """
    Middleware that checks Firebase authentication for admin access.
    Redirects to login if user tries to access /admin/ without proper permissions.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_backend = FirebaseAdminBackend()
    
    def __call__(self, request):
        # Check if user is authenticated via Firebase session
        firebase_uid = request.session.get('uid')
        
        # Attach empty profile by default
        request.user_profile = None

        if firebase_uid:
            # Try to get from cache first
            from django.core.cache import cache
            cache_key = f'user_profile_{firebase_uid}'
            user_profile = cache.get(cache_key)
            
            if user_profile is None:
                user_profile = db.get_user_profile(firebase_uid)
                if user_profile:
                    # Cache for 5 minutes
                    cache.set(cache_key, user_profile, 300)
            
            # Attach to request for downstream use (context processors, views)
            request.user_profile = user_profile
            
            if request.user.is_authenticated and user_profile:
                # Sync Django user permissions with Firestore on every request
                # Handle both Python True/False and JavaScript true/false
                is_super_staff = user_profile.get('is_super_staff', False)
                should_be_admin = (is_super_staff is True or is_super_staff == 'true' or is_super_staff == True)
                
                # Update Django user permissions if they don't match Firestore
                if should_be_admin and (not request.user.is_staff or not request.user.is_superuser):
                    request.user.is_staff = True
                    request.user.is_superuser = True
                    request.user.is_active = True
                    request.user.save()
                elif not should_be_admin and (request.user.is_staff or request.user.is_superuser):
                    request.user.is_staff = False
                    request.user.is_superuser = False
                    request.user.save()
        
        # Check if accessing admin without proper permissions
        if request.path.startswith('/admin/'):
            # Skip for static files and login page
            if request.path.startswith('/admin/static/') or request.path == '/admin/login/':
                return self.get_response(request)
            
            # Check if user is authenticated and has admin permissions
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)
            
            # Check for Firebase session and try to log in
            if firebase_uid and request.user_profile:
                user_profile = request.user_profile
                
                is_super_staff = user_profile.get('is_super_staff', False)
                if is_super_staff is True or is_super_staff == 'true' or is_super_staff == True:
                    # Try to get or create Django user for admin
                    from django.contrib.auth.models import User
                    try:
                        user = User.objects.get(username=firebase_uid)
                    except User.DoesNotExist:
                        # Create user
                        user = User.objects.create_user(
                            username=firebase_uid,
                            email=user_profile.get('email', ''),
                            password=None
                        )
                    
                    # Set admin permissions
                    user.is_staff = True
                    user.is_superuser = True
                    user.is_active = True
                    user.save()
                    
                    # Log user in for Django admin
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    return self.get_response(request)
            
            # No valid authentication - redirect to home
            return redirect('/')
        
        return self.get_response(request)