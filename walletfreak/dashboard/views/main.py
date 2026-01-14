from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.services import db
from datetime import datetime, timedelta
from calendar import monthrange
import json
from cards.templatetags.card_extras import resolve_card_image_url

@login_required
def coming_soon(request):
    feature = request.GET.get('feature', 'Coming Soon')
    context = {
        'page_title': feature,
        'feature_name': feature
    }
    return render(request, 'dashboard/coming_soon.html', context)

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
    
    # Get all available cards for adding (Optimized: Basic info only)
    try:
        all_cards = db.get_cards()
    except Exception as e:
        print(f"Error fetching all cards: {e}")
        all_cards = []
    
    # Create lookup map for efficient access
    cards_map = {c['id']: c for c in all_cards}
    
    # Get IDs of cards already in user's wallet
    user_card_ids = set()
    for card in active_cards + inactive_cards + eyeing_cards:
        user_card_ids.add(card.get('card_id'))
    
    # Filter out cards already in wallet
    available_cards = [card for card in all_cards if card['id'] not in user_card_ids]
    
    # Prepare available cards JSON for JavaScript with full details
    available_cards_json = json.dumps([{
        'id': card.get('id', ''),
        'name': card.get('name', 'Unknown Card'),
        'issuer': card.get('issuer', 'Unknown Issuer'),
        'benefits': card.get('benefits', []),
        'rewards_structure': card.get('rewards_structure', []),
        'credits': card.get('credits', []),
        'welcome_bonus': card.get('welcome_bonus', ''),
        'welcome_offer': card.get('welcome_offer', ''),
        'signup_bonus': card.get('signup_bonus', ''),
        'welcome_requirement': card.get('welcome_requirement', ''),
        'annual_fee': card.get('annual_fee', 0),
        'image_url': resolve_card_image_url(card.get('id')) if card.get('id') else '',
        'earning_rates': card.get('earning_rates', []),
        'earning': card.get('earning', []),
    } for card in all_cards], default=str)
    
    # Calculate benefits and values
    all_benefits = []
    action_needed_benefits = []
    maxed_out_benefits = []
    ignored_benefits = []
    total_used_value = 0
    total_potential_value = 0
    total_annual_fee = 0
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for card in active_cards:
        try:
            # Get full card details - OPTIMIZED: Use cached map instead of DB call
            card_details = cards_map.get(card['card_id'])
            
            # Fallback if somehow not in map (e.g. card deleted but user has it)
            if not card_details:
                 continue

            # SYNC: Update active card with canonical details to fix stale images/names
            card['image_url'] = card_details.get('image_url')
            card['name'] = card_details.get('name')
            
            total_annual_fee += (card_details.get('annual_fee') or 0)
            
            # Get card anniversary date (when user added the card)
            anniversary_date_str = card.get('anniversary_date', '')
            
            # Special handling for "default"
            # If user selected "I don't know", it's stored as "default"
            # Interpret as Jan 1st of previous year
            if anniversary_date_str == 'default':
                 anniversary_month = 1
                 anniversary_year = current_year - 1
            elif anniversary_date_str:
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
                benefit_type = benefit.get('benefit_type')

                # Filter out Protection and Bonus benefits for display lists
                if benefit_type in ['Protection', 'Bonus']:
                    continue

                dollar_value = benefit.get('dollar_value')
                if dollar_value and dollar_value > 0:
                    benefit_id = benefit.get('id')
                    if not benefit_id: 
                         benefit_id = str(idx)
                    frequency = benefit.get('time_category', 'Annually (calendar year)')
                    
                    # Get usage from user's card data
                    benefit_usage_data = card.get('benefit_usage', {}).get(benefit_id, {})
                    
                    # Determine periods based on frequency
                    periods = []
                    current_period_status = 'empty' # empty, partial, full
                    current_period_used = 0
                    ytd_used = 0
                    
                    # Get period values mapping from benefit
                    period_values = benefit.get('period_values', {})
                    
                    if 'monthly' in frequency.lower():
                        # Generate 12 months
                        for m_idx, m_name in enumerate(months):
                            period_key = f"{current_year}_{m_idx+1:02d}"
                            period_max = period_values.get(period_key, dollar_value / 12)  # Fallback to division
                            if anniversary_year < current_year:
                                is_available = (m_idx + 1) <= current_month
                            else:
                                is_available = (m_idx + 1) >= anniversary_month and (m_idx + 1) <= current_month
                            
                            p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                            p_used = (p_data.get('used') or 0)
                            ytd_used += p_used
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
                                'is_available': is_available,
                                'used': p_used
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
                        h1_status = 'full' if (h1_data.get('is_full') or (h1_data.get('used') or 0) >= h1_max) else ('partial' if (h1_data.get('used') or 0) > 0 else 'empty')
                        if anniversary_year < current_year:
                            h1_available = current_month >= 1
                        else:
                            h1_available = anniversary_month <= 6 and current_month >= 1
                        periods.append({'label': 'H1', 'key': h1_key, 'status': h1_status, 'is_current': current_month <= 6, 'max_value': h1_max, 'is_available': h1_available, 'used': (h1_data.get('used') or 0)})
                        
                        # H2
                        h2_data = benefit_usage_data.get('periods', {}).get(h2_key, {})
                        h2_status = 'full' if (h2_data.get('is_full') or (h2_data.get('used') or 0) >= h2_max) else ('partial' if (h2_data.get('used') or 0) > 0 else 'empty')
                        if anniversary_year < current_year:
                            h2_available = current_month >= 7
                        else:
                            h2_available = (anniversary_month <= 6 and current_month >= 7) or (anniversary_month >= 7 and current_month >= anniversary_month)
                        periods.append({'label': 'H2', 'key': h2_key, 'status': h2_status, 'is_current': current_month > 6, 'max_value': h2_max, 'is_available': h2_available, 'used': (h2_data.get('used') or 0)})
                        
                        if current_month <= 6:
                            current_period_status = h1_status
                            current_period_used = (h1_data.get('used') or 0)
                        else:
                            current_period_status = h2_status
                            current_period_used = (h2_data.get('used') or 0)
                        
                        ytd_used = (h1_data.get('used') or 0) + (h2_data.get('used') or 0)

                    elif 'quarterly' in frequency.lower():
                        # Q1-Q4
                        curr_q = (current_month - 1) // 3 + 1
                        anniversary_q = (anniversary_month - 1) // 3 + 1
                        for q in range(1, 5):
                            q_key = f"{current_year}_Q{q}"
                            q_max = period_values.get(q_key, dollar_value / 4)
                            if anniversary_year < current_year:
                                q_available = q <= curr_q
                            else:
                                q_available = q >= anniversary_q and q <= curr_q
                            
                            has_periods_data = bool(benefit_usage_data.get('periods'))
                            q_data = benefit_usage_data.get('periods', {}).get(q_key, {})
                            
                            if has_periods_data:
                                p_used = (q_data.get('used') or 0)
                            else:
                                p_used = (q_data.get('used') or 0)

                            q_status = 'full' if (q_data.get('is_full') or p_used >= q_max) else ('partial' if p_used > 0 else 'empty')
                            periods.append({'label': f'Q{q}', 'key': q_key, 'status': q_status, 'is_current': q == curr_q, 'max_value': q_max, 'is_available': q_available, 'used': p_used})
                            
                            if q == curr_q:
                                current_period_status = q_status
                                current_period_used = p_used

                    elif 'every 4 years' in frequency.lower():
                        if anniversary_month:
                             this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             if datetime.now() < this_year_anniv:
                                 annual_start_year = current_year - 1
                             else:
                                 annual_start_year = current_year
                        else:
                             annual_start_year = current_year
                        
                        base_year = anniversary_year if anniversary_year else 2020
                        
                        block_idx = (annual_start_year - base_year) // 4
                        
                        block_start_year = base_year + (block_idx * 4)
                        block_end_year = block_start_year + 4
                        
                        period_key = f"{block_start_year}_{block_end_year}"
                        
                        if anniversary_month:
                             reset_date_obj = datetime(block_end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             reset_date_str = reset_date_obj.strftime('%b %d, %Y')
                        else:
                             reset_date_str = f"Dec 31, {block_end_year}" # Fallback
                             
                        has_periods_data = bool(benefit_usage_data.get('periods'))
                        p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                        
                        if has_periods_data:
                            p_used = (p_data.get('used') or 0)
                        else:
                            p_used = (p_data.get('used') or 0)

                        p_full = p_data.get('is_full', False)
                        
                        status = 'full' if (p_full or p_used >= dollar_value) else ('partial' if p_used > 0 else 'empty')
                        periods.append({
                            'label': f"{block_start_year}-{block_end_year}",
                            'key': period_key, 
                            'status': status, 
                            'is_current': True, 
                            'max_value': dollar_value, 
                            'used': p_used,
                            'reset_date': reset_date_str
                        })
                        
                        current_period_status = status
                        current_period_used = p_used
                        ytd_used = p_used

                    else:
                        # Annual / Permanent
                        reset_date_str = None
                        
                        if 'anniversary' in frequency.lower():
                            now_date = datetime.now()
                            this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            
                            if now_date < this_year_anniv:
                                start_year = current_year - 1
                                end_year = current_year
                            else:
                                start_year = current_year
                                end_year = current_year + 1
                                
                            period_key = f"{start_year}"
                            
                            reset_date_obj = datetime(end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            reset_date_str = reset_date_obj.strftime('%b %d, %Y')
                            
                        else:
                            period_key = f"{current_year}"
                            reset_date_str = f"Dec 31, {current_year}"
                        
                        has_periods_data = bool(benefit_usage_data.get('periods'))
                        p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                        
                        if has_periods_data:
                            p_used = (p_data.get('used') or 0)
                        else:
                            p_used = (p_data.get('used') or 0)
                            
                        p_full = p_data.get('is_full', False)
                        
                        status = 'full' if (p_full or p_used >= dollar_value) else ('partial' if p_used > 0 else 'empty')
                        periods.append({
                            'label': str(period_key.split('_')[0]) if '_' in period_key else str(current_year), # Label: '2025' or '2026'
                            'key': period_key, 
                            'status': status, 
                            'is_current': True, 
                            'max_value': dollar_value, 
                            'used': p_used,
                            'reset_date': reset_date_str
                        })
                        
                        current_period_status = status
                        current_period_used = p_used
                        ytd_used = p_used

                    # Calculate days until current period expires
                    days_until_expiration = None
                    now = datetime.now()
                    
                    if 'monthly' in frequency.lower():
                        last_day = monthrange(current_year, current_month)[1]
                        period_end = datetime(current_year, current_month, last_day, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'quarterly' in frequency.lower():
                        curr_q = (current_month - 1) // 3 + 1
                        quarter_end_month = curr_q * 3
                        last_day = monthrange(current_year, quarter_end_month)[1]
                        period_end = datetime(current_year, quarter_end_month, last_day, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'semi-annually' in frequency.lower():
                        if current_month <= 6:
                            period_end = datetime(current_year, 6, 30, 23, 59, 59)
                        else:
                            period_end = datetime(current_year, 12, 31, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'every 4 years' in frequency.lower():
                         if anniversary_month:
                             this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             if datetime.now() < this_year_anniv:
                                 annual_start_year = current_year - 1
                             else:
                                 annual_start_year = current_year
                         else:
                             annual_start_year = current_year
                        
                         base_year = anniversary_year if anniversary_year else 2020
                         block_idx = (annual_start_year - base_year) // 4
                         block_start_year = base_year + (block_idx * 4)
                         block_end_year = block_start_year + 4
                         
                         if anniversary_month:
                             reset_date_obj = datetime(block_end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             period_end = datetime(block_end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1, 23, 59, 59)
                         else:
                             period_end = datetime(block_end_year, 12, 31, 23, 59, 59)
                         
                         days_until_expiration = (period_end - now).days

                    else:
                        if 'anniversary' in frequency.lower() and anniversary_month:
                            this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            if now < this_year_anniv:
                                start_year = current_year - 1
                            else:
                                start_year = current_year
                            
                            exp_year = start_year + 1
                            
                            last_day = monthrange(exp_year, anniversary_month)[1]
                            anniversary_day = anniversary_date.day if anniversary_date_str else last_day
                            period_end = datetime(exp_year, anniversary_month, min(anniversary_day, last_day), 23, 59, 59)
                        else:
                            period_end = datetime(current_year, 12, 31, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    
                    
                    # Check if ignored status is stale (from a previous period)
                    is_ignored = benefit_usage_data.get('is_ignored', False)
                    if is_ignored:
                        last_updated = benefit_usage_data.get('last_updated')
                        
                        period_start_date = None
                        try:
                            if 'monthly' in frequency.lower():
                                period_start_date = datetime(current_year, current_month, 1)
                            elif 'quarterly' in frequency.lower():
                                curr_q = (current_month - 1) // 3 + 1
                                q_start_month = (curr_q - 1) * 3 + 1
                                period_start_date = datetime(current_year, q_start_month, 1)
                            elif 'semi-annually' in frequency.lower():
                                h_start_month = 1 if current_month <= 6 else 7
                                period_start_date = datetime(current_year, h_start_month, 1)
                            elif 'every 4 years' in frequency.lower():
                                if anniversary_month:
                                     this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                                     if datetime.now() < this_year_anniv:
                                         annual_start_year = current_year - 1
                                     else:
                                         annual_start_year = current_year
                                else:
                                     annual_start_year = current_year
                                
                                base_year = anniversary_year if anniversary_year else 2020
                                block_idx = (annual_start_year - base_year) // 4
                                block_start_year = base_year + (block_idx * 4)
                                
                                if anniversary_month:
                                    period_start_date = datetime(block_start_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                                else:
                                    period_start_date = datetime(block_start_year, 1, 1)

                            elif 'anniversary' in frequency.lower():
                                if anniversary_month:
                                    this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                                    if datetime.now() < this_year_anniv:
                                        p_start_year = current_year - 1
                                    else:
                                        p_start_year = current_year
                                    period_start_date = datetime(p_start_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                                else:
                                    period_start_date = datetime(current_year, 1, 1)
                            else:
                                period_start_date = datetime(current_year, 1, 1)
                                
                            if period_start_date:
                                if last_updated:
                                    if isinstance(last_updated, str):
                                        try:
                                             pass
                                        except:
                                            pass
                                    
                                    if hasattr(last_updated, 'tzinfo') and last_updated.tzinfo:
                                        last_updated_naive = last_updated.replace(tzinfo=None)
                                    else:
                                        last_updated_naive = last_updated
                                        
                                    if last_updated_naive < period_start_date:
                                        is_ignored = False 
                                else:
                                    is_ignored = False
                        except Exception as e:
                            print(f"Error checking ignore reset for benefit {idx}: {e}")
                    
                    
                    benefit_obj = {
                        'user_card_id': card['id'],  # Firestore document ID for user_cards subcollection
                        'card_id': card['card_id'],  # Card slug for filtering
                        'card_name': card_details['name'],
                        'benefit_id': benefit_id,
                        'benefit_name': benefit['description'],
                        'amount': dollar_value,
                        'used': current_period_used,
                        'periods': periods,
                        'frequency': frequency,
                        'current_period_status': current_period_status,
                        'script_id': f"{card['card_id']}_{benefit_id}",  # Unique ID for DOM elements
                        'days_until_expiration': days_until_expiration,
                        'is_ignored': is_ignored,
                        'ytd_used': ytd_used,
                        'additional_details': benefit.get('additional_details')
                    }
                    
                    all_benefits.append(benefit_obj)
                    
                    if is_ignored:
                        ignored_benefits.append(benefit_obj)
                    elif current_period_status == 'full':
                        maxed_out_benefits.append(benefit_obj)
                    else:
                        action_needed_benefits.append(benefit_obj)
                    
                    if not is_ignored:
                        benefit_potential = 0
                        for p in periods:
                            benefit_potential += p.get('max_value', 0)
                        
                        total_potential_value += benefit_potential

                    if (benefit_type == 'Credit' or benefit_type == 'Perk') and not is_ignored:
                        total_used_value += ytd_used
        except Exception as e:
            print(f"Error processing card benefits: {e}")
            continue
    
    card_524_map = {c['id']: c.get('is_524', True) for c in all_cards}
    
    cutoff_date = datetime.now() - timedelta(days=365*2)
    chase_524_count = 0
    
    for card in active_cards + inactive_cards:
        card_id = card.get('card_id')
        if not card_524_map.get(card_id, True):
            continue

        ann_date_str = card.get('anniversary_date')
        
        if ann_date_str == 'default':
            continue
            
        if ann_date_str:
            try:
                ann_date = datetime.strptime(ann_date_str, '%Y-%m-%d')
                if ann_date >= cutoff_date:
                    chase_524_count += 1
            except ValueError:
                pass
                
    chase_eligible = chase_524_count < 5
    


    visible_filter_card_ids = set()
    for benefit in action_needed_benefits + maxed_out_benefits + ignored_benefits:
        visible_filter_card_ids.add(benefit.get('card_id'))
        
    context = {

        'user': request.user,
        'active_cards': active_cards,
        'inactive_cards': inactive_cards,
        'eyeing_cards': eyeing_cards,
        'assigned_personality': assigned_personality,
        'all_cards_json': available_cards_json,
        
        'total_extracted_value': round(total_used_value, 2),
        'total_potential_value': round(total_potential_value, 2),
        'total_annual_fee': total_annual_fee,
        'net_performance': round(total_used_value - total_annual_fee, 2),
        'action_needed_benefits': action_needed_benefits,
        'maxed_out_benefits': maxed_out_benefits,
        'ignored_benefits': ignored_benefits,
        
        'visible_filter_card_ids': visible_filter_card_ids,
        
        'chase_524_count': chase_524_count,
        'chase_eligible': chase_eligible,
    }
    
    return render(request, 'dashboard/dashboard.html', context)
