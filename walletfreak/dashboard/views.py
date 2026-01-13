from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from core.services import db
from datetime import datetime, timedelta
from calendar import monthrange
import json


from cards.templatetags.card_extras import resolve_card_image_url

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
                 # Try fetching directly or skip? Skip effectively handles deleted cards.
                 # Taking valid cards only is safer.
                 # print(f"Card {card['card_id']} not found in global cache.")
                 continue

            # SYNC: Update active card with canonical details to fix stale images/names
            card['image_url'] = card_details.get('image_url')
            card['name'] = card_details.get('name')
            
            total_annual_fee += card_details.get('annual_fee', 0)
            
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
                    # benefit_id = f"benefit_{idx}" # OLD
                    benefit_id = benefit.get('id')
                    if not benefit_id: 
                         # Fallback for legacy or malformed data, though id should be there from hydration
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
                            # Available if: anniversary year < current year (all months available) OR (same year AND month >= anniversary_month AND month <= current_month)
                            if anniversary_year < current_year:
                                is_available = (m_idx + 1) <= current_month
                            else:
                                is_available = (m_idx + 1) >= anniversary_month and (m_idx + 1) <= current_month
                            
                            p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                            p_used = p_data.get('used', 0)
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
                        h1_status = 'full' if (h1_data.get('is_full') or h1_data.get('used', 0) >= h1_max) else ('partial' if h1_data.get('used', 0) > 0 else 'empty')
                        # H1 available if: anniversary year < current year (always available) OR (same year AND anniversary is in H1 and we're past start of year)
                        if anniversary_year < current_year:
                            h1_available = current_month >= 1
                        else:
                            h1_available = anniversary_month <= 6 and current_month >= 1
                        periods.append({'label': 'H1', 'key': h1_key, 'status': h1_status, 'is_current': current_month <= 6, 'max_value': h1_max, 'is_available': h1_available, 'used': h1_data.get('used', 0)})
                        
                        # H2
                        h2_data = benefit_usage_data.get('periods', {}).get(h2_key, {})
                        h2_status = 'full' if (h2_data.get('is_full') or h2_data.get('used', 0) >= h2_max) else ('partial' if h2_data.get('used', 0) > 0 else 'empty')
                        # H2 available if: anniversary year < current year (available if we're in H2) OR (same year AND ((anniversary in H1 and current is H2) OR (anniversary in H2 and current >= anniversary month)))
                        if anniversary_year < current_year:
                            h2_available = current_month >= 7
                        else:
                            h2_available = (anniversary_month <= 6 and current_month >= 7) or (anniversary_month >= 7 and current_month >= anniversary_month)
                        periods.append({'label': 'H2', 'key': h2_key, 'status': h2_status, 'is_current': current_month > 6, 'max_value': h2_max, 'is_available': h2_available, 'used': h2_data.get('used', 0)})
                        
                        if current_month <= 6:
                            current_period_status = h1_status
                            current_period_used = h1_data.get('used', 0)
                        else:
                            current_period_status = h2_status
                            current_period_used = h2_data.get('used', 0)
                        
                        ytd_used = h1_data.get('used', 0) + h2_data.get('used', 0)

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
                            
                            # FALLBACK LOGIC FIX:
                            # Only use legacy 'used' if the ENTIRE 'periods' dictionary is missing/empty in benefit_usage.
                            # If 'periods' exists (even if this specific key is missing), it means we are on the new system => 0 usage.
                            has_periods_data = bool(benefit_usage_data.get('periods'))
                            q_data = benefit_usage_data.get('periods', {}).get(q_key, {})
                            
                            if has_periods_data:
                                p_used = q_data.get('used', 0)
                            else:
                                # Start fresh for new periods if no period data exists at all? 
                                # Actually, if NO period data exists, it might be an old benefit. 
                                # But if we are generating keys for 2026 and legacy was 2025, we shouldn't use legacy.
                                # Legacy 'used' was total-to-date.
                                # If we are in a new time period (year/month), we generally shouldn't use legacy unless we know it applies.
                                # Safer: Only use legacy if we can't determine period split? 
                                # For Quarterly/Monthly, we generally shouldn't rely on global 'used' for specific chunks unless we know.
                                # Let's assume 0 if no specific period data, UNLESS it's the very first time migration?
                                # No, for reset logic, 0 is correct for new periods.
                                p_used = q_data.get('used', 0)

                            q_status = 'full' if (q_data.get('is_full') or p_used >= q_max) else ('partial' if p_used > 0 else 'empty')
                            periods.append({'label': f'Q{q}', 'key': q_key, 'status': q_status, 'is_current': q == curr_q, 'max_value': q_max, 'is_available': q_available, 'used': p_used})
                            
                            if q == curr_q:
                                current_period_status = q_status
                                current_period_used = p_used

                    elif 'every 4 years' in frequency.lower():
                        # Every 4 Years (e.g. Global Entry)
                        # Anchor to Card Anniversary Year to create fixed 4-year blocks
                        # 1. Determine local "annual" start year (same as Anniversary logic)
                        if anniversary_month:
                             this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             if datetime.now() < this_year_anniv:
                                 annual_start_year = current_year - 1
                             else:
                                 annual_start_year = current_year
                        else:
                             # Calendar year fallback for start
                             annual_start_year = current_year
                        
                        # 2. Align to 4-year blocks from Card Open Year
                        # If anniversary_year (card open year) is available, use it. Else default to some Mod 4 basis (e.g. 2020)
                        base_year = anniversary_year if anniversary_year else 2020
                        
                        years_diff = annual_start_year - base_year
                        # Ensure positive diff or handle negative
                        # (annual_start - base) // 4 returns floor, works for negative too
                        block_idx = (annual_start_year - base_year) // 4
                        
                        block_start_year = base_year + (block_idx * 4)
                        block_end_year = block_start_year + 4
                        
                        period_key = f"{block_start_year}_{block_end_year}"
                        
                        # Reset Date
                        if anniversary_month:
                             reset_date_obj = datetime(block_end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                             reset_date_str = reset_date_obj.strftime('%b %d, %Y')
                        else:
                             reset_date_str = f"Dec 31, {block_end_year}" # Fallback
                             
                        # Period Data
                        has_periods_data = bool(benefit_usage_data.get('periods'))
                        p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                        
                        if has_periods_data:
                            p_used = p_data.get('used', 0)
                        else:
                            p_used = p_data.get('used', 0)

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
                        # Logic for Anniversary Date vs Calendar Year
                        reset_date_str = None
                        
                        if 'anniversary' in frequency.lower():
                            # Determine start year of the current anniversary period
                            # If today is BEFORE the anniversary date in current year, the period started last year.
                            # If today is AFTER (or ON) the anniversary date, the period started this year.
                            
                            # Need accurate comparison including DAY
                            now_date = datetime.now()
                            this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            
                            if now_date < this_year_anniv:
                                # We are in the period starting last year
                                start_year = current_year - 1
                                end_year = current_year
                            else:
                                # We are in the period starting this year
                                start_year = current_year
                                end_year = current_year + 1
                                
                            period_key = f"{start_year}"
                            
                            # Calculate reset date (Anniversary date of end_year)
                            reset_date_obj = datetime(end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            reset_date_str = reset_date_obj.strftime('%b %d, %Y')
                            
                        else:
                            # Calendar Year
                            period_key = f"{current_year}"
                            reset_date_str = f"Dec 31, {current_year}"
                        
                        
                        # FALLBACK LOGIC FIX:
                        has_periods_data = bool(benefit_usage_data.get('periods'))
                        p_data = benefit_usage_data.get('periods', {}).get(period_key, {})
                        
                        if has_periods_data:
                            p_used = p_data.get('used', 0)
                        else:
                            # Only fallback to legacy if NO period data exists at all AND we are likely in the first period?
                            # If it's a new year/period key, we definitely don't want legacy.
                            # Check if period_key matches current era? 
                            # If we have NO keys, maybe migration. 
                            # But if the benefit is "Annual", legacy `used` applies to "current annual".
                            # If `period_key` is new (e.g. 2026), legacy (from 2025) should NOT apply.
                            # So strictly: 0.
                            p_used = p_data.get('used', 0)
                            
                            # EXCEPTION: If the user NEVER had period keys (pure legacy) and this is their first view?
                            # We might lose data. 
                            # But legacy `used` was cumulative? Or annual? 
                            # Usually annual. 
                            # If we assume migration happened properly, we're good. 
                            # If not, we might hide old data. 
                            # However, for the BUG "reset didn't happen", force 0 for new keys is the fix.
                            pass

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
                        # Current month end
                        last_day = monthrange(current_year, current_month)[1]
                        period_end = datetime(current_year, current_month, last_day, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'quarterly' in frequency.lower():
                        # Current quarter end
                        curr_q = (current_month - 1) // 3 + 1
                        quarter_end_month = curr_q * 3
                        last_day = monthrange(current_year, quarter_end_month)[1]
                        period_end = datetime(current_year, quarter_end_month, last_day, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'semi-annually' in frequency.lower():
                        # Current half-year end (June 30 or Dec 31)
                        if current_month <= 6:
                            period_end = datetime(current_year, 6, 30, 23, 59, 59)
                        else:
                            period_end = datetime(current_year, 12, 31, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    elif 'every 4 years' in frequency.lower():
                        # Every 4 Years Expiration
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
                             # End of day before reset? Or Reset Date is expiration? 
                             # Expiration is usually end of previous period.
                             # If reset is Jan 1 2026, period ends Dec 31 2025? 
                             # Or strict exact time? 
                             # Using standard period_end logic: End of 'block_end_year' ? No.
                             # It resets ON `reset_date_obj`. So expiration is that date or day before?
                             # In Annual logic: `period_end` is the Anniversary Day.
                             period_end = datetime(block_end_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1, 23, 59, 59)
                         else:
                             period_end = datetime(block_end_year, 12, 31, 23, 59, 59)
                         
                         days_until_expiration = (period_end - now).days

                    else:
                        # Annual - end of year or anniversary date
                        if 'anniversary' in frequency.lower() and anniversary_month:
                            # Logic must match the period loop logic to ensure consistency
                            # 1. Determine START YEAR of current period
                            this_year_anniv = datetime(current_year, anniversary_month, anniversary_date.day if anniversary_date_str else 1)
                            if now < this_year_anniv:
                                start_year = current_year - 1
                            else:
                                start_year = current_year
                            
                            # 2. Expiration is Anniversary Date of NEXT year (Start Year + 1)
                            exp_year = start_year + 1
                            
                            last_day = monthrange(exp_year, anniversary_month)[1]
                            anniversary_day = anniversary_date.day if anniversary_date_str else last_day
                            period_end = datetime(exp_year, anniversary_month, min(anniversary_day, last_day), 23, 59, 59)
                        else:
                            # Calendar year - Dec 31
                            period_end = datetime(current_year, 12, 31, 23, 59, 59)
                        days_until_expiration = (period_end - now).days
                    
                    
                    # --- IGNORE RESET LOGIC ---
                    # Check if ignored status is stale (from a previous period)
                    is_ignored = benefit_usage_data.get('is_ignored', False)
                    if is_ignored:
                        last_updated = benefit_usage_data.get('last_updated')
                        
                        # Calculate Period Start Date for comparison
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
                                # Every 4 Years Reset Logic
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
                                # Use the start year calculated in the Annual/Anniversary block logic
                                # We need to reuse that logic or re-calculate.
                                # Re-calculating for safety as variables might not be in scope if not Annual loop (though variable scoping in python loop is usually fine, 'start_year' is inside 'else' block)
                                
                                # Simplified Anniversary Start Calculation:
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
                                # Annual (Calendar)
                                period_start_date = datetime(current_year, 1, 1)
                                
                            # Compare
                            if period_start_date:
                                # Ensure last_updated is naive / comparable
                                if last_updated:
                                    # Handle string timestamp if that occurs?
                                    if isinstance(last_updated, str):
                                        # Parse? Assume datetime for now as Firestore returns datetime
                                        try:
                                             # Attempt naive parse if ISO format
                                             # But usually it's a DatetimeWithNanoseconds
                                             pass
                                        except:
                                            pass
                                    
                                    # If timezone aware, convert to naive or convert period_start to aware
                                    if hasattr(last_updated, 'tzinfo') and last_updated.tzinfo:
                                        # Convert to naive local (simple strip)
                                        last_updated_naive = last_updated.replace(tzinfo=None)
                                    else:
                                        last_updated_naive = last_updated
                                        
                                    if last_updated_naive < period_start_date:
                                        is_ignored = False # RESET
                                else:
                                    # No timestamp -> likely legacy ignore or error
                                    # Reset to be safe, so user can re-ignore if they want
                                    is_ignored = False
                        except Exception as e:
                            print(f"Error checking ignore reset for benefit {idx}: {e}")
                            # Fallback: keep is_ignored as is
                    
                    
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
                    
                    # YTD Total Rewards sums ALL valid benefits (potential) - EXCLUDING ignored
                    if not is_ignored:
                        # Calculate available potential value based on periods
                        benefit_potential = 0
                        for p in periods:
                            # Sum all periods to get Full Year Potential (User Request: "all possible credits for the whole year")
                            benefit_potential += p.get('max_value', 0)
                        
                        total_potential_value += benefit_potential

                    # Credits Used and Net Performance are based strictly on "Credit" type benefits
                    # Also exclude output from these metrics if ignored? 
                    # The requirement says "Remove the value of that benefit from YTD Total rewards."
                    # It also says "user cannot log any of the values".
                    # Let's assume ignored benefits do not contribute to Credits Used either if they were partially used before ignoring?
                    # The prompt says: "When the benefit is ignored, Remove the value of that benefit from YTD Total rewards."
                    # It implies it shouldn't count.
                    # Credits Used includes all benefits with monetary value (Credits, Perks, Bonus etc)
                    if (benefit_type == 'Credit' or benefit_type == 'Perk') and not is_ignored:
                        total_used_value += ytd_used
        except Exception as e:
            print(f"Error processing card benefits: {e}")
            continue
    
    # Calculate Chase 5/24 Status
    # Rule: Ineligible if 5 or more personal cards opened in last 24 months
    # Only count cards that are marked as Is524
    
    # Create lookup map for card 5/24 status
    # default to True if not found to be safe, but per user request we trust the flag
    # defaulting to True is safer for 5/24 estimation if data is missing, 
    # but user said "If the card is not Is524, feel free to ignore it".
    # Since I'm seeding it, it should be there.
    card_524_map = {c['id']: c.get('is_524', True) for c in all_cards}
    
    cutoff_date = datetime.now() - timedelta(days=365*2)
    chase_524_count = 0
    
    # Check both active and inactive cards (history matters)
    for card in active_cards + inactive_cards:
        # Check if card counts towards 5/24
        card_id = card.get('card_id')
        if not card_524_map.get(card_id, True):
            continue

        ann_date_str = card.get('anniversary_date')
        
        # Rule: "Ignore the 'default' keyword when doing 5/24 calculations"
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
    
    # Fetch user profile data to ensure photo_url is available
    try:
        user_data = db.get_user_profile(uid) or {}
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        user_data = {}

    # Calculate visible filter card IDs (cards that have at least one benefit shown)
    visible_filter_card_ids = set()
    for benefit in action_needed_benefits + maxed_out_benefits + ignored_benefits:
        visible_filter_card_ids.add(benefit.get('card_id'))
        
    context = {
        'user_profile': {
            'photo_url': user_data.get('photo_url') or request.session.get('user_photo'),
            'email': user_data.get('email') or request.session.get('user_email')
        },
        'user': request.user, # Standard Django user
        'active_cards': active_cards,
        'inactive_cards': inactive_cards,
        'eyeing_cards': eyeing_cards,
        'assigned_personality': assigned_personality,
        'all_cards_json': available_cards_json,
        
        # Benefits
        'total_extracted_value': round(total_used_value, 2),
        'total_potential_value': round(total_potential_value, 2),
        'total_annual_fee': total_annual_fee,
        'net_performance': round(total_used_value - total_annual_fee, 2),
        'action_needed_benefits': action_needed_benefits,
        'maxed_out_benefits': maxed_out_benefits,
        'ignored_benefits': ignored_benefits,
        
        # UI Helpers
        'visible_filter_card_ids': visible_filter_card_ids,
        
        # 5/24 Status
        'chase_524_count': chase_524_count,
        'chase_eligible': chase_eligible,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


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
        deleted_card_slug = db.remove_card_from_user(uid, user_card_id)
        
        # If AJAX, return the generic card details so frontend can add it back to 'available' list
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
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
            
            return JsonResponse({'success': True}) # Fallback if card not found or slug missing
            
        return redirect('dashboard')  # Redirect to dashboard after removing card
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.POST.get('ajax'):
             return JsonResponse({'success': False, 'error': str(e)}, status=500)
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
        increment = request.POST.get('increment') == 'true'
        
        db.update_benefit_usage(uid, user_card_id, benefit_id, usage_amount, period_key=period_key, is_full=is_full, increment=increment)
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


@login_required
@require_POST
def toggle_benefit_ignore_status(request, user_card_id, benefit_id):
    """Toggle ignore status for a benefit"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    try:
        is_ignored = request.POST.get('is_ignored') == 'true'
        
        # We allow users to ignore benefits even if they have usage history.
        # The 'Ignore' feature is for hiding it from the main views for the current period.
        
        db.toggle_benefit_ignore(uid, user_card_id, benefit_id, is_ignored)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def points_collection(request):
    """Points Collection feature (Premium Only)"""
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
        
    # Check premium status
    if not db.is_premium(uid):
        return redirect('pricing')
        
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/points_collection.html', context)