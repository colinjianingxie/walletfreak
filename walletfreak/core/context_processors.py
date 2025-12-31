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
            # Reuse profile fetched in middleware
            if hasattr(request, 'user_profile'):
                user_profile = request.user_profile
            else:
                # Fallback if middleware didn't run (e.g. tests)
                user_profile = db.get_user_profile(uid)

            try:
                # Cache wallet count
                from django.core.cache import cache
                wallet_key = f'wallet_count_{uid}'
                wallet_count = cache.get(wallet_key)
                
                if wallet_count is None:
                    user_cards = db.get_user_cards(uid)
                    wallet_count = len(user_cards)
                    cache.set(wallet_key, wallet_count, 300) # 5 mins
                
                # Get assigned personality details if available
                personality_slug = None
                if user_profile:
                    personality_slug = user_profile.get('assigned_personality')
                
                # Default to 'student-starter' if not set
                if not personality_slug:
                    personality_slug = 'student-starter'
                
                if personality_slug:
                    # Cache personality
                    pers_key = f'personality_{personality_slug}'
                    assigned_personality = cache.get(pers_key)
                    
                    if assigned_personality is None:
                        assigned_personality = db.get_personality_by_slug(personality_slug)
                        if assigned_personality:
                            cache.set(pers_key, assigned_personality, 300)
            except Exception:
                pass
            
    # Check premium status
    is_premium = False
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            is_premium = db.is_premium(uid)

    return {
        'wallet_count': wallet_count,
        'user_profile': user_profile,
        'assigned_personality': assigned_personality,
        'user_is_premium': is_premium
    }
