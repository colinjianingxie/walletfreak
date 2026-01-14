from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.services import db

@login_required
@require_POST
def toggle_benefit_usage(request, user_card_id, benefit_id):
    """Toggle benefit usage tracking"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_benefit_usage(request, user_card_id, benefit_id):
    """Update benefit usage amount"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        usage_amount = float(request.POST.get('amount', 0))
        period_key = request.POST.get('period_key')
        is_full = request.POST.get('is_full') == 'true'
        increment = request.POST.get('increment') == 'true'
        
        db.update_benefit_usage(uid, user_card_id, benefit_id, usage_amount, period_key=period_key, is_full=is_full, increment=increment)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_benefit_ignore_status(request, user_card_id, benefit_id):
    """Toggle ignore status for a benefit"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        is_ignored = request.POST.get('is_ignored') == 'true'
        
        db.toggle_benefit_ignore(uid, user_card_id, benefit_id, is_ignored)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
