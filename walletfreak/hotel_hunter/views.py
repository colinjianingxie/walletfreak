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

DATA_DIR = '/Users/xie/Desktop/projects/walletfreak/walletfreak/walletfreak_data'

def load_hotel_mapping():
    mapping = {}
    path = os.path.join(DATA_DIR, 'hotel_code_mapping.csv')
    if os.path.exists(path):
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Chain Code'] and row['Program ID']:
                    # Map Code -> {Name, Program ID}
                    mapping[row['Chain Code']] = {
                        'chain_name': row['Chain Name'],
                        'program_id': row['Program ID']
                    }
    return mapping

def load_transfer_rules():
    rules = {} # source_id -> [partners]
    path = os.path.join(DATA_DIR, 'transfer_rules', '*.json')
    for filename in glob.glob(path):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                source_id = data.get('source_program_id')
                if source_id:
                    rules[source_id] = data.get('transfer_partners', [])
        except:
            pass
    return rules

def estimate_points_cost(price, program_id):
    # Heuristic Valuations (CPP)
    valuations = {
        'world_of_hyatt': 0.018,
        'hilton_honors': 0.006,
        'marriott_bonvoy': 0.008,
        'ihg_one_rewards': 0.007,
        'wyndham_rewards': 0.01,
        'accor_all': 0.02, # Fixed revenue based approx
        'best_western_rewards': 0.006,
        'choice_privileges': 0.006,
        'sonesta_travel_pass': 0.008,
        'i_prefer': 0.008,
        'gha_discovery': 0.05 # GHA is weird ($ based), assume high efficiency if D$ used
    }
    
    val = valuations.get(program_id, 0.01) # Default 1cpp
    points_needed = int(price / val)
    
    # Round to nearest 1000 usually
    return round(points_needed / 1000) * 1000, val

