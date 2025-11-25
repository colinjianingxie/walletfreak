from firebase_admin import auth
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class FirebaseAuthentication:
    @staticmethod
    def verify_token(id_token):
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None

    @staticmethod
    def get_or_create_user(decoded_token):
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        
        # Try to find existing user by username (we'll use uid as username)
        try:
            user = User.objects.get(username=uid)
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=uid,
                email=email,
                password=None # Unusable password
            )
            user.first_name = decoded_token.get('name', '').split(' ')[0]
            user.save()
        
        return user
