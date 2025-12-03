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
    
    # Get IDs of cards already in user's wallet
    user_card_ids = set()
    for card in active_cards + inactive_cards + eyeing_cards:
        user_card_ids.add(card.get('card_id'))
    
    # Filter out cards already in wallet
    available_cards = [card for card in all_cards if card['id'] not in user_card_ids]
    
    # Prepare available cards JSON for JavaScript with full details
    available_cards_json = json.dumps([{
        'id': card['id'],
        'name': card['name'],
        'issuer': card['issuer'],
        'benefits': card.get('benefits', []),
        'rewards_structure': card.get('rewards_structure', []),
        'credits': card.get('credits', []),
        'welcome_bonus': card.get('welcome_bonus', ''),
        'welcome_offer': card.get('welcome_offer', ''),
        'signup_bonus': card.get('signup_bonus', ''),
        'welcome_requirement': card.get('welcome_requirement', ''),
        'annual_fee': card.get('annual_fee', 0)
    } for card in available_cards], default=str)
    
    # Calculate benefits and values
    all_benefits = []
    action_needed_benefits = []
    maxed_out_benefits = []
    total_used_value = 0
    total_potential_value = 0
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for card in active_cards:
        try:
            # Get full card details
            card_details = db.get_card_by_slug(card['card_id'])
            if not card_details:
                continue
            
            # Get card anniversary date (when user added the card)
            anniversary_date_str = card.get('anniversary_date', '')
            if anniversary_date_str:
                try:
                    anniversary_date = datetime.strptime(anniversary_date_str, '%Y-%m-%d')
                    anniversary_month = anniversary_date.month
                    anniversary_year = anniversary_date.year
                except:
                    # Default to January if parsing fails
                    anniversary_month = 1
                    anniversary_year = current_year
            else:
                # Default to January for cards without anniversary date
                anniversary_month = 1
                anniversary_year = current_year
            
            # Process each benefit
            for idx, benefit in enumerate(card_details.get('benefits', [])):
                dollar_value = benefit.get('dollar_value')
                if dollar_value and dollar_value > 0:
                    benefit_id = f"benefit_{idx}"
                    frequency = benefit.get('time_category', 'Annually (calendar year)')
                    
                    # Get usage from user's card data
                    benefit_usage_data = card.get('benefit_usage', {}).get(benefit_id, {})
                    
                    # Determine periods based on frequency
                    periods = []
                    current_period_status = 'empty' # empty, partial, full
                    current_period_used = 0
                    
                    # Get period values mapping from benefit
                    period_values = benefit.get('period_values', {})
                    
                    if 'monthly' in frequency.lower():
                        # Generate 12 months
                        for m_idx, m_name in enumerate(months):
                            period_key = f"{current_year}_{m_idx+1:02d}"
                            period_max = period_values.get(period_key, dollar_value / 12)  # Fallback to division
                            # Available if: anniversary year < current year (all months available) OR (same year AND month >= anniversary_month AND month <= current_month)
                            if anniversary_year < current_year:
                                is_available = (m_idx + 1) <= current_month
                            else:
                                is_available = (m_idx + 1) >= anniversary_month and (m_idx + 1) <= current_month
                            
                            p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                            p_used = p_data.get('used', 0)
                            p_full = p_data.get('is_full', False)
                            
                            status = 'empty'
                            if p_full or p_used >= period_max:
                                status = 'full'
                            elif p_used > 0:
                                status = 'partial'
                                
                            periods.append({
                                'label': m_name,
                                'key': period_key,
                                'status': status,
                                'is_current': (m_idx + 1) == current_month,
                                'max_value': period_max,
                                'is_available': is_available
                            })
                            
                            if (m_idx + 1) == current_month:
                                current_period_status = status
                                current_period_used = p_used

                    elif 'semi-annually' in frequency.lower():
                        # H1 (Jan-Jun), H2 (Jul-Dec)
                        h1_key = f"{current_year}_H1"
                        h2_key = f"{current_year}_H2"
                        h1_max = period_values.get(h1_key, dollar_value / 2)
                        h2_max = period_values.get(h2_key, dollar_value / 2)
                        
                        # H1
                        h1_data = benefit_usage_data.get('periods', {}).get(h1_key, {})
                        h1_status = 'full' if (h1_data.get('is_full') or h1_data.get('used', 0) >= h1_max) else ('partial' if h1_data.get('used', 0) > 0 else 'empty')
                        # H1 available if: anniversary year < current year (always available) OR (same year AND anniversary is in H1 and we're past start of year)
                        if anniversary_year < current_year:
                            h1_available = current_month >= 1
                        else:
                            h1_available = anniversary_month <= 6 and current_month >= 1
                        periods.append({'label': 'H1', 'key': h1_key, 'status': h1_status, 'is_current': current_month <= 6, 'max_value': h1_max, 'is_available': h1_available})
                        
                        # H2
                        h2_data = benefit_usage_data.get('periods', {}).get(h2_key, {})
                        h2_status = 'full' if (h2_data.get('is_full') or h2_data.get('used', 0) >= h2_max) else ('partial' if h2_data.get('used', 0) > 0 else 'empty')
                        # H2 available if: anniversary year < current year (available if we're in H2) OR (same year AND ((anniversary in H1 and current is H2) OR (anniversary in H2 and current >= anniversary month)))
                        if anniversary_year < current_year:
                            h2_available = current_month >= 7
                        else:
                            h2_available = (anniversary_month <= 6 and current_month >= 7) or (anniversary_month >= 7 and current_month >= anniversary_month)
                        periods.append({'label': 'H2', 'key': h2_key, 'status': h2_status, 'is_current': current_month > 6, 'max_value': h2_max, 'is_available': h2_available})
                        
                        if current_month <= 6:
                            current_period_status = h1_status
                            current_period_used = h1_data.get('used', 0)
                        else:
                            current_period_status = h2_status
                            current_period_used = h2_data.get('used', 0)

                    elif 'quarterly' in frequency.lower():
                        # Q1-Q4
                        curr_q = (current_month - 1) // 3 + 1
                        anniversary_q = (anniversary_month - 1) // 3 + 1
                        for q in range(1, 5):
                            q_key = f"{current_year}_Q{q}"
                            q_max = period_values.get(q_key, dollar_value / 4)
                            # Available if: anniversary year < current year (all quarters up to current available) OR (same year AND quarter >= anniversary_quarter AND quarter <= current_quarter)
                            if anniversary_year < current_year:
                                q_available = q <= curr_q
                            else:
                                q_available = q >= anniversary_q and q <= curr_q
                            q_data = benefit_usage_data.get('periods', {}).get(q_key, {})
                            q_status = 'full' if (q_data.get('is_full') or q_data.get('used', 0) >= q_max) else ('partial' if q_data.get('used', 0) > 0 else 'empty')
                            periods.append({'label': f'Q{q}', 'key': q_key, 'status': q_status, 'is_current': q == curr_q, 'max_value': q_max, 'is_available': q_available})
                            
                            if q == curr_q:
                                current_period_status = q_status
                                current_period_used = q_data.get('used', 0)

                    else:
                        # Annual / Permanent
                        period_key = f"{current_year}"
                        p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                        # Fallback to legacy 'used' if period data missing
                        legacy_used = benefit_usage_data.get('used', 0)
                        p_used = p_data.get('used', legacy_used)
                        p_full = p_data.get('is_full', False)
                        
                        status = 'full' if (p_full or p_used >= dollar_value) else ('partial' if p_used > 0 else 'empty')
                        periods.append({'label': str(current_year), 'key': period_key, 'status': status, 'is_current': True, 'max_value': dollar_value})
                        
                        current_period_status = status
                        current_period_used = p_used

                    benefit_obj = {
                        'user_card_id': card['id'],  # Firestore document ID for user_cards subcollection
                        'card_id': card['card_id'],  # Card slug for filtering
                        'card_name': card_details['name'],
                        'benefit_id': benefit_id,
                        'benefit_name': benefit['description'][:50] + '...' if len(benefit['description']) > 50 else benefit['description'],
                        'amount': dollar_value,
                        'used': current_period_used,
                        'periods': periods,
                        'frequency': frequency,
                        'current_period_status': current_period_status,
                        'script_id': f"{card['card_id']}_{benefit_id}"  # Unique ID for DOM elements
                    }
                    
                    all_benefits.append(benefit_obj)
                    
                    # Check if ALL available periods are full (not just current period)
                    available_periods = [p for p in periods if p.get('is_available', True)]
                    all_available_full = all(p['status'] == 'full' for p in available_periods) if available_periods else False
                    
                    if all_available_full and len(available_periods) > 0:
                        maxed_out_benefits.append(benefit_obj)
                    else:
                        action_needed_benefits.append(benefit_obj)
                    
                    total_used_value += current_period_used
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
        'action_needed_benefits': action_needed_benefits,
        'maxed_out_benefits': maxed_out_benefits,
        'total_used_value': total_used_value,
        'total_potential_value': total_potential_value,
        'current_month_idx': current_month - 1,
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
    
    # Get all available cards for the modal
    all_cards_dict = {}
    try:
        all_cards = db.get_cards()
        for card in all_cards:
            # Ensure essential fields exist
            if 'annual_fee' not in card:
                card['annual_fee'] = 0
            if 'benefits' not in card:
                card['benefits'] = []
            
            # Normalize earning rates if needed (depending on DB structure)
            # Assuming DB has 'earning_rates' or 'rewards_structure'
            
            all_cards_dict[card['id']] = card
    except Exception as e:
        print(f"Error fetching all cards: {e}")

    cards_json = json.dumps(all_cards_dict, default=str)
    
    context = {
        'user_cards': enriched_cards,
        'cards_json': cards_json,
    }
    
    return render(request, 'dashboard/wallet.html', context)


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
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
                return JsonResponse({'success': True})
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
        db.remove_card_from_user(uid, user_card_id)
        return redirect('wallet')  # Stay on wallet page for better UX
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
        period_key = request.POST.get('period_key')
        is_full = request.POST.get('is_full') == 'true'
        
        db.update_benefit_usage(uid, user_card_id, benefit_id, usage_amount, period_key=period_key, is_full=is_full)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



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