@login_required
def index(request):
    uid = request.session.get('uid')
    
    # Fetch Data
    all_programs = db.get_all_loyalty_programs()
    user_balances = db.get_user_loyalty_balances(uid) if uid else []
    
    # User Wallet Map: program_id -> balance
    wallet = {b['program_id']: b.get('balance', 0) for b in user_balances}
    
    # Filter and Format (Loyalty Points Header)
    display_points = []
    relevant_types = ['hotel', 'bank'] 
    
    for p in all_programs:
        if p.get('type') in relevant_types:
            pid = p['id']
            if pid in wallet:
                balance = wallet[pid]
                
                # Simple color mapping
                color_class = 'gray' 
                if 'ur' in pid.lower() or 'chase' in pid.lower(): color_class = 'ur'
                elif 'mr' in pid.lower() or 'amex' in pid.lower(): color_class = 'mr'
                elif 'bilt' in pid.lower(): color_class = 'bilt'
                elif 'hyatt' in pid.lower(): color_class = 'hyatt' 
                elif 'marriott' in pid.lower(): color_class = 'marriott'
                elif 'hilton' in pid.lower(): color_class = 'hilton'
                
                display_points.append({
                    'name': p.get('short_name') or p.get('program_name'),
                    'balance': balance,
                    'type': p.get('type'),
                    'id': pid,
                    'color_class': color_class
                })
    
    # Load Intelligence Data
    hotel_mapping = load_hotel_mapping()
    transfer_rules = load_transfer_rules()
    
    # Search Logic
    hotels = []
    location_query = request.GET.get('location')
    
    if location_query:
        if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
            service = AmadeusService()
            
            # Extract search parameters
            dates_str = request.GET.get('dates', '')
            check_in = request.GET.get('checkInDate')
            check_out = request.GET.get('checkOutDate')
            
            if not check_in and ' - ' in dates_str:
                parts = dates_str.split(' - ')
                if len(parts) == 2:
                    check_in = parts[0]
                    check_out = parts[1]

            search_params = {
                'radius': request.GET.get('radius'),
                'radiusUnit': request.GET.get('radiusUnit'),
                'chainCodes': request.GET.get('chainCodes'),
                'amenities': request.GET.get('amenities'),
                'ratings': request.GET.get('ratings'),
                'hotelSource': request.GET.get('hotelSource'),
                'maxPrice': request.GET.get('maxPrice'),
                'check_in': check_in,
                'check_out': check_out,
                'adults': request.GET.get('guests')
            }
            
            search_params = {k: v for k, v in search_params.items() if v}

            api_results = service.search_hotel_offers_by_city(location_query, **search_params)
            
            if api_results:
                # Fetch Sentiments
                sentiment_map = {}
                try:
                    hotel_ids = list(set([o.get('hotel', {}).get('hotelId') for o in api_results if o.get('hotel', {}).get('hotelId')]))
                    sentiments = service.get_hotel_sentiments(hotel_ids)
                    sentiment_map = {s['hotelId']: s.get('overallRating') for s in sentiments}
                except Exception as e:
                    print(f"DEBUG: Error fetching sentiments: {e}")

                # Processing Loop
                for offer in api_results:
                    try:
                        hotel_data = offer.get('hotel', {})
                        offers_data = offer.get('offers', [])
                        hotel_id = hotel_data.get('hotelId')
                        
                        price_val = 0
                        currency = "$"
                        
                        if offers_data:
                            price_info = offers_data[0].get('price', {})
                            price_val = float(price_info.get('total', 0))
                            currency = price_info.get('currency', '$')

                        chain_code = hotel_data.get('chainCode', '')
                        
                        # Intelligence: Identify Brand & Program
                        mapped_info = hotel_mapping.get(chain_code, {})
                        brand_name = mapped_info.get('chain_name', chain_code)
                        program_id = mapped_info.get('program_id')
                        
                        # Sentiment
                        rating = sentiment_map.get(hotel_id)

                        # --- BUILD OPTIONS ---
                        options = []
                        
                        # 1. Transfer Partners
                        if program_id:
                            points_needed, valuation_cpp = estimate_points_cost(price_val, program_id)
                            
                            # Find all transferable sources
                            for source_id, partners in transfer_rules.items():
                                for partner in partners:
                                    if partner['destination_program_id'] == program_id:
                                        # Match found! Source -> Program
                                        ratio = partner['ratio']
                                        transfer_needed = math.ceil(points_needed / ratio)
                                        
                                        # Check user balance in source
                                        user_bal = wallet.get(source_id, 0)
                                        needed_delta = max(0, transfer_needed - user_bal)
                                        
                                        cpp_value = (price_val * 100) / transfer_needed
                                        
                                        # Title formatting
                                        source_name_map = {'chase_ur': 'Chase UR', 'amex_mr': 'Amex MR', 'bilt_rewards': 'Bilt', 'citi_ty': 'Citi ThankYou', 'cap1_miles': 'Capital One'}
                                        src_display = source_name_map.get(source_id, source_id)

                                        # Only show if reasonable or user has points
                                        if user_bal > 0 or cpp_value > 1.2:
                                            options.append({
                                                'type': 'transfer',
                                                'title': f"Transfer from {src_display}",
                                                'badge': 'RECOMMENDED' if cpp_value > 1.8 else 'GOOD VALUE',
                                                'badge_class': 'bg-green-100 text-green-700 border-green-200' if cpp_value > 1.8 else 'bg-blue-100 text-blue-700 border-blue-200',
                                                'description': f"Transfer ~{transfer_needed:,} pts from {src_display} ({ratio}:1).",
                                                'data_points': f"{points_needed:,} pts",
                                                'data_sub': f"{cpp_value:.2f} cpp",
                                                'btn_text': 'Transfer & Book',
                                                'btn_class': 'bg-green-600 hover:bg-green-700 text-white',
                                                'current_balance': user_bal,
                                                'needed': transfer_needed
                                            })
                        
                        # 2. Perks / Benefits (Benefits Check)
                        # Implied logic: Check if user holds cards like Platinum (amex_mr) or Sapphire (chase_ur)
                        # For now, simplify: if user has 'amex_mr' -> FHR. if 'chase_ur' -> The Edit.
                        if 'amex_mr' in wallet and wallet['amex_mr'] > 0:
                            options.append({
                                'type': 'shield',
                                'title': 'Amex Fine Hotels & Resorts',
                                'badge': 'PERKS',
                                'badge_class': 'bg-purple-100 text-purple-700 border-purple-200',
                                'description': 'Get $100 Experience Credit, Daily Breakfast for 2, 4pm Checkout.',
                                'data_points': f"${int(price_val)}",
                                'data_sub': '~$250 in Perks',
                                'btn_text': 'Book via Amex',
                                'btn_class': 'bg-purple-600 hover:bg-purple-700 text-white'
                            })
                            
                        # 3. Cash / Portal
                        options.append({
                            'type': 'credit-card',
                            'title': 'Pay Cash (Maximize Points)',
                            'badge': None,
                            'description': 'Book via portal to earn 5x-10x points.',
                            'data_points': f"${int(price_val)}",
                            'data_sub': f"+{int(price_val*5):,} pts",
                            'btn_text': 'Book Cash',
                            'btn_class': 'bg-slate-900 hover:bg-slate-800 text-white'
                        })

                        # Sort options by perceived value (Transfer > Perks > Cash)
                        # Already roughly sorted by insertion order

                        hotels.append({
                            'name': hotel_data.get('name', 'Unknown Hotel').title(),
                            'location_text': f"{hotel_data.get('cityCode', location_query.upper())}", 
                            'price': price_val,
                            'currency': currency,
                            'rating': rating, 
                            'brand': brand_name,
                            'options': options
                        })
                    except Exception as e:
                        print(f"DEBUG: Error parsing offer: {e}")
                        continue
    
    context = {
        'loyalty_points': display_points,
        'hotels': hotels,
        'active_cards_count': len(user_balances)
    }
    return render(request, 'hotel_hunter/index.html', context)
