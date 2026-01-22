from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.services import db
from core.services.amadeus_service import AmadeusService
from django.conf import settings
import csv
import json
import os
import glob
import math
from datetime import datetime, timedelta

DATA_DIR = '/Users/xie/Desktop/projects/walletfreak/walletfreak/walletfreak_data'

# --- CONSTANTS & CONFIG ---

# Point Valuations (CPP - Cents Per Point)
# In a real app, these might come from DB or User Settings.
VALUATIONS = {
    'chase_ur': 1.7,
    'amex_mr': 1.6,
    'citi_ty': 1.6,
    'cap1_miles': 1.7,
    'bilt_rewards': 1.8,
    'world_of_hyatt': 1.8,
    'hilton_honors': 0.6,
    'marriott_bonvoy': 0.8,
    'ihg_one_rewards': 0.6,
    'wyndham_rewards': 1.0,
    'accor_all': 2.0, # Approximate, fixed rev based
    'best_western_rewards': 0.6,
    'choice_privileges': 0.6,
    'sonesta_travel_pass': 0.8,
}

def get_valuation(program_id):
    return VALUATIONS.get(program_id, 1.0)

def load_hotel_mapping():
    mapping = {}
    path = os.path.join(DATA_DIR, 'hotel_code_mapping.csv')
    if os.path.exists(path):
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Chain Code']:
                    # Map Code -> {Name, Program ID, Program Name}
                    mapping[row['Chain Code']] = {
                        'chain_name': row['Chain Name'],
                        'program_id': row['Program ID'],
                        'program_name': row['Loyalty Program']
                    }
    return mapping

# --- LOGIC HELPERS ---

def identify_user_cards(user_cards):
    """Identify key cards for portal logic."""
    inventory = {
        'has_amex_plat': False,
        'has_amex_gold': False, # checking just in case
        'has_chase_csr': False,
        'has_chase_csp': False,
        'has_chase_cip': False, # Ink Preferred
        'has_capital_one_vx': False,
    }
    
    for c in user_cards:
        name = c.get('name', '').lower()
        issuer = c.get('issuer', '').lower()
        
        if 'american express' in issuer or 'amex' in name:
            if 'platinum' in name: inventory['has_amex_plat'] = True
            if 'gold' in name: inventory['has_amex_gold'] = True
            
        if 'chase' in issuer:
            if 'reserve' in name: inventory['has_chase_csr'] = True
            if 'preferred' in name: inventory['has_chase_csp'] = True
            if 'ink business preferred' in name: inventory['has_chase_cip'] = True
            
        if 'venture x' in name: inventory['has_capital_one_vx'] = True
            
    return inventory

def calculate_effective_cost(cash_price, points_earned_val, perks_val=0):
    """
    Effective Cost = Cash Price - (Value of Points Earned) - (Value of Perks)
    """
    return cash_price - points_earned_val - perks_val

def estimate_hotel_redemption_cost(cash_price, program_id):
    """
    Estimate points needed for a direct hotel redemption.
    Using dynamic pricing models approx.
    """
    val_cpp = get_valuation(program_id)
    # Convert cents to dollars for cpp calc: val_cpp is cents.
    # Price $100 -> 10000 cents. Points = 10000 / 1.0 = 10000.
    
    # Formula: Price / (CPP / 100)
    needed = int(cash_price / (val_cpp / 100.0))
    
    # Rounding logic common in programs (e.g. Hyatt is categorical, but specific dynamic is hard)
    # Let's round to nearest 1000 for cleaner UI
    return round(needed / 1000) * 1000


# --- MAIN VIEW ---

