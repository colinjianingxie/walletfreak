from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.services import db
import json

@login_required
@require_POST
def submit_personality_survey(request):
    """Submit personality survey responses"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        personality_id = data.get('personality_id')
        responses = data.get('responses', {})
        card_ids = data.get('card_ids', [])
        
        # Save survey
        survey_id = db.save_personality_survey(uid, personality_id, responses, card_ids)
        
        # Update user's assigned personality
        db.update_user_personality(uid, personality_id)
        
        return JsonResponse({'success': True, 'survey_id': survey_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def publish_personality(request):
    """Publish user's personality (make it public)"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        # Update user profile to make personality public
        db.update_document('users', uid, {'personality_public': True})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
