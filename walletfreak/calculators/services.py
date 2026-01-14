import csv
import os
import math
import json
from datetime import datetime, date
from django.conf import settings
from core.services import db

class OptimizerService:
    def __init__(self):
        self.cards_map = {c['id']: c for c in db.get_cards()}
        # self.bonuses and self.default_rates no longer loaded from CSV here on init 
        # because we will derive them from cards_map on the fly or pre-process them
        
    def _load_default_rates(self):
        """
        Derives default rates from enriched card data.
        Returns dict: {slug: {'rate': float, 'currency': str}}
        """
        rates = {}
        for slug, card in self.cards_map.items():
            found_default = False
            for r in card.get('earning_rates', []):
                if r.get('is_default'):
                    rates[slug] = {
                        'rate': float(r.get('multiplier') or r.get('rate') or 0.0),
                        'currency': r.get('currency', 'points')
                    }
                    found_default = True
                    break
            
            if not found_default:
                # Fallback: Try to find 'All Purchases' or base rate?
                # For now stick to strict is_default or 0
                pass
                
        return rates

    def calculate_recommendations(self, planned_spend, duration_months, user_wallet_slugs=None, mode='single', uid=None, sort_by='recommended'):
        """
        Core optimization logic.
        """
        if user_wallet_slugs is None:
            user_wallet_slugs = set()
            
        # Match Score Pre-Calculation
        match_scores = {}
        if uid:
            # We need all_cards for the match score calculation
            # db.get_cards() returns list of dicts. self.cards_map is id->dict.
            # We can reconstruct the list or just call db.get_cards() again? 
            # self.cards_map values are the cards.
            all_cards_list = list(self.cards_map.values())
            
            user_personality = db.get_user_assigned_personality(uid)
            # Need full card objects for user wallet
            user_cards_full = db.get_user_cards(uid)
            
            match_scores = db.calculate_match_scores(user_personality, user_cards_full, all_cards_list)
            
        # Fixed date for simulation/optimization as per requirements
        today = date(2025, 12, 24)
        monthly_spend_capacity = planned_spend / duration_months if duration_months > 0 else 0
        
        candidates = []
        
        default_rates = self._load_default_rates()
        
        for slug, card_obj in self.cards_map.items():
            # 1. Filter: In Wallet
            if slug in user_wallet_slugs:
                continue
                
            # 3. Parse Bonus Data from Enriched Card Object
            bonus_data = card_obj.get('sign_up_bonus') or {}
            if not bonus_data:
                continue
                
            try:
                # Map keys from parse_updates.py / Firestore
                req_spend = float(bonus_data.get('spend_amount', 0))
                req_months = int(bonus_data.get('duration_months', 0))
                bonus_qty = float(bonus_data.get('value', 0))
                bonus_type = bonus_data.get('currency', 'Points') # 'currency' holds the type (Points/Cash)
                # eff_date_str = bonus_data.get('effective_date', '') # Not used in logic below currently
            except (ValueError, TypeError):
                continue
                
            # 5. Filter: Infeasible
            if req_spend > planned_spend:
                continue

            # 6. Additional Filter: Monthly Spend Constraint
            if req_months > 0:
                monthly_req = req_spend / req_months
                if monthly_req > monthly_spend_capacity + 1.0:
                    continue
            
            # 7. Valuation
            raw_cpp = card_obj.get('points_value_cpp') or 1.0
            try:
                cpp = float(raw_cpp) if isinstance(raw_cpp, (int, float)) else 1.0
            except:
                cpp = 1.0
            
            # Bonus Value ($)
            if str(bonus_type).lower() == 'cash':
                bonus_value = bonus_qty
            else:
                bonus_value = bonus_qty * (cpp / 100.0)
                
            # Ongoing Rate Value ($ per $1 spend)
            default_rate_info = default_rates.get(slug, {'rate': 0, 'currency': 'points'})
            def_rate_val = default_rate_info['rate']
            def_currency = default_rate_info['currency']
            
            # Convert ongoing rate to dollar value per dollar spent
            if 'cash' in str(def_currency).lower() or 'cash' in str(bonus_type).lower():
                 ongoing_rate_dollar = def_rate_val / 100.0
            else:
                 ongoing_rate_dollar = def_rate_val * (cpp / 100.0)

            # Metrics Calculation
            total_earn_from_spend = planned_spend * ongoing_rate_dollar
            
            total_value = bonus_value + total_earn_from_spend
            
            # annual_fee is inside card_obj.get('annual_fee') 
            # In parse_updates it's stored as int on root.
            annual_fee = float(card_obj.get('annual_fee') or 0)
            net_value = total_value - annual_fee
            
            # ROI
            if planned_spend > 0:
                roi = (net_value / planned_spend) * 100
            else:
                roi = 0
                
            denom = req_spend if req_spend > 0 else 500.0
            marginal_density = (bonus_value - annual_fee) / denom + ongoing_rate_dollar
            
            # Match Score
            # Use card ID for lookup since calculate_match_scores returns by ID
            c_id = card_obj.get('id')
            match_score = match_scores.get(c_id, 0.0)
            
            # Rank Score Formula: Net Value + (Match Score * 2.0)
            rank_score = net_value + (match_score * 2.0)

            candidates.append({
                'slug': slug,
                'card': card_obj,
                'bonus_value': bonus_value,
                'net_value': net_value,
                'roi': roi,
                'marginal_density': marginal_density,
                'ongoing_rate': ongoing_rate_dollar,
                'req_spend': req_spend,
                'req_months': req_months,
                'annual_fee': annual_fee,
                'bonus_text': f"{int(bonus_qty):,} {bonus_type}" if bonus_qty > 0 else "No Bonus",
                'match_score': match_score,
                'rank_score': rank_score
            })
            
        # Optimization Algorithm
        if mode == 'combo':
            return self._optimize_combo(candidates, planned_spend, monthly_spend_capacity)
        else:
            return self._optimize_single(candidates, sort_by)

    def _load_all_rates(self):
        """
        Derives ALL rates from enriched card data.
        Returns dict: {slug: [ {category, rate, currency, details}, ... ]}
        """
        rates_by_slug = {}
        for slug, card in self.cards_map.items():
            # card['earning_rates'] contains the list of rate dicts
            rates_by_slug[slug] = card.get('earning_rates', [])
        return rates_by_slug


            
    def _optimize_single(self, candidates, sort_by='recommended'):
        if sort_by == 'value':
             # Sort by Net Value DESC
            candidates.sort(key=lambda x: (x['net_value'], x['roi']), reverse=True)
        else:
            # Default: Recommended (Rank Score)
            # Sort by Rank Score DESC, then Net Value DESC as tiebreaker
            candidates.sort(key=lambda x: (x['rank_score'], x['net_value']), reverse=True)
            
        return candidates[:10]
        
    def _optimize_combo(self, candidates, planned_spend, monthly_capacity):
        # Sort by Marginal Density DESC (still best for packing problem)
        # But we could arguably consider rank_score here too?
        # For now, let's keep density for the *selection* phase to maximize efficiency,
        # but the request was "incorporate match score when ranking".
        # The result of combo is a list.
        # If we change the sort here, we change WHICH cards are picked.
        # Let's keep the packer logic pure (Density) because "Match Score" is subjective utility,
        # whereas fitting into a spend budget is mathematical constraint.
        # However, we should display the match scores in the result.
        
        candidates.sort(key=lambda x: x['marginal_density'], reverse=True)
        
        selected = []
        remaining_spend = planned_spend
        
        current_monthly_load = 0.0
        
        for cand in candidates:
            if len(selected) >= 3: # Limit to 2-4 cards (let's say 3 for now)
                break
                
            req_spend = cand['req_spend']
            req_months = cand['req_months']
            monthly_req = req_spend / req_months if req_months > 0 else 0
            
            # Check Feasibility
            if req_spend <= remaining_spend:
                # Check Monthly Bandwidth
                if current_monthly_load + monthly_req <= monthly_capacity:
                    # Select this card
                    # Allocation: Min to unlock bonus
                    cand['allocated_spend'] = req_spend
                    remaining_spend -= req_spend
                    current_monthly_load += monthly_req
                    selected.append(cand)
            
        # Allocate remaining spend to selected card with highest ongoing_rate
        if remaining_spend > 0 and selected:
            # Find best earner among selected
            best_earner = max(selected, key=lambda x: x['ongoing_rate'])
            best_earner['allocated_spend'] += remaining_spend
            # Re-calculate net value for this card with extra spend
            # Original net_value was based on *planned_spend* (full spend).
            # We need to adjust selected cards to show value based on *allocated_spend*.
            
        # Recalculate Totals for Output
        final_results = []
        for cand in selected:
            allocated = cand.get('allocated_spend', 0)
            # Recalculate value based on ACTUAL allocation
            total_earn = allocated * cand['ongoing_rate']
            val = cand['bonus_value'] + total_earn - cand['annual_fee']
            cand['net_value'] = val # Update for display
            cand['roi'] = (val / allocated * 100) if allocated > 0 else 0
            
            # Update rank_score based on new net_value?
            # Rank score = Net Value + (Match Score * 2)
            # Match score doesn't change, but net_value did.
            cand['rank_score'] = val + (cand.get('match_score', 0) * 2.0)
            
            final_results.append(cand)
            
        return final_results
            


    def get_all_unique_categories(self):
        """
        Returns a sorted list of all unique category strings found in default_rates.csv.
        """
        all_rates = self._load_all_rates()
        unique_cats = set()
        
        for slug, rates in all_rates.items():
            for r in rates:
                cat_data = r['category']
                if isinstance(cat_data, str):
                    try:
                        cat_list = json.loads(cat_data)
                    except json.JSONDecodeError:
                        cat_list = [cat_data]
                else:
                    cat_list = cat_data if isinstance(cat_data, list) else [str(cat_data)]
                
                for c in cat_list:
                    # Filter out empty and "All Purchases"
                    if c and c.lower() != 'all purchases': 
                         unique_cats.add(c)
                         
        sorted_cats = sorted(list(unique_cats))
        return sorted_cats

    def calculate_spend_recommendations(self, amount, specific_category, parent_category, user_wallet_slugs, sibling_categories=None):
        """
        Recommends cards for a specific purchase amount and category.
        Also calculates synergies for wallet cards based on performance in sibling categories.
        
        Returns: { 'wallet': [], 'opportunities': [] }
        """
        if sibling_categories is None:
            sibling_categories = []
            
        all_rates = self._load_all_rates()
        
        wallet_recs = []
        opportunity_recs = []
        
        # Helper to find best rate for a card with fallback logic
        def get_best_rate_for_card(slug, rates_list):
            best_rate = 0.0
            best_rate_data = None
            match_type = 'Default' # 'Specific', 'Generic', 'Default'
            
            # Helper to check if a rate's category list contains a target string
            def rate_matches(r, target):
                if not target: return False, 0.0
                cat_data = r['category']
                if isinstance(cat_data, str):
                    try:
                        cat_list = json.loads(cat_data)
                    except json.JSONDecodeError:
                        cat_list = [cat_data]
                else:
                    cat_list = cat_data if isinstance(cat_data, list) else [str(cat_data)]
                
                for c_str in cat_list:
                    if c_str.lower() == target.lower():
                        return True, float(r.get('multiplier') or r.get('rate') or 0.0)
                return False, 0.0

            # 1. Try Specific Match (Step 2)
            if specific_category:
                # 1a. Exact Brand Match
                for r in rates_list:
                    is_match, val = rate_matches(r, specific_category)
                    if is_match and val > best_rate:
                        best_rate = val
                        best_rate_data = r
                        match_type = 'Specific'

                # 1b. Hardcoded Fallbacks (Direct Airline / Hotel)
                # If we haven't found a match yet (or want to maximize? User said "Direct Airline should also apply")
                # We should check this and take the higher of the two? Or just treat it as a valid specific match.
                
                fallback_target = None
                if parent_category:
                     if parent_category.lower() == 'airlines':
                         fallback_target = "Direct Airline Bookings"
                     elif parent_category.lower() == 'hotels':
                         fallback_target = "Direct Hotel Bookings"
                
                if fallback_target:
                    for r in rates_list:
                        is_match, val = rate_matches(r, fallback_target)
                        if is_match and val > best_rate:
                            best_rate = val
                            best_rate_data = r
                            match_type = 'Specific' # Count as specific per user intent

                # If found specific match (either brand or direct fallback), return it
                if match_type == 'Specific':
                    return best_rate, best_rate_data, 'Specific'
                
                # If specific category was provided but NO match found (and no fallback match),
                # User request: "does not match exactly ... always use the default rate."
                # This implies we SKIP the "Parent Match" step below for this case.
                pass 

            # 2. Try Parent Match (Step 1 - Only if Step 2 wasn't provided)
            # If specific_category IS provided, we skip this to enforce strictness + default fallback.
            elif parent_category:
                parent_best_rate = 0.0
                parent_match_data = None
                
                for r in rates_list:
                    is_match, val = rate_matches(r, parent_category)
                    if is_match and val > parent_best_rate:
                        parent_best_rate = val
                        parent_match_data = r
                
                if parent_match_data:
                    return parent_best_rate, parent_match_data, 'Generic'

            # 3. Fallback to Default / All Purchases
            default_best_rate = 0.0
            default_match_data = None
            
            for r in rates_list:
                is_base = r['is_default']
                is_match, val = rate_matches(r, 'All Purchases')
                
                current_val = float(r.get('multiplier') or r.get('rate') or 0.0)
                
                if is_base or is_match:
                    if current_val > default_best_rate:
                        default_best_rate = current_val
                        default_match_data = r
            
            return default_best_rate, default_match_data, 'Default'

        # Process ALL cards
        for slug, card_obj in self.cards_map.items():
            card_rates = all_rates.get(slug, [])
            
            rate_val, rate_data, match_type = get_best_rate_for_card(slug, card_rates)
            
            # If absolutely no rate found (unlikely if 'All Purchases' exists), skip or assume 0
            if not rate_data and rate_val == 0:
                 # Try to fallback to 1x if nothing else?
                 rate_val = 1.0
                 rate_data = {'currency': 'points', 'category': 'Base Estimate'}
                 match_type = 'Default'

            # Valuation (CPP)
            raw_cpp = card_obj.get('points_value_cpp') or card_obj.get('PointsValueCpp', '1.0')
            try:
                cpp = float(raw_cpp) if isinstance(raw_cpp, (int, float)) or raw_cpp.replace('.', '', 1).isdigit() else 1.0
            except:
                cpp = 1.0

            # Estimate Points & Value
            currency_lower = rate_data.get('currency', 'points').lower()
            
            # Calculations
            est_points = amount * rate_val
            
            if 'cash' in currency_lower:
                est_value = amount * (rate_val / 100.0)
                # Ensure points display logic matches user expectation (multiplier * amount as "points" equivalent?)
                # For consistency with previous step, we stick to:
                est_points = amount * rate_val 
            else:
                # Points: 3x -> 300 points -> Value = 300 * (cpp/100)
                est_value = est_points * (cpp / 100.0)
                
            # RENT LOGIC (3% Fee)
            # If category is Rent, apply 3% fee to value for all except Bilt
            if specific_category and specific_category.lower() == 'rent':
                if 'bilt' not in slug.lower(): # bilt-mastercard
                     fee = amount * 0.03
                     est_value -= fee

            # Determine Display Logic for "Matched Category"
            matched_display = "All Purchases"
            if rate_data.get('category'):
                raw_cats = rate_data['category']
                if isinstance(raw_cats, str):
                    try:
                         # Try JSON parse
                         cat_list = json.loads(raw_cats)
                    except:
                         cat_list = [raw_cats]
                else:
                    cat_list = raw_cats if isinstance(raw_cats, list) else [str(raw_cats)]
                
                # Check what matched
                found_match = False
                # Check specific
                if specific_category:
                     for c in cat_list:
                         if c.lower() == specific_category.lower():
                             matched_display = c
                             found_match = True
                             break
                # Check parent
                if not found_match and parent_category:
                     for c in cat_list:
                         if c.lower() == parent_category.lower():
                             matched_display = c
                             found_match = True
                             break
                # Fallback
                if not found_match:
                    # Likely All Purchases or Base Rate
                    if 'All Purchases' in cat_list:
                        matched_display = "All Purchases"
                    else:
                        matched_display = cat_list[0] # Show whatever category that drove this rate

            # Collect all unique categories for this card for display
            unique_categories = set()
            for r in card_rates:
                c_data = r['category']
                if isinstance(c_data, str):
                    try:
                        c_list = json.loads(c_data)
                    except json.JSONDecodeError:
                        c_list = [c_data]
                else:
                    c_list = c_data if isinstance(c_data, list) else [str(c_data)]
                
                for c in c_list:
                    unique_categories.add(c)

            # Currency Display Logic
            if 'cash' in currency_lower:
                currency_display = 'Cashback'
            else:
                # Capitalize (Points, Miles, Avios)
                currency_display = currency_lower.title() # "Avios", "Points"

            result_item = {
                'card': card_obj,
                'est_points': int(est_points),
                'est_value': est_value,
                'earning_rate': f"{rate_val}x" if 'cash' not in currency_lower else f"{rate_val}%",
                'category_matched': matched_display,
                'slug': slug,
                'card_name': card_obj.get('name', 'Unknown Card'),
                'categories': sorted(list(unique_categories)),
                'currency': currency_lower,
                'currency_display': currency_display,
                'match_type': match_type,
                'is_specific_match': match_type == 'Specific',
                'cpp': cpp
            }
            
            if slug in user_wallet_slugs:
                wallet_recs.append(result_item)
            else:
                opportunity_recs.append(result_item)
                
        # Sort and limit
        # Sort key: (is_specific, value)
        # specific='Specific' -> 1, else 0
        def sort_key(item):
            priority = 1 if item['match_type'] == 'Specific' else 0
            return (priority, item['est_value'])

        wallet_recs.sort(key=sort_key, reverse=True)
        
        # Identify Winner(s)
        if wallet_recs:
            max_val = wallet_recs[0]['est_value']
            for item in wallet_recs:
                item['is_winner'] = abs(item['est_value'] - max_val) < 0.01
                
            # Synergy Calculation for Wallet Cards
            if sibling_categories:
                # 1. Pre-calculate max rates for each sibling category across the wallet
                max_rates_by_sibling = {sib: 0.0 for sib in sibling_categories}
                
                # We need to look at ALL wallet cards to find the true max, even those not in wallet_recs (though wallet_recs should have all by definition of calculate_recommendations logic filtering)
                # Actually calculate_recommendations iterates all known cards and splits by wallet/opportunity.
                # So wallet_recs contains all wallet cards.
                
                for item in wallet_recs:
                    slug = item['slug']
                    card_rates = all_rates.get(slug, [])
                    
                    for sibling in sibling_categories:
                        sib_rate = 0.0
                        # Simplified lookup
                        for r in card_rates:
                            cat_data = r['category']
                            if isinstance(cat_data, str):
                                try:
                                    cat_list = json.loads(cat_data)
                                except:
                                    cat_list = [cat_data]
                            else:
                                cat_list = cat_data if isinstance(cat_data, list) else [str(cat_data)]
                            
                            for c in cat_list:
                                if c.lower() == sibling.lower():
                                    if float(r.get('multiplier') or r.get('rate') or 0.0) > sib_rate:
                                        sib_rate = float(r.get('multiplier') or r.get('rate') or 0.0)
                        
                        if sib_rate > max_rates_by_sibling[sibling]:
                            max_rates_by_sibling[sibling] = sib_rate

                # 2. Assign Synergies
                for item in wallet_recs:
                    slug = item['slug']
                    card_rates = all_rates.get(slug, [])
                    
                    best_synergy = None
                    best_synergy_rate = 0.0
                    
                    for sibling in sibling_categories:
                        # Find rate
                        sib_rate = 0.0
                        for r in card_rates:
                            cat_data = r['category']
                            if isinstance(cat_data, str):
                                try:
                                    cat_list = json.loads(cat_data)
                                except:
                                    cat_list = [cat_data]
                            else:
                                cat_list = cat_data if isinstance(cat_data, list) else [str(cat_data)]
                            for c in cat_list:
                                if c.lower() == sibling.lower():
                                    if float(r.get('multiplier') or r.get('rate') or 0.0) > sib_rate:
                                        sib_rate = float(r.get('multiplier') or r.get('rate') or 0.0)
                        
                        if sib_rate > 0:
                            # Prioritize the sibling that gives the highest rate for this card
                            if sib_rate > best_synergy_rate:
                                best_synergy_rate = sib_rate
                                
                                # Check vs Max for this sibling category
                                max_for_sib = max_rates_by_sibling.get(sibling, 0.0)
                                is_tied_for_top = (sib_rate >= max_for_sib and max_for_sib > 0)
                                
                                # Calculate estimated value for this sibling at this rate
                                if 'cash' in item['currency']:
                                    sib_est_value = amount * (sib_rate / 100.0)
                                else:
                                    sib_est_value = (amount * sib_rate) * (item['cpp'] / 100.0)
                                
                                # Get the best wallet value (from the top card for the ORIGINAL category)
                                best_wallet_value = max_val if wallet_recs else 0.0
                                
                                # Default: No label (will only show if meets criteria below)
                                label = None
                                color_class = "text-slate-700" 
                                bg_class = "border-slate-100"
                                text_class = "text-slate-500"
                                
                                # EQUAL PERFORMER: 
                                # This card has a subcategory match (the sibling) AND 
                                # ties for the highest rate in wallet for this sibling category
                                if is_tied_for_top:
                                    label = "EQUAL PERFORMER"
                                    color_class = "text-indigo-600"
                                    bg_class = "border-indigo-100"
                                    text_class = "text-indigo-700"
                                # POTENTIAL CANDIDATE:
                                # A different subcategory (sibling) that yields equal or higher 
                                # estimated value compared to the best wallet card's value
                                # Also requires 4x+ points or high cash back rate
                                elif sib_est_value >= best_wallet_value and (sib_rate >= 4.0 or ('cash' in item['currency'] and sib_rate >= 4.0)):
                                    label = "POTENTIAL CANDIDATE"
                                    color_class = "text-green-700" 
                                    bg_class = "border-green-100"
                                    text_class = "text-green-600"
                                # SOLID CHOICE:
                                # Not Equal Performer or Potential Candidate, but 
                                # estimated value is within 85% of the top value
                                elif best_wallet_value > 0 and sib_est_value >= (best_wallet_value * 0.85):
                                    label = "SOLID CHOICE"
                                    color_class = "text-slate-700" 
                                    bg_class = "border-slate-100"
                                    text_class = "text-slate-500"
                                    
                                # Description
                                if 'cash' in item['currency']:
                                    desc = f"Earns {sib_rate}% on {sibling}."
                                else:
                                    desc = f"Earns {sib_rate}x points on {sibling}."
                                    
                                # Only create synergy if card qualifies for a label
                                if label:
                                    best_synergy = {
                                        'name': sibling,
                                        'rate': sib_rate,
                                        'label': label,
                                        'description': desc,
                                        'color_class': color_class,
                                        'bg_class': bg_class,
                                        'text_class': text_class
                                    }
                    
                    item['synergy'] = best_synergy

        # 3. Calculate Opportunity Cost / Net Gain
        opportunity_recs.sort(key=sort_key, reverse=True)
        
        # Calculate Lost Value
        best_wallet_val = wallet_recs[0]['est_value'] if wallet_recs else 0.0
        best_opp_val = opportunity_recs[0]['est_value'] if opportunity_recs else 0.0
        
        lost_value = max(0.0, best_opp_val - best_wallet_val)
        net_gain = best_opp_val - best_wallet_val

        # Calculate differential for each opportunity vs best wallet card
        for item in opportunity_recs:
            item['diff_vs_wallet'] = max(0.0, item['est_value'] - best_wallet_val)
        
        # Helper to strict-ify data for JSON serialization in templates
        def sanitize_card_for_json(card_data):
            # ... (helper code)
            clean = {}
            for k, v in card_data.items():
                if isinstance(v, (datetime, date)):
                    clean[k] = v.isoformat()
                else:
                    clean[k] = v
            return clean

        # Sanitize cards in results
        for item in wallet_recs:
            # Ensure slug is available at top level for template convenience
            item['slug'] = item['card'].get('slug', item['card'].get('slug-id', item['card'].get('id', '')))
            item['card_json'] = json.dumps(sanitize_card_for_json(item['card']))
            
        for item in opportunity_recs:
            item['slug'] = item['card'].get('slug', item['card'].get('slug-id', item['card'].get('id', '')))
            item['card_json'] = json.dumps(sanitize_card_for_json(item['card']))

        return {
            'wallet': wallet_recs,
            'opportunities': opportunity_recs[:5],
            'lost_value': lost_value,
            'net_gain': net_gain
        }
