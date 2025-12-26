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
        self.bonuses = self._load_signup_bonuses()
        self.default_rates = self._load_default_rates()

    def _load_signup_bonuses(self):
        csv_path = os.path.join(settings.BASE_DIR, 'default_signup.csv')
        bonuses = {}
        if not os.path.exists(csv_path):
            return bonuses
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    slug = row.get('slug-id')
                    if slug:
                        bonuses[slug] = row
        except Exception as e:
            print(f"Error reading signup CSV: {e}")
        return bonuses

    def _load_default_rates(self):
        """
        Loads the simple default ongoing rate for each card.
        We look for 'IsDefault' == 'Yes'.
        Returns dict: {slug: {'rate': float, 'currency': str}}
        """
        csv_path = os.path.join(settings.BASE_DIR, 'default_rates.csv')
        rates = {}
        if not os.path.exists(csv_path):
            return rates
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    if row.get('IsDefault') == 'Yes':
                        slug = row.get('slug-id')
                        try:
                            rate = float(row.get('EarningRate', 0))
                        except ValueError:
                            rate = 0.0
                            
                        rates[slug] = {
                            'rate': rate,
                            'currency': row.get('Currency', 'points')
                        }
        except Exception as e:
            print(f"Error reading default rates CSV: {e}")
        return rates

    def calculate_recommendations(self, planned_spend, duration_months, user_wallet_slugs=None, mode='single'):
        """
        Core optimization logic.
        """
        if user_wallet_slugs is None:
            user_wallet_slugs = set()
            
        # Fixed date for simulation/optimization as per requirements
        today = date(2025, 12, 24)
        monthly_spend_capacity = planned_spend / duration_months if duration_months > 0 else 0
        
        candidates = []
        
        for slug, bonus_data in self.bonuses.items():
            # 1. Filter: In Wallet
            if slug in user_wallet_slugs:
                continue
                
            # 2. Filter: Exist in DB
            card_obj = self.cards_map.get(slug)
            if not card_obj:
                continue
                
            # 3. Parse Bonus Data
            try:
                req_spend = float(bonus_data.get('SpendAmount', 0))
                req_months = int(bonus_data.get('SignupDurationMonths', 0))
                bonus_qty = float(bonus_data.get('SignUpBonusValue', 0))
                bonus_type = bonus_data.get('SignUpBonusType', 'Points')
                eff_date_str = bonus_data.get('EffectiveDate', '').strip()
            except (ValueError, TypeError):
                continue
                
            # 5. Filter: Infeasible
            if req_spend > planned_spend:
                continue
            # Logic Update: Removed hard duration constraint.
            # We now allow longer durations if the monthly run rate fits within capacity.

            # 6. Additional Filter: Monthly Spend Constraint
            # "monthly_req = spend_amount / signup_duration_months <= monthly_spend_capacity"
            if req_months > 0:
                monthly_req = req_spend / req_months
                # Allow a small buffer or strict? Rule said <=.
                if monthly_req > monthly_spend_capacity + 1.0: # +1 for float tolerance
                    continue

            # 7. Valuation
            # Determine CPP from card object
            # Default to 1.0 if N/A or missing
            
            raw_cpp = card_obj.get('points_value_cpp') or card_obj.get('PointsValueCpp', '1.0')
            try:
                # Handle 'N/A' or other non-numeric strings by defaulting to 1.0
                if isinstance(raw_cpp, str) and not raw_cpp.replace('.', '', 1).isdigit():
                     cpp = 1.0
                else:
                     cpp = float(raw_cpp)
            except (ValueError, TypeError):
                cpp = 1.0
            
            # Bonus Value ($)
            if bonus_type.lower() == 'cash':
                bonus_value = bonus_qty
            else:
                bonus_value = bonus_qty * (cpp / 100.0)
                
            # Ongoing Rate Value ($ per $1 spend)
            default_rate_info = self.default_rates.get(slug, {'rate': 0, 'currency': 'points'})
            def_rate_val = default_rate_info['rate']
            def_currency = default_rate_info['currency']
            
            # Convert ongoing rate to dollar value per dollar spent
            if 'cash' in def_currency.lower() or 'cash' in bonus_type.lower(): # Fallback to bonus type if rate currency ambiguous
                 # Cash back rate is usually percent (e.g. 1.5 for 1.5%) -> 0.015 dollars per dollar
                 # Wait, usually "1.5" in CSV means 1.5%.
                 ongoing_rate_dollar = def_rate_val / 100.0
            else:
                 # Points/Miles: e.g. 2x points -> 2 * CPP / 100
                 ongoing_rate_dollar = def_rate_val * (cpp / 100.0)

            # Metrics Calculation
            # "total_earn_from_spend = planned_spend * ongoing_rate"
            # NOTE: User requirement says "Includes bonus + ongoing on full spend".
            total_earn_from_spend = planned_spend * ongoing_rate_dollar
            
            total_value = bonus_value + total_earn_from_spend
            
            annual_fee = float(card_obj.get('annual_fee', 0))
            net_value = total_value - annual_fee
            
            # ROI
            if planned_spend > 0:
                roi = (net_value / planned_spend) * 100
            else:
                roi = 0 # Or -inf
                
            # Marginal Density
            # (bonus_value - fee) / spend_amount + ongoing_rate
            # If spend_amount (req_spend) is 0, use placeholder 500
            denom = req_spend if req_spend > 0 else 500.0
            marginal_density = (bonus_value - annual_fee) / denom + ongoing_rate_dollar

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
                'bonus_text': f"{int(bonus_qty):,} {bonus_type}" if bonus_qty > 0 else "No Bonus"
            })
            
        # Optimization Algorithm
        if mode == 'combo':
            return self._optimize_combo(candidates, planned_spend, monthly_spend_capacity)
        else:
            return self._optimize_single(candidates)
            
    def _optimize_single(self, candidates):
        # Sort by Net Value DESC, then ROI DESC
        candidates.sort(key=lambda x: (x['net_value'], x['roi']), reverse=True)
        return candidates[:10]
        
    def _optimize_combo(self, candidates, planned_spend, monthly_capacity):
        # Sort by Marginal Density DESC
        candidates.sort(key=lambda x: x['marginal_density'], reverse=True)
        
        selected = []
        remaining_spend = planned_spend
        # We need to track monthly utilization too strictly if we want to be perfect,
        # but the prompt says "monthly_req <= monthly_spend_capacity" which is per-card check (already done in filter).
        # "Ensure sum monthly_req <= monthly_spend_capacity" is Global constraint.
        
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
            final_results.append(cand)
            
        return final_results
            
    def _load_all_rates(self):
        """
        Loads ALL rates from default_rates.csv, not just default ones.
        Returns dict: {slug: [ {category, rate, currency, details}, ... ]}
        """
        csv_path = os.path.join(settings.BASE_DIR, 'default_rates.csv')
        rates_by_slug = {}
        if not os.path.exists(csv_path):
            return rates_by_slug
            
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    slug = row.get('slug-id')
                    if not slug:
                        continue
                        
                    if slug not in rates_by_slug:
                        rates_by_slug[slug] = []
                        
                    try:
                        rate_val = float(row.get('EarningRate', 0))
                    except ValueError:
                        rate_val = 0.0
                        
                    rates_by_slug[slug].append({
                        'category': row.get('RateCategory', '[]'), # Changed from BenefitCategory
                        'rate': rate_val,
                        'currency': row.get('Currency', 'points'),
                        'details': row.get('AdditionalDetails', ''),
                        'is_default': row.get('IsDefault') == 'Yes'
                    })
        except Exception as e:
            print(f"Error reading all rates CSV: {e}")
            
        return rates_by_slug

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
                    if c and c.lower() != 'all purchases': 
                         unique_cats.add(c)
                         
        sorted_cats = sorted(list(unique_cats))
        return sorted_cats

    def calculate_spend_recommendations(self, amount, category, user_wallet_slugs):
        """
        Recommends cards for a specific purchase amount and category.
        Returns: { 'wallet': [], 'opportunities': [] }
        """
        all_rates = self._load_all_rates()
        
        wallet_recs = []
        opportunity_recs = []
        
        # Category Mapping (Frontend -> CSV Categories)
        # Frontend: [Dining, Travel, Groceries, Gas, Tech & Gadgets, Everything Else]
        # CSV contains diverse strings. We need a fuzzy matcher or mapped list.
        category_map = {
            'Dining': ['Dining', 'Restaurants'],
            'Travel': ['Travel', 'Flights', 'Hotels', 'Transit', 'Car Rentals'],
            'Groceries': ['Groceries', 'Supermarkets', 'Whole Foods'],
            'Gas': ['Gas', 'EV Charging', 'Fuel'],
            'Tech & Gadgets': ['Online Retail', 'Electronics', 'Amazon', 'Best Buy', 'Apple'],
            'Dining': ['Dining', 'Restaurants'],
            'Travel': ['Travel', 'Flights', 'Hotels', 'Transit', 'Car Rentals'],
            'Groceries': ['Groceries', 'Supermarkets', 'Whole Foods'],
            'Gas': ['Gas', 'EV Charging', 'Fuel'],
            'Tech & Gadgets': ['Online Retail', 'Electronics', 'Amazon', 'Best Buy', 'Apple'],
            'Everything Else': ['All Purchases'] # Still used for keyword matching if needed
        }
        
        target_keywords = category_map.get(category, ['All Purchases'])
        
        # Helper to find best rate for a card
        def get_best_rate_for_card(slug, rates_list):
            best_rate = 0.0
            best_rate_data = None
            
            # Check specific category matches first
            for r in rates_list:
                # Parse category JSON if string
                cat_data = r['category']
                if isinstance(cat_data, str):
                    try:
                        cat_list = json.loads(cat_data)
                    except json.JSONDecodeError:
                        cat_list = [cat_data]
                else:
                    cat_list = cat_data if isinstance(cat_data, list) else [str(cat_data)]

                # Check if any keyword matches
                match = False
                if category == 'Everything Else':
                     if r['is_default']:
                         match = True
                else:
                    for cat_str in cat_list:
                        for kw in target_keywords:
                            if kw.lower() in cat_str.lower():
                                match = True
                                break
                        if match: break
                            
                if match:
                    if r['rate'] > best_rate:
                        best_rate = r['rate']
                        best_rate_data = r
                        # Normalize category field for result to be the matching string
                        # Or keep the whole list? For "category_matched" we might want the specific match or the primary one.
                        # Let's attach the matched list for now or just the first one?
                        # user wants to display ALL unique rate categories for the card later.
                        pass
            
            # Fallback to "All Purchases" / Default if no specific match
            if best_rate == 0.0:
                for r in rates_list:
                    if r['is_default'] or 'All Purchases' in r['category']:
                         # If we already found a rate (e.g. 0), override? 
                         # Usually All Purchases is the floor.
                         if r['rate'] > best_rate:
                             best_rate = r['rate']
                             best_rate_data = r
            
            return best_rate, best_rate_data

        # Process ALL cards
        for slug, card_obj in self.cards_map.items():
            card_rates = all_rates.get(slug, [])
            if not card_rates:
                continue

            rate_val, rate_data = get_best_rate_for_card(slug, card_rates)
            
            if not rate_data:
                continue
                
            # Valuation
            raw_cpp = card_obj.get('points_value_cpp') or card_obj.get('PointsValueCpp', '1.0')
            try:
                cpp = float(raw_cpp) if isinstance(raw_cpp, (int, float)) or raw_cpp.replace('.', '', 1).isdigit() else 1.0
            except:
                cpp = 1.0

            # Estimate Points
            # If cash back currency, points = dollar value? 
            # Or points = amount * rate (if rate is %)
            # Rate in CSV is usually "3" for 3x or 3%.
            est_points = amount * rate_val
            
            # Estimate Value ($)
            currency_lower = rate_data['currency'].lower()
            if 'cash' in currency_lower:
                # Cash back: Rate 3 means 3% usually -> 0.03 * amount
                # Wait, earlier logic said:
                # "Cash back rate is usually percent (e.g. 1.5 for 1.5%) -> 0.015 dollars per dollar"
                # But here rate_val is e.g. 1.5. 
                # So dollar value = amount * (rate_val / 100)
                est_value = amount * (rate_val / 100.0)
                # For display consistency, let's show "Points equivalent" as est_value * 100?
                # Or just show points as the raw 300 (for $100 * 3%).
                # User mock shows "1,500" Est Points.
                est_points = amount * rate_val # e.g. 100 * 3 = 300
            else:
                # Points: 3x -> 300 points
                est_value = est_points * (cpp / 100.0)

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
            
            # Filter out "All Purchases" or similar generic if desired, or keep all.
            # User said: "get all unique rates categories for each card and display it"
            
            # Format category_matched for display
            # If rate_data has a list, join them or pick one? 
            # In the loop above `get_best_rate_for_card` we didn't update `rate_data['category']` which is still the raw string/json.
            # Let's clean it up for the single match too.
            matched_cats_str = rate_data['category']
            if isinstance(matched_cats_str, str):
                try:
                    m_list = json.loads(matched_cats_str)
                    matched_display = ", ".join(m_list)
                except:
                    matched_display = matched_cats_str
            else:
                 matched_display = ", ".join(matched_cats_str) if isinstance(matched_cats_str, list) else str(matched_cats_str)

            result_item = {
                'card': card_obj,
                'est_points': int(est_points),
                'est_value': est_value,
                'earning_rate': f"{rate_val}x" if 'cash' not in currency_lower else f"{rate_val}%",
                'category_matched': matched_display,
                'slug': slug,
                'card_name': card_obj.get('name', 'Unknown Card'),
                'categories': sorted(list(unique_categories))
            }
            
            if slug in user_wallet_slugs:
                wallet_recs.append(result_item)
            else:
                opportunity_recs.append(result_item)
                
        # Sort and limit
        wallet_recs.sort(key=lambda x: x['est_value'], reverse=True)
        opportunity_recs.sort(key=lambda x: x['est_value'], reverse=True)
        
        # Calculate Lost Value
        best_wallet_val = wallet_recs[0]['est_value'] if wallet_recs else 0.0
        best_opp_val = opportunity_recs[0]['est_value'] if opportunity_recs else 0.0
        
        lost_value = max(0.0, best_opp_val - best_wallet_val)
        
        # Helper to strict-ify data for JSON serialization in templates
        def sanitize_card_for_json(card_data):
            # Create a copy to avoid mutating original cache if needed (though cards_map is ref)
            # Actually we just need to ensure datetime objects are strings
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
            'wallet': wallet_recs[:3],
            'opportunities': opportunity_recs[:3],
            'lost_value': lost_value
        }
