import json
from django.conf import settings
from .services import db

def firebase_config(request):
    return {
        'firebase_config_json': json.dumps(settings.FIREBASE_CLIENT_CONFIG)
    }

def wallet_status(request):
    wallet_count = 0
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                user_cards = db.get_user_cards(uid)
                wallet_count = len(user_cards)
            except Exception:
                pass
            
    return {'wallet_count': wallet_count}
