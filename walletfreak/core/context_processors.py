import json
from django.conf import settings

def firebase_config(request):
    return {
        'firebase_config_json': json.dumps(settings.FIREBASE_CLIENT_CONFIG)
    }