@login_required
def index(request):
    uid = request.session.get('uid')
    
    # 1. Fetch User Data
    user_balances = db.get_user_loyalty_balances(uid) if uid else []
    user_cards = db.get_user_cards(uid, status='active', hydrate=True) if uid else []
    
    wallet_balances = {b['program_id']: int(b.get('balance', 0)) for b in user_balances}
    card_inventory = identify_user_cards(user_cards)
    
    # Linked/Co-brand Cards Map
    linked_cards_map = {}
    for c in user_cards:
        lp = c.get('loyalty_program')
        if lp:
            linked_cards_map[lp] = c # Assuming one active per program for simplicity

    # 2. Metadata
    hotel_mapping = load_hotel_mapping()
    raw_rules = db.get_all_transfer_rules()
    transfer_rules = {}
    for r in raw_rules:
        sid = r.get('source_program_id')
        if sid:
            transfer_rules[sid] = r.get('transfer_partners', [])
            
    # 3. Search Logic
    hotels = []
    location_query = request.GET.get('location')
    
    # Default Dates Logic
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=3) # Tomorrow + 2 days
    
    default_check_in = tomorrow.strftime('%Y-%m-%d')
    default_check_out = day_after.strftime('%Y-%m-%d')
    
    if location_query:
        if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
            service = AmadeusService()
            
            dates_str = request.GET.get('dates', '')
            check_in_raw = request.GET.get('checkInDate')
            check_out_raw = request.GET.get('checkOutDate')
            
            # Use provided or defaults
            check_in = check_in_raw if check_in_raw else default_check_in
            check_out = check_out_raw if check_out_raw else default_check_out
            
            # VALIDATION: Prevent same day
            if check_in == check_out:
                # Force +1 day
                try:
                    cin_date = datetime.strptime(check_in, '%Y-%m-%d')
                    check_out = (cin_date + timedelta(days=1)).strftime('%Y-%m-%d')
                except:
                    pass

            # Basic date parsing fallback if needed (omitted for brevity, relying on inputs)
            
            search_params = {
                'radius': request.GET.get('radius'),
                'chainCodes': request.GET.get('chainCodes'),
                'ratings': request.GET.get('ratings'),
                'maxPrice': request.GET.get('maxPrice'),
                'check_in': check_in,
                'check_out': check_out,
                'adults': request.GET.get('guests')
            }
            # Clean params
            search_params = {k: v for k, v in search_params.items() if v}

            try:
                api_results = service.search_hotel_offers_by_city(location_query, **search_params)

            except Exception as e:
                print(f"Amadeus Error: {e}")
                api_results = []
                
            if api_results:
                # Dedupe Hotel IDs for Sentiment
                hotel_ids = list(set([o.get('hotel', {}).get('hotelId') for o in api_results if o.get('hotel', {}).get('hotelId')]))
                sentiment_map = {}
                # TODO: Re-enable sentiment when quota permits or handling robustly
                # try:
                #     sentiments = service.get_hotel_sentiments(hotel_ids)
                #     sentiment_map = {s['hotelId']: s.get('overallRating') for s in sentiments}
                # except: pass

                for offer in api_results:
                    try:
                        hotel_data = offer.get('hotel', {})
                        offers_data = offer.get('offers', [])
                        if not offers_data: continue
                        
                        price_obj = offers_data[0].get('price', {})
                        cash_price = float(price_obj.get('total', 0))
                        currency = price_obj.get('currency', 'USD')
                        
                        # Only support USD logic for now
                        if currency != 'USD' and currency != 'US' and '$' not in currency:
                            # Simple FX fallback or skip? Let's process but warning labels might be off.
                            pass

                        chain_code = hotel_data.get('chainCode', '')
                        mapped = hotel_mapping.get(chain_code, {})
                        
                        hotel_name = hotel_data.get('name', 'Unknown Hotel').title()
                        brand_name = mapped.get('chain_name', chain_code)
                        program_id = mapped.get('program_id')
                        program_name = mapped.get('program_name')
                        
                        rating = sentiment_map.get(hotel_data.get('hotelId'))
                        if not rating: rating = 4.5 # Fallback mock rating

                        # --- STRATEGY GENERATION ---
                        strategies = []

                        # A. CASH DIRECT (Best Card)
                        if True:
                            # 1. Determine best multiplier
                            mult = 1
                            card_name = "Debit/Cash"
                            
                            # Check Co-brand
                            if program_id and program_id in linked_cards_map:
                                c = linked_cards_map[program_id]
                                card_name = c.get('name')
                                # Heuristic multipliers
                                if 'Aspire' in card_name: mult = 14
                                elif 'Surpass' in card_name: mult = 12
                                elif 'Brilliant' in card_name: mult = 21 # 6x card + 15x status? usually 6x card only here. Status is separate.
                                # Let's stick to Card Multipliers.
                                elif 'Hyatt' in card_name: mult = 4
                                elif 'Marriott' in card_name: mult = 6
                                elif 'Hilton' in card_name: mult = 7
                                elif 'IHG' in card_name: mult = 10
                            
                            # Check General Travel Cards if better
                            general_best = 1
                            general_name = "Cash"
                            
                            if card_inventory['has_chase_csr']:
                                general_best = 3
                                general_name = "Chase Sapphire Reserve"
                            elif card_inventory['has_chase_csp']:
                                general_best = 2
                                general_name = "Chase Sapphire Preferred"
                            elif card_inventory['has_amex_plat']: 
                                general_best = 1 # Amex Plat is 1x on hotels unless prepaid portal
                                general_name = "Amex Platinum"
                                # But Green is 3x? Assume user might have better.
                            
                            # Valuations for earned points
                            earned_val_cpp = 1.0
                            if 'Chase' in card_name or 'Chase' in general_name: earned_val_cpp = get_valuation('chase_ur')
                            elif 'Amex' in general_name: earned_val_cpp = get_valuation('amex_mr')
                            elif program_id: earned_val_cpp = get_valuation(program_id)
                            
                            # Compare Co-brand vs General
                            final_mult = mult
                            final_card = card_name
                            
                            # Simple comparison logic (mult * val vs general_best * val)
                            # Approximate: Hotel points usually worth less (0.6-0.8) vs Bank (1.6-1.7)
                            # e.g. Hilton 14x * 0.6 = 8.4% return. Chase 3x * 1.7 = 5.1% return.
                            # So co-brand usually wins high mults.
                            
                            if card_name == "Debit/Cash" and general_best > 1:
                                final_mult = general_best
                                final_card = general_name
                            
                            pts_earned = int(cash_price * final_mult)
                            value_earned = pts_earned * (earned_val_cpp / 100.0)
                            
                            eff_cost = calculate_effective_cost(cash_price, value_earned)
                            
                            strategies.append({
                                'type': 'cash_direct',
                                'label': f"Cash ({final_card})",
                                'sub_label': f"Earn {final_mult}x Points",
                                'cost_display': f"${cash_price:.0f}",
                                'effective_cost': eff_cost,
                                'details_earned': f"{pts_earned:,} pts",
                                'details_value': value_earned,
                                'icon': 'credit-card',
                                'card_name': final_card
                            })

                        # B. PORTAL STRATEGIES
                        # 1. Amex FHR (Cash)
                        if card_inventory['has_amex_plat']:
                            # Simplified assumption: FHR available for luxury/high-end
                            is_luxury = float(cash_price) > 400 or (rating and float(rating) > 4.5)
                            if is_luxury:
                                earned_pts = int(cash_price * 5)
                                val_earned = earned_pts * (get_valuation('amex_mr') / 100.0)
                                perks_val = 100 # $100 experience credit
                                eff_cost = calculate_effective_cost(cash_price, val_earned, perks_val)
                                
                                strategies.append({
                                    'type': 'portal_amex_fhr',
                                    'label': "Cash (Amex FHR)",
                                    'sub_label': "5x Pts + FHR Perks",
                                    'cost_display': f"${cash_price:.0f}",
                                    'effective_cost': eff_cost,
                                    'details_earned': f"{earned_pts:,} pts + $100",
                                    'details_value': val_earned + perks_val,
                                    'icon': 'star',
                                    'card_name': 'Amex Platinum'
                                })

                        # 2. Chase Travel (Cash 10x/5x)
                        if card_inventory['has_chase_csr'] or card_inventory['has_chase_csp']:
                            mult = 10 if card_inventory['has_chase_csr'] else 5
                            card = "Chase Sapphire Reserve" if card_inventory['has_chase_csr'] else "Chase Sapphire Preferred"
                            
                            earned_pts = int(cash_price * mult)
                            val_earned = earned_pts * (get_valuation('chase_ur') / 100.0)
                            eff_cost = calculate_effective_cost(cash_price, val_earned)
                            
                            strategies.append({
                                'type': 'portal_chase_cash',
                                'label': "Cash (Chase Portal)",
                                'sub_label': f"Earn {mult}x Points",
                                'cost_display': f"${cash_price:.0f}",
                                'effective_cost': eff_cost,
                                'details_earned': f"{earned_pts:,} pts",
                                'details_value': val_earned,
                                'icon': 'globe',
                                'card_name': card
                            })

                        # C. TRANSFER PARTNERS
                        if program_id:
                            # Estimated Redemption cost (Destination Currency, e.g. Marriott Pts)
                            # This ensures all transfers to the same partner use the same base cost.
                            dest_points_needed = estimate_hotel_redemption_cost(cash_price, program_id)
                            
                            # Check Transfer Paths
                            for source_id, partners in transfer_rules.items():
                                for partner in partners:
                                    if partner['destination_program_id'] == program_id:
                                        # Valid transfer
                                        ratio = partner['ratio']
                                        
                                        # Calculate Source Points Needed
                                        # Destination Pts = Source Pts * Ratio
                                        # Source Pts = Destination Pts / Ratio
                                        source_points_needed = math.ceil(dest_points_needed / ratio)
                                        
                                        # Opportunity Cost = Source Points * Source CPP
                                        source_val_cpp = get_valuation(source_id)
                                        opp_cost = source_points_needed * (source_val_cpp / 100.0)
                                        
                                        # Ratio formatting: 1.0 -> 1, 1.5 -> 1.5
                                        ratio_display = f"{ratio:.1f}".rstrip('0').rstrip('.')
                                        
                                        # Redemption CPP (Value you get for spending these points)
                                        # = Cash Price / Points Needed
                                        redemption_cpp = 0
                                        if source_points_needed > 0:
                                            redemption_cpp = (cash_price / source_points_needed) * 100.0
                                            
                                        # Details Text Loginc
                                        details = f"Est. based on {source_val_cpp}cpp."
                                        if redemption_cpp > source_val_cpp:
                                            details += " Strong redemption value."
                                        else:
                                            details += f" Only worth if < {source_points_needed:,} pts."
                                        
                                        src_name_map = {'chase_ur': 'Chase', 'amex_mr': 'Amex', 'bilt_rewards': 'Bilt', 'citi_ty': 'Citi', 'cap1_miles': 'Capital One'}
                                        src_display = src_name_map.get(source_id, source_id.title())

                                        strategies.append({
                                            'type': 'transfer',
                                            'label': f"Transfer {src_display} \u2192 {program_name}",
                                            'sub_label': f"1:{ratio_display} Ratio",
                                            'cost_display': f"~{source_points_needed:,} pts",
                                            'cost_cpp_display': f"{redemption_cpp:.2f} cpp", # Passed for template
                                            'effective_cost': opp_cost,
                                            'details_earned': details,
                                            'details_value': 0, 
                                            'icon': 'arrow-right-left',
                                            'card_name': f"{src_display} Points"
                                        })

                        # D. PAY WITH POINTS (Portals)
                        # 1. Chase Pay Yourself Back / Portal Redemption
                        if card_inventory['has_chase_csr'] or card_inventory['has_chase_csp']:
                            rate = 1.5 if card_inventory['has_chase_csr'] else 1.25
                            points_cost = int(cash_price * 100 / rate)
                            
                            # Effective Cost = Value of points burned
                            # If I burn 10k UR. Value is 10k * 1.7cpp = $170.
                            # But I got $150 of travel (10k * 1.5).
                            # So I lost value? compared to potential.
                            # The "Effective Cost" to the user is the Opportunity Cost of the points.
                            opp_cost = points_cost * (get_valuation('chase_ur') / 100.0)
                            
                            card = "Chase Sapphire Reserve" if card_inventory['has_chase_csr'] else "Chase Sapphire Preferred"

                            strategies.append({
                                'type': 'portal_pay_points',
                                'label': "Pay Pts (Chase Portal)",
                                'sub_label': f"Fixed {rate}\u00a2 Redemption",
                                'cost_display': f"{points_cost:,} pts",
                                'effective_cost': opp_cost,
                                'details_earned': f"Opp. Cost: ${opp_cost:.0f}",
                                'details_value': 0,
                                'icon': 'globe',
                                'card_name': card,
                                # Flag bad value if Opp Cost > Cash Price
                                'is_bad_value': opp_cost > cash_price
                            })
                            
                        # 2. Amex Pay with Points (1.0cpp on Portal as per user)
                        if card_inventory['has_amex_plat'] or card_inventory['has_amex_gold']:
                            rate = 1.0 
                            points_cost = int(cash_price * 100 / rate)
                            opp_cost = points_cost * (get_valuation('amex_mr') / 100.0)
                            
                            strategies.append({
                                'type': 'portal_pay_points',
                                'label': "Pay Pts (Amex Portal)",
                                'sub_label': f"Fixed {rate}\u00a2 Redemption",
                                'cost_display': f"{points_cost:,} pts",
                                'effective_cost': opp_cost,
                                'details_earned': f"Opp. Cost: ${opp_cost:.0f}",
                                'details_value': 0,
                                'icon': 'globe',
                                'card_name': "Amex Points",
                                'is_bad_value': opp_cost > cash_price * 1.2 # Only flag if significantly worse
                            })


                        # --- WINNER DETERMINATION ---
                        # Sort by Effective Cost (Ascending)
                        strategies.sort(key=lambda x: x['effective_cost'])
                        
                        # Assign Verdicts
                        # Assign Verdicts
                        best_strat = None
                        if strategies:
                            best_strat = strategies[0]
                            best_strat['is_winner'] = True
                            
                            # Determine savings vs cash baseline
                            cash_baseline = next((s for s in strategies if s['type'] == 'cash_direct'), None)
                            if cash_baseline:
                                savings = cash_baseline['effective_cost'] - best_strat['effective_cost']
                                if savings > 5:
                                    best_strat['savings'] = savings 
                                    best_strat['savings_text'] = f"Save ${int(savings)}"
                            
                            # Mark neutrals and avoids
                            for s in strategies:
                                eff_cost = s['effective_cost']
                                price = cash_price
                                
                                # Default Verdict
                                verdict = 'Neutral'
                                
                                # Check logic based on User Rules
                                # Good Value: Eff < Price (Savings > 0)
                                # Poor Value: Eff > Price * 1.01 (Cost > Price)
                                
                                if eff_cost < price * 0.99: 
                                     verdict = 'Good Value' 
                                elif eff_cost > price * 1.01: 
                                     verdict = 'Poor Value'
                                     s['is_bad_value'] = True
                                else:
                                     verdict = 'Neutral'
                                
                                s['verdict'] = verdict

                                if s == best_strat: continue
                                
                                # (Old logic removed - superseded by above User Rules)


                        hotels.append({
                            'name': hotel_name,
                            'location_text': f"{hotel_data.get('cityCode', location_query.upper())} • {brand_name or 'Independent'}", 
                            'price': cash_price,
                            'currency': currency,
                            'rating': rating, 
                            'brand': brand_name,
                            'image_url': 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&q=80&w=800', # Mock image
                            'strategies': strategies,
                            'winner': best_strat
                        })
                    except Exception as e:
                        print(f"Error parsing hotel: {e}")
                        continue
                        
    # 4. Render
    
    context = {
        'loyalty_points_header': [], # Re-add if needed or use existing logic
        'hotels': hotels,
        'default_check_in': default_check_in,
        'default_check_out': default_check_out,
    }
    
    # Re-inject the loyalty points header logic from previous file if needed?
    # User's request focused on the results card.
    
    # Let's add back valid Point Balances for header
    display_points = []
    for pid, bal in wallet_balances.items():
        if bal > 0:
            # Color logic
            color = 'gray'
            if 'chase' in pid: color = 'ur'
            elif 'amex' in pid: color = 'mr'
            elif 'hyatt' in pid: color = 'hyatt'
            
            display_points.append({
                'name': pid.replace('_', ' ').title(),
                'balance': bal,
                'color_class': color
            })
    context['loyalty_points'] = display_points
    
    return render(request, 'hotel_hunter/index.html', context)
