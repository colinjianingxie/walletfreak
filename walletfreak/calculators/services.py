import csv
import os
import math
from datetime import datetime, date
from django.conf import settings
from core.services import db
from .points_valuations import get_cents_per_point

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
                
            # 4. Filter: Expired (DISABLED)
            # User Request: "Do not exclude cards-expired, assume all cards are active."
            # if eff_date_str:
            #     try:
            #         eff_date = datetime.strptime(eff_date_str, '%Y-%m-%d').date()
            #         if eff_date < today:
            #             continue
            #     except ValueError:
            #         pass
            
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
            # Determine CPP
            cpp = get_cents_per_point(slug, bonus_type)
            
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
