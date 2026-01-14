from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse
from core.services import db
import json
from cards.templatetags.card_extras import resolve_card_image_url

@login_required
@require_POST
def add_card(request, card_id):
    """Add a card to user's wallet"""
    uid = request.session.get('uid')
    if not uid:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        return redirect('login')
    
    try:
        status = request.POST.get('status', 'active')
        anniversary_date = request.POST.get('anniversary_date', None)
        
        success = db.add_card_to_user(uid, card_id, status=status, anniversary_date=anniversary_date)
        
        if success:
            # Get updated personality
            personality = db.get_user_assigned_personality(uid)
            personality_data = None
            if personality:
                personality_data = {
                    'id': personality.get('id'),
                    'name': personality.get('name'),
                    'match_score': personality.get('match_score', 0)
                }

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
                return JsonResponse({'success': True, 'personality': personality_data})
            return redirect('dashboard')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
                return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)
            return JsonResponse({'success': False, 'error': 'Card not found'}, status=404)
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
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
        # Check if we should also remove loyalty program
        delete_loyalty = False
        try:
            body = json.loads(request.body)
            delete_loyalty = body.get('delete_loyalty_program', False)
        except:
            pass
            
        card_doc = db.db.collection('users').document(uid).collection('user_cards').document(user_card_id).get()
        deleted_card_slug = db.remove_card_from_user(uid, user_card_id)
        
        # If successfully deleted and flag is set, remove loyalty program
        if deleted_card_slug and delete_loyalty:
             master_card = db.get_card_by_slug(deleted_card_slug)
             if master_card:
                 pid = master_card.get('loyalty_program')
                 if pid:
                     db.remove_user_loyalty_program(uid, pid)
        
        # If AJAX, return the generic card details so frontend can add it back to 'available' list
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax') or request.content_type == 'application/json':
            # Get updated personality
            personality = db.get_user_assigned_personality(uid)
            personality_data = None
            if personality:
                personality_data = {
                    'id': personality.get('id'),
                    'name': personality.get('name'),
                    'match_score': personality.get('match_score', 0)
                }
            
            response_data = {'success': True, 'personality': personality_data}

            if deleted_card_slug:
                generic_card = db.get_card_by_slug(deleted_card_slug)
                if generic_card:
                    # Construct standardized card object for JS
                    card_data = {
                        'id': generic_card.get('id', deleted_card_slug),
                        'name': generic_card.get('name'),
                        'issuer': generic_card.get('issuer'),
                        'benefits': generic_card.get('benefits', []),
                        'rewards_structure': generic_card.get('rewards_structure', []),
                        'credits': generic_card.get('credits', []),
                        'welcome_bonus': generic_card.get('welcome_bonus', ''),
                        'welcome_offer': generic_card.get('welcome_offer', ''),
                        'signup_bonus': generic_card.get('signup_bonus', ''),
                        'welcome_requirement': generic_card.get('welcome_requirement', ''),
                        'annual_fee': generic_card.get('annual_fee', 0),
                        'image_url': resolve_card_image_url(deleted_card_slug),
                        'earning_rates': generic_card.get('earning_rates', []),
                        'earning': generic_card.get('earning', []),
                    }
                    response_data['card'] = card_data
            
            return JsonResponse(response_data)
            
        return redirect('dashboard')  # Redirect to dashboard after removing card
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def check_card_delete_consequences(request, user_card_id):
    """Check if deleting a card will orphan a loyalty program"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    try:
        # 1. Get ALL active cards for user (hydrated)
        all_cards = db.get_user_cards(uid, status='active', hydrate=True)
        
        # 2. Find the target card
        target_card = next((c for c in all_cards if c['user_card_id'] == user_card_id), None)
        
        if not target_card:
             all_cards_all = db.get_user_cards(uid, hydrate=True)
             target_card = next((c for c in all_cards_all if c['user_card_id'] == user_card_id), None)
             
        if not target_card:
            return JsonResponse({'success': False, 'error': 'Card not found'})

        loyalty_pid = target_card.get('loyalty_program')
        
        if not loyalty_pid:
            # No loyalty program linked
            return JsonResponse({
                'will_be_removed': False,
                'message': 'No loyalty program linked.'
            })
            
        # 3. Check for other cards sharing this program
        user_card_id_clean = user_card_id.strip()
        other_cards_count = sum(1 for c in all_cards if c.get('loyalty_program') == loyalty_pid and str(c.get('user_card_id')).strip() != user_card_id_clean)
        
        will_be_removed = (other_cards_count == 0)
        
        program_name = loyalty_pid
        prog_info = db.get_document('program_loyalty', loyalty_pid)
        if prog_info:
            program_name = prog_info.get('program_name', loyalty_pid)
            
        return JsonResponse({
            'will_be_removed': will_be_removed,
            'program_name': program_name,
            'program_id': loyalty_pid,
            'other_cards_count': other_cards_count
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_POST
def update_anniversary(request, user_card_id):
    """Update anniversary date for a card"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        anniversary_date = request.POST.get('anniversary_date')
        
        # LOGIC CHANGE: Update in-place to preserve ID, but reset benefits
        update_data = {
            'anniversary_date': anniversary_date,
            'benefit_usage': {} # Reset benefits
        }
        
        # Use the existing update_card_details method
        db.update_card_details(uid, user_card_id, update_data)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
