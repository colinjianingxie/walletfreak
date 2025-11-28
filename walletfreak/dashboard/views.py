from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from core.services import db
from datetime import datetime
import json


@login_required
def dashboard(request):
    """Main dashboard view showing user's cards and personality"""
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    # Get user's cards grouped by status
    try:
        active_cards = db.get_user_cards(uid, status='active')
        inactive_cards = db.get_user_cards(uid, status='inactive')
        eyeing_cards = db.get_user_cards(uid, status='eyeing')
    except Exception as e:
        print(f"Error fetching user cards: {e}")
        active_cards = []
        inactive_cards = []
        eyeing_cards = []
    
    # Get user's assigned personality
    try:
        assigned_personality = db.get_user_assigned_personality(uid)
    except Exception as e:
        print(f"Error fetching personality: {e}")
        assigned_personality = None
    
    # Get all available cards for adding
    try:
        all_cards = db.get_cards()
    except Exception as e:
        print(f"Error fetching all cards: {e}")
        all_cards = []
    
    # Prepare available cards JSON for JavaScript
    available_cards_json = json.dumps([{
        'id': card['id'],
        'name': card['name'],
        'issuer': card['issuer']
    } for card in all_cards])
    
    # Calculate benefits and values
    all_benefits = []
    total_used_value = 0
    total_potential_value = 0
    
    for card in active_cards:
        try:
            # Get full card details
            card_details = db.get_card_by_slug(card['card_id'])
            if not card_details:
                continue
            
            # Process each benefit
            for idx, benefit in enumerate(card_details.get('benefits', [])):
                dollar_value = benefit.get('dollar_value')
                if dollar_value and dollar_value > 0:
                    benefit_id = f"benefit_{idx}"
                    
                    # Get usage from user's card data
                    benefit_usage = card.get('benefit_usage', {}).get(benefit_id, {})
                    used_amount = benefit_usage.get('used', 0)
                    
                    # Check if fully used
                    is_used = used_amount >= dollar_value
                    
                    all_benefits.append({
                        'card_id': card['id'],
                        'card_name': card_details['name'],
                        'benefit_id': benefit_id,
                        'benefit_name': benefit['description'][:50] + '...' if len(benefit['description']) > 50 else benefit['description'],
                        'amount': dollar_value,
                        'used': used_amount,
                        'is_used': is_used,
                        'frequency': benefit.get('category', 'Permanent')
                    })
                    
                    total_used_value += used_amount
                    total_potential_value += dollar_value
        except Exception as e:
            print(f"Error processing card benefits: {e}")
            continue
    
    context = {
        'active_cards': active_cards,
        'inactive_cards': inactive_cards,
        'eyeing_cards': eyeing_cards,
        'assigned_personality': assigned_personality,
        'all_cards': all_cards,
        'available_cards_json': available_cards_json,
        'all_benefits': all_benefits,
        'total_used_value': total_used_value,
        'total_potential_value': total_potential_value,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def wallet(request):
    """Wallet view showing detailed card management"""
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    # Get all user's cards
    try:
        user_cards = db.get_user_cards(uid)
    except Exception as e:
        print(f"Error fetching user cards: {e}")
        user_cards = []
    
    # Enrich with full card details
    enriched_cards = []
    for user_card in user_cards:
        try:
            card_details = db.get_card_by_slug(user_card['card_id'])
            if card_details:
                user_card['details'] = card_details
                enriched_cards.append(user_card)
        except Exception as e:
            print(f"Error fetching card details: {e}")
            continue
    
    context = {
        'user_cards': enriched_cards,
    }
    
    return render(request, 'dashboard/wallet.html', context)


@login_required
@require_POST
def add_card(request, card_id):
    """Add a card to user's wallet"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        status = request.POST.get('status', 'active')
        anniversary_date = request.POST.get('anniversary_date', None)
        
        success = db.add_card_to_user(uid, card_id, status=status, anniversary_date=anniversary_date)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_card_status(request, user_card_id):
    """Update the status of a user's card"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        new_status = request.POST.get('status')
        if new_status not in ['active', 'inactive', 'eyeing']:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        db.update_card_status(uid, user_card_id, new_status)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def remove_card(request, user_card_id):
    """Remove a card from user's wallet"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        db.remove_card_from_user(uid, user_card_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_anniversary(request, user_card_id):
    """Update the anniversary date for a user's card"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        anniversary_date = request.POST.get('anniversary_date')
        db.update_card_details(uid, user_card_id, {'anniversary_date': anniversary_date})
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def toggle_benefit_usage(request, user_card_id, benefit_id):
    """Toggle benefit usage tracking"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        # This would toggle the benefit tracking on/off
        # Implementation depends on your benefit tracking structure
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
        db.update_benefit_usage(uid, user_card_id, benefit_id, usage_amount)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def personality_survey(request):
    """Display personality survey"""
    try:
        personalities = db.get_personalities()
    except Exception as e:
        print(f"Error fetching personalities: {e}")
        personalities = []
    
    context = {
        'personalities': personalities,
    }
    
    return render(request, 'dashboard/personality_survey.html', context)


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
def personality_results(request):
    """Display personality results"""
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    try:
        assigned_personality = db.get_user_assigned_personality(uid)
    except Exception as e:
        print(f"Error fetching personality: {e}")
        assigned_personality = None
    
    # Get recommended cards for this personality
    recommended_cards = []
    if assigned_personality:
        try:
            for card_id in assigned_personality.get('recommended_cards', []):
                card = db.get_card_by_slug(card_id)
                if card:
                    recommended_cards.append(card)
        except Exception as e:
            print(f"Error fetching recommended cards: {e}")
    
    context = {
        'personality': assigned_personality,
        'recommended_cards': recommended_cards,
    }
    
    return render(request, 'dashboard/personality_results.html', context)


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