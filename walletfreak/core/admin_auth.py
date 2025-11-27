"""
Custom authentication backend for Django admin using Firebase authentication.
Checks if user has is_super_staff=True in Firestore before granting admin access.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from firebase_admin import auth
from .services import FirestoreService

db = FirestoreService()


class FirebaseAdminBackend(BaseBackend):
    """
    Custom authentication backend that uses Firebase tokens
    and checks Firestore for is_super_staff permission.
    """
    
    def authenticate(self, request, firebase_token=None, **kwargs):
        """
        Authenticate user with Firebase token and check admin permissions.
        """
        if not firebase_token:
            return None
        
        try:
            # Verify Firebase token
            decoded_token = auth.verify_id_token(firebase_token)
            uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            
            # Get user profile from Firestore
            user_profile = db.get_user_profile(uid)
            
            # Check if user has super_staff permission
            if not user_profile or not user_profile.get('is_super_staff', False):
                return None
            
            # Get or create Django user
            try:
                user = User.objects.get(username=uid)
            except User.DoesNotExist:
                # Create new user with admin privileges
                user = User.objects.create_user(
                    username=uid,
                    email=email,
                    password=None  # Unusable password - Firebase handles auth
                )
                user.first_name = decoded_token.get('name', '').split(' ')[0] if decoded_token.get('name') else ''
                user.last_name = ' '.join(decoded_token.get('name', '').split(' ')[1:]) if decoded_token.get('name') else ''
            
            # Set admin permissions based on Firestore
            user.is_staff = user_profile.get('is_super_staff', False)
            user.is_superuser = user_profile.get('is_super_staff', False)
            user.save()
            
            return user
            
        except Exception as e:
            print(f"Firebase admin authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID and verify they still have admin permissions.
        """
        try:
            user = User.objects.get(pk=user_id)
            
            # Verify user still has admin permissions in Firestore
            user_profile = db.get_user_profile(user.username)
            if user_profile and user_profile.get('is_super_staff', False):
                return user
            
            # Revoke admin access if permission was removed
            if user.is_staff or user.is_superuser:
                user.is_staff = False
                user.is_superuser = False
                user.save()
            
            return None
            
        except User.DoesNotExist:
            return None