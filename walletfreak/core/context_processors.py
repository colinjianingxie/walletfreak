import json
from django.conf import settings
from .services import db

def firebase_config(request):
    return {
        'firebase_config_json': json.dumps(settings.FIREBASE_CLIENT_CONFIG)
    }

def wallet_status(request):
    user_profile = None
    assigned_personality = None
    wallet_count = 0
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                # Get wallet count
                user_cards = db.get_user_cards(uid)
                wallet_count = len(user_cards)
                
                # Get user profile for avatar/name
                user_profile = db.get_user_profile(uid)
                
                # Get assigned personality details if available
                if user_profile and user_profile.get('assigned_personality'):
                    assigned_personality = db.get_personality_by_slug(user_profile.get('assigned_personality'))
            except Exception:
                pass
            
    return {
        'wallet_count': wallet_count,
        'user_profile': user_profile,
        'assigned_personality': assigned_personality
    }
