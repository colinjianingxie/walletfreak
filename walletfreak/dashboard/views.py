from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.services import db
import datetime
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo

@login_required
def dashboard(request):
    uid = request.session.get('uid')
    user_profile = db.get_user_profile(uid)
    
    active_cards = db.get_user_cards(uid, status='active')
    inactive_cards = db.get_user_cards(uid, status='inactive')
    wishlist_cards = db.get_user_cards(uid, status='eyeing')
    
    # Calculate all benefits with their usage status
    all_benefits = []
    
    # Get current date in Eastern Time
    eastern = ZoneInfo('America/New_York')
    current_date = datetime.datetime.now(eastern).date()
    
    for card in active_cards:
        # We need to fetch the full card details to get the benefit definitions
        card_def = db.get_card_by_slug(card['card_id'])
        if not card_def or 'benefits' not in card_def:
            continue
            
        # Parse anniversary date if exists
        anniversary_date = None
        if card.get('anniversary_date'):
            try:
                anniversary_date = datetime.datetime.strptime(card['anniversary_date'], '%Y-%m-%d').date()
            except ValueError:
                pass

        for benefit in card_def['benefits']:
            if benefit.get('amount', 0) > 0:
                # Check usage
                usage = card.get('benefit_usage', {}).get(benefit['id'], {})
                used_amount = usage.get('used', 0)
                last_updated = usage.get('last_updated') # Timestamp
                
                # Determine reset period start/end
                reset_period = benefit.get('reset_period', 'annual').lower()
                
                period_start = None
                
                if reset_period == 'monthly':
                    period_start = current_date.replace(day=1)
                elif reset_period == 'quarterly':
                    # Q1: Jan-Mar, Q2: Apr-Jun, etc.
                    q_start_month = 3 * ((current_date.month - 1) // 3) + 1
                    period_start = current_date.replace(month=q_start_month, day=1)
                elif reset_period == 'semi-annual':
                    # H1: Jan-Jun, H2: Jul-Dec
                    h_start_month = 1 if current_date.month <= 6 else 7
                    period_start = current_date.replace(month=h_start_month, day=1)
                elif reset_period == 'annual':
                    # Calendar year
                    period_start = current_date.replace(month=1, day=1)
                elif reset_period == 'anniversary' and anniversary_date:
                    # Anniversary year logic
                    # Find the most recent anniversary date
                    this_year_anniversary = anniversary_date.replace(year=current_date.year)
                    if this_year_anniversary > current_date:
                        period_start = this_year_anniversary - relativedelta(years=1)
                    else:
                        period_start = this_year_anniversary
                
                # If last update was before period start, treat as 0 used
                if last_updated:
                    # Convert Firestore timestamp to date
                    last_updated_date = last_updated.date()
                    if period_start and last_updated_date < period_start:
                        used_amount = 0

                # Add ALL benefits (used and unused) to the list
                all_benefits.append({
                    'card_name': card['name'],
                    'benefit_name': benefit['name'],
                    'benefit_id': benefit['id'],
                    'card_id': card['id'],
                    'amount': benefit['amount'],
                    'used': used_amount,
                    'remaining': benefit['amount'] - used_amount,
                    'is_used': used_amount >= benefit['amount'],
                    'frequency': benefit.get('reset_period', 'annual').title(),
                    'reset_date': (period_start + relativedelta(years=1) if reset_period == 'anniversary' else None)
                })

    # Calculate totals
    total_potential_value = 0
    total_used_value = 0
    
    for card in active_cards:
        card_def = db.get_card_by_slug(card['card_id'])
        if not card_def or 'benefits' not in card_def:
            continue
            
        for benefit in card_def['benefits']:
            if benefit.get('amount', 0) > 0:
                total_potential_value += benefit['amount']
                
                # Get usage
                usage = card.get('benefit_usage', {}).get(benefit['id'], {})
                used = usage.get('used', 0)
                
                # Re-applying reset logic briefly:
                last_updated = usage.get('last_updated')
                reset_period = benefit.get('reset_period', 'annual').lower()
                anniversary_date = None
                if card.get('anniversary_date'):
                    try:
                        anniversary_date = datetime.datetime.strptime(card['anniversary_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                        
                period_start = None
                if reset_period == 'monthly':
                    period_start = current_date.replace(day=1)
                elif reset_period == 'quarterly':
                    q_start_month = 3 * ((current_date.month - 1) // 3) + 1
                    period_start = current_date.replace(month=q_start_month, day=1)
                elif reset_period == 'semi-annual':
                    h_start_month = 1 if current_date.month <= 6 else 7
                    period_start = current_date.replace(month=h_start_month, day=1)
                elif reset_period == 'annual':
                    period_start = current_date.replace(month=1, day=1)
                elif reset_period == 'anniversary' and anniversary_date:
                    this_year_anniversary = anniversary_date.replace(year=current_date.year)
                    if this_year_anniversary > current_date:
                        period_start = this_year_anniversary - relativedelta(years=1)
                    else:
                        period_start = this_year_anniversary
                
                if last_updated:
                    last_updated_date = last_updated.date()
                    if period_start and last_updated_date < period_start:
                        used = 0
                
                total_used_value += used

    context = {
        'user_profile': user_profile,
        'active_cards': active_cards,
        'inactive_cards': inactive_cards,
        'wishlist_cards': wishlist_cards,
        'all_benefits': all_benefits,
        'total_potential_value': total_potential_value,
        'total_used_value': total_used_value,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
def toggle_benefit_usage(request, user_card_id, benefit_id):
    if request.method == 'POST':
        uid = request.session.get('uid')
        
        # Fetch the card to get current usage
        user_cards = db.get_user_cards(uid)
        target_card = next((c for c in user_cards if c['id'] == user_card_id), None)
        
        if target_card:
            card_def = db.get_card_by_slug(target_card['card_id'])
            if card_def:
                target_benefit = next((b for b in card_def.get('benefits', []) if b['id'] == benefit_id), None)
                if target_benefit:
                    # Toggle logic: check current usage
                    current_usage = target_card.get('benefit_usage', {}).get(benefit_id, {})
                    current_used = current_usage.get('used', 0)
                    amount = target_benefit['amount']
                    
                    # If currently used (at max), set to 0. Otherwise, set to max.
                    new_amount = 0 if current_used >= amount else amount
                    db.update_benefit_usage(uid, user_card_id, benefit_id, new_amount)
                    
                    # Check if this is an AJAX request
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        from django.http import JsonResponse
                        
                        # Calculate new totals
                        active_cards = db.get_user_cards(uid, status='active')
                        total_potential_value = 0
                        total_used_value = 0
                        
                        from zoneinfo import ZoneInfo
                        eastern = ZoneInfo('America/New_York')
                        current_date = datetime.datetime.now(eastern).date()
                        
                        for card in active_cards:
                            card_def_temp = db.get_card_by_slug(card['card_id'])
                            if not card_def_temp or 'benefits' not in card_def_temp:
                                continue
                                
                            for benefit in card_def_temp['benefits']:
                                if benefit.get('amount', 0) > 0:
                                    total_potential_value += benefit['amount']
                                    
                                    usage = card.get('benefit_usage', {}).get(benefit['id'], {})
                                    used = usage.get('used', 0)
                                    
                                    # Apply reset logic
                                    last_updated = usage.get('last_updated')
                                    reset_period = benefit.get('reset_period', 'annual').lower()
                                    anniversary_date = None
                                    if card.get('anniversary_date'):
                                        try:
                                            anniversary_date = datetime.datetime.strptime(card['anniversary_date'], '%Y-%m-%d').date()
                                        except ValueError:
                                            pass
                                            
                                    period_start = None
                                    if reset_period == 'monthly':
                                        period_start = current_date.replace(day=1)
                                    elif reset_period == 'quarterly':
                                        q_start_month = 3 * ((current_date.month - 1) // 3) + 1
                                        period_start = current_date.replace(month=q_start_month, day=1)
                                    elif reset_period == 'semi-annual':
                                        h_start_month = 1 if current_date.month <= 6 else 7
                                        period_start = current_date.replace(month=h_start_month, day=1)
                                    elif reset_period == 'annual':
                                        period_start = current_date.replace(month=1, day=1)
                                    elif reset_period == 'anniversary' and anniversary_date:
                                        this_year_anniversary = anniversary_date.replace(year=current_date.year)
                                        if this_year_anniversary > current_date:
                                            period_start = this_year_anniversary - relativedelta(years=1)
                                        else:
                                            period_start = this_year_anniversary
                                    
                                    if last_updated:
                                        last_updated_date = last_updated.date()
                                        if period_start and last_updated_date < period_start:
                                            used = 0
                                    
                                    total_used_value += used
                        
                        return JsonResponse({
                            'success': True,
                            'is_used': new_amount >= amount,
                            'remaining': amount - new_amount,
                            'total_used_value': total_used_value,
                            'total_potential_value': total_potential_value,
                            'utilization_percentage': int((total_used_value / total_potential_value * 100) if total_potential_value > 0 else 0)
                        })
                    
    return redirect('dashboard')

@login_required
def add_card(request, card_id):
    uid = request.session.get('uid')
    status = request.POST.get('status', 'active')
    if request.method == 'POST':
        db.add_card_to_user(uid, card_id, status=status)
        return redirect('dashboard')
    return redirect('card_list')

@login_required
def update_card_status(request, user_card_id):
    if request.method == 'POST':
        uid = request.session.get('uid')
        new_status = request.POST.get('status')
        db.update_card_status(uid, user_card_id, new_status)
    return redirect('dashboard')

@login_required
def remove_card(request, user_card_id):
    if request.method == 'POST':
        uid = request.session.get('uid')
        db.remove_card_from_user(uid, user_card_id)
    return redirect('dashboard')

@login_required
def update_anniversary(request, user_card_id):
    if request.method == 'POST':
        uid = request.session.get('uid')
        date_str = request.POST.get('anniversary_date')
        if date_str:
            db.update_card_details(uid, user_card_id, {'anniversary_date': date_str})
    return redirect('dashboard')
