from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.services import db
import datetime
from dateutil.relativedelta import relativedelta

@login_required
def dashboard(request):
    uid = request.session.get('uid')
    user_profile = db.get_user_profile(uid)
    
    active_cards = db.get_user_cards(uid, status='active')
    inactive_cards = db.get_user_cards(uid, status='inactive')
    wishlist_cards = db.get_user_cards(uid, status='eyeing')
    
    # Calculate unused subscriptions
    unused_subscriptions = []
    current_date = datetime.date.today()
    
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
                is_reset = False
                
                # Logic to determine if usage should be reset (visual only, we don't reset DB here)
                # In a real app, we'd store 'period_start' in usage to compare.
                # Here we'll just check if last_updated is within the current period.
                
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

                if used_amount < benefit['amount']:
                    unused_subscriptions.append({
                        'card_name': card['name'],
                        'benefit_name': benefit['name'],
                        'amount': benefit['amount'],
                        'remaining': benefit['amount'] - used_amount,
                        'frequency': benefit.get('reset_period', 'annual').title(),
                        'reset_date': (period_start + relativedelta(years=1) if reset_period == 'anniversary' else None)
                    })

    context = {
        'user_profile': user_profile,
        'active_cards': active_cards,
        'inactive_cards': inactive_cards,
        'wishlist_cards': wishlist_cards,
        'unused_subscriptions': unused_subscriptions
    }
    return render(request, 'dashboard/dashboard.html', context)

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
