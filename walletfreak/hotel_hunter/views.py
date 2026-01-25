from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from core.services import db
from core.services.amadeus_service import AmadeusService
from django.conf import settings
from django.core.cache import cache
import csv
import json
import os
import math
from datetime import datetime, timedelta
from xai_sdk import Client
from xai_sdk.chat import user
from xai_sdk.tools import web_search
from .prompts import STRATEGY_ANALYSIS_PROMPT_TEMPLATE
import threading
from django.shortcuts import redirect
from django.urls import reverse

DATA_DIR = '/Users/xie/Desktop/projects/walletfreak/walletfreak/walletfreak_data'

# --- CONSTANTS & CONFIG ---
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
    'accor_all': 2.0, 
    'best_western_rewards': 0.6,
    'choice_privileges': 0.6,
    'sonesta_travel_pass': 0.8,
}


def load_hotel_mapping():
    mapping = {}
    path = os.path.join(DATA_DIR, 'hotel_code_mapping.csv')
    if os.path.exists(path):
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Chain Code']:
                    mapping[row['Chain Code']] = {
                        'chain_name': row['Chain Name'],
                        'program_id': row['Program ID'],
                        'program_name': row['Loyalty Program']
                    }
    return mapping


def get_brand_class(program_id):
    """Maps loyalty program to CSS class name for color bars."""
    if not program_id: return 'independent'
    if 'hyatt' in program_id: return 'hyatt'
    if 'hilton' in program_id: return 'hilton'
    if 'marriott' in program_id: return 'marriott'
    if 'ihg' in program_id: return 'ihg'
    return 'independent'

# --- MAIN VIEWS ---

@login_required
def index(request):
    """
    Initial Search View.
    Fetches raw hotel data from Amadeus and renders the list.
    """
    hotels = []
    location_query = request.GET.get('location')
    
    # Dates
    today = datetime.now().date()
    default_check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    default_check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')
    
    context = {
        'default_check_in': default_check_in,
        'default_check_out': default_check_out,
        'hotels': []
    }

    if location_query:
        if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
            service = AmadeusService()
            
            check_in_raw = request.GET.get('checkInDate') or default_check_in
            check_out_raw = request.GET.get('checkOutDate') or default_check_out
            
            # Basic validation
            if check_in_raw == check_out_raw: 
                # Add a day if equal
                try: 
                    check_out_raw = (datetime.strptime(check_in_raw, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                except: pass

            search_params = {
                'check_in': check_in_raw,
                'check_out': check_out_raw,
                'adults': request.GET.get('guests', '1')
            }
            try:
                # Generate Cache Key
                cache_key = f"hotel_search_{location_query}_{search_params['check_in']}_{search_params['check_out']}_{search_params['adults']}"
                cached_data = cache.get(cache_key)

                if cached_data:
                    hotels = cached_data
                else:
                    # We fetch offers
                    api_results = service.search_hotel_offers_by_city(location_query, **search_params)
                    
                    # Load Mapping
                    hotel_mapping = load_hotel_mapping()
                    
                    # Mock Ratings Map (Since Sentiment API is flaky/quota limited)
                    # In real prod we'd fetch or cache this
                    
                    for offer in api_results:
                        try:
                            hotel_data = offer.get('hotel', {})
                            offers_data = offer.get('offers', [])
                            if not offers_data: continue
                            
                            price_obj = offers_data[0].get('price', {})
                            cash_price = float(price_obj.get('total', 0))
                            currency = price_obj.get('currency', 'USD')
                            
                            chain_code = hotel_data.get('chainCode', '')
                            mapped = hotel_mapping.get(chain_code, {})
                            
                            hotel_name = hotel_data.get('name', 'Unknown Hotel').title()
                            brand_name = mapped.get('chain_name', chain_code)
                            program_id = mapped.get('program_id', '')
                            program_name = mapped.get('program_name', '')
                            
                            # Mock Rating for demo stability
                            rating = 4.5 
                            
                            # ID for HTML
                            hid = hotel_data.get('hotelId', '0')
                            
                            # Construct Data Object to pass to "Compare"
                            # We need to serialize this to JSON
                            hotel_json_obj = {
                                'hotel_id': hid,
                                'name': hotel_name,
                                'location_code': hotel_data.get('cityCode', location_query.upper()),
                                'brand_name': brand_name,
                                'program_id': program_id,
                                'program_name': program_name,
                                'price': cash_price,
                                'currency': currency,
                                'rating': rating,
                                'chain_code': chain_code
                            }

                            hotels.append({
                                'id_safe': hid,
                                'name': hotel_name,
                                'location_text': f"{hotel_data.get('cityCode', 'ETH')} • {brand_name or 'Independent'}",
                                'price': cash_price,
                                'currency': currency,
                                'rating': rating,
                                'brand': brand_name,
                                'brand_class': get_brand_class(program_id),
                                'json_data': json.dumps(hotel_json_obj)
                            })

                        except Exception as e:
                            print(f"Parse Error: {e}")
                            continue
                    
                    # Cache the results for 1 hour if we got data
                    if hotels:
                        cache.set(cache_key, hotels, 3600)
                        
            except Exception as e:
                print(f"Amadeus Error: {e}")
                
        context['hotels'] = hotels

    return render(request, 'hotel_hunter/index.html', context)


@login_required
def compare(request):
    """
    Analyzes selected hotels using AI (Simulated) to determine the best booking strategy.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    uid = request.session.get('uid')
    if not uid:
        # Fallback for dev if no session
        # return JsonResponse({'error': 'User not authenticated'}, status=401)
        pass 
    
    # 1. Get User Context (Cards, Points)
    # Fetch full card details to get earning rates
    user_cards = db.get_user_cards(uid, status='active', hydrate=True) if uid else []
    user_balances_raw = db.get_user_loyalty_balances(uid) if uid else []
    
    # Format Balances
    wallet_balances = {b['program_id']: int(b.get('balance', 0)) for b in user_balances_raw}
    
    # Transfer Rules
    raw_rules = db.get_all_transfer_rules()
    transfer_rules = {}
    for r in raw_rules:
        sid = r.get('source_program_id')
        if sid:
            # Minify transfer rules for token efficiency
            partners = []
            for p in r.get('transfer_partners', []):
                partners.append({
                    'dest': p.get('destination_program_id'),
                    'ratio': p.get('ratio'),
                    'time': p.get('transfer_time', 'Instant')
                })
            transfer_rules[sid] = partners

    # 2. Get Selected Hotels
    selected_hotels_raw = request.POST.getlist('selected_hotels')
    selected_hotels = []
    if selected_hotels_raw:
        for json_str in selected_hotels_raw:
            try:
                # We fix potential single-quote JSON or similar issues if present
                # But the template uses json.dumps so it should be valid double-quoted JSON.
                hotel_dict = json.loads(json_str)
                # Remove price and rating to force AI to fetch real-time
                hotel_dict.pop('price', None)
                hotel_dict.pop('rating', None)
                selected_hotels.append(hotel_dict)
            except: 
                # Log error or handle malformed JSON
                pass
    
    # 3. Preparation for Prompt
    # We minify user cards to only essential fields for the AI
    user_cards_minified = []
    for c in user_cards:
        # Extract Earning Rates
        rates = []
        for r in c.get('earning_rates', []):
            rates.append(f"{r.get('multiplier')}x on {', '.join(r.get('category', []))}")
        
        user_cards_minified.append({
            'name': c.get('name'),
            'slug_id': c.get('slug-id'),
            'bank': c.get('issuer'),
            'earning_rates': rates,
            'is_travel_portal_eligible': 'Safire' in c.get('name') or 'Plat' in c.get('name') or 'Venture' in c.get('name') # heuristic
        })

    # 4. Construct the Prompt
    # Get parameters
    check_in = request.POST.get('checkInDate', '2025-06-01')
    check_out = request.POST.get('checkOutDate', '2025-06-03')
    guests = request.POST.get('guests', '1')

    prompt = STRATEGY_ANALYSIS_PROMPT_TEMPLATE.format(
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        user_cards_json=json.dumps(user_cards_minified, indent=2),
        loyalty_balances_json=json.dumps(wallet_balances, indent=2),
        transfer_rules_json=json.dumps(transfer_rules, indent=2),
        selected_hotels_json=json.dumps(selected_hotels, indent=2),
        valuations_json=json.dumps(VALUATIONS, indent=2)
    )
    
    # Debug: Print prompt to console to show we constructed it
    # print("\n" + "="*50)
    # print(" GENERATED AI PROMPT ")
    # print("="*50)
    # print(prompt)
    # print("="*50 + "\n")

    # 5. ASYNC PROCESSING START
    # Instead of blocking, we create a record with 'processing' status and launch a background thread
    
    if uid:
        try:
            strategy_record = {
                'location_text': request.POST.get('location'),
                'check_in': check_in,
                'check_out': check_out,
                'guests': guests,
                'hotel_count': len(selected_hotels),
                'analysis_results': [], # Empty initially
                'status': 'processing',
                'prompt_used': prompt  # Save the prompt for download
            }
            # Save "Processing" state
            strategy_id = db.save_hotel_strategy(uid, strategy_record)
            
            # Define Background Worker
            def run_analysis_in_background(prompt_text, user_id, strat_id):
                # Call AI
                print(f"Starting background analysis for strategy {strat_id}...")
                results = call_grok_analysis(prompt_text)
                
                if not results:
                    print(f"Analysis failed for {strat_id}")
                    # Update to failed state
                    try:
                        strategies_ref = db.db.collection('users').document(user_id).collection('hotel_strategies').document(strat_id)
                        strategies_ref.update({
                            'status': 'failed',
                            'analysis_results': []
                        })
                    except Exception as e:
                        print(f"Failed to update strategy to failed state: {e}")
                    return

                # Update Firestore with results
                # Note: our db helper might not have deep update support easily exposed, 
                # but let's assume we can access the underlying collection update method or use `create_document` with merge=True?
                # Actually `save_hotel_strategy` uses `.add()`. We need an UPDATE method.
                # Let's use the `db.db` raw access for specific subcollection update if needed, 
                # or add a helper. 
                # HACK: using raw db client access since we are inside the view which imports db service.
                # But safer to add a helper method to `users.py` if possible. 
                # For now let's modify `users.py` or use raw firestore client if `db.db` is public (it is).
                
                try:
                    strategies_ref = db.db.collection('users').document(user_id).collection('hotel_strategies').document(strat_id)
                    strategies_ref.update({
                        'status': 'ready',
                        'analysis_results': results,
                        'hotel_count': len(results) # Update count based on successful analysis
                    })
                    print(f"Updated strategy {strat_id} with results.")
                except Exception as e:
                    print(f"Failed to update strategy result: {e}")

            # Launch Thread
            t = threading.Thread(target=run_analysis_in_background, args=(prompt, uid, strategy_id))
            t.daemon = True
            t.start()
            
            # Redirect to History
            return redirect('hotel_hunter:history')
            
        except Exception as e:
            print(f"Error initiating strategy: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    # Fallback if no User (cannot save history) - run synchronously (demo mode)
    analysis_results = call_grok_analysis(prompt)
    context = {
        'analysis': {'analysis_results': analysis_results or []},
        'search_params': {
            'location': request.POST.get('location'),
            'checkInDate': request.POST.get('checkInDate'),
            'checkOutDate': request.POST.get('checkOutDate'),
            'guests': request.POST.get('guests', '1')
        }
    }
    return render(request, 'hotel_hunter/strategy_report.html', context)

@login_required
def history(request):
    """
    Displays the user's strategy history.
    """
    uid = request.session.get('uid')
    strategies = []
    if uid:
        strategies = db.get_user_hotel_strategies(uid)
        # Parse date strings to datetime objects for template formatting
        for s in strategies:
            try:
                if s.get('check_in'):
                    s['check_in'] = datetime.strptime(s['check_in'], '%Y-%m-%d')
                if s.get('check_out'):
                    s['check_out'] = datetime.strptime(s['check_out'], '%Y-%m-%d')
            except:
                pass
    
    return render(request, 'hotel_hunter/history.html', {'strategies': strategies})

@login_required
def strategy_report(request, strategy_id):
    """
    Displays a specific saved strategy report.
    """
    uid = request.session.get('uid')
    
    strategy = None
    if uid:
        strategy = db.get_hotel_strategy(uid, strategy_id)
        
    if not strategy:
        # Handle not found or unauthorized
        return render(request, 'hotel_hunter/index.html', {'error': 'Report not found'})
        
    # Check if user is super staff
    is_super_staff = False
    if uid:
        user_profile = db.get_user_profile(uid)
        if user_profile:
            is_super_staff = user_profile.get('is_super_staff', False)

    context = {
        'analysis': {'analysis_results': strategy.get('analysis_results', [])},
        'search_params': {
            'location': strategy.get('location_text'),
            'checkInDate': strategy.get('check_in'),
            'checkOutDate': strategy.get('check_out'),
            'guests': strategy.get('guests', '1')
        },
        'strategy_id': strategy_id,
        'is_history_view': True,
        'prompt_used': strategy.get('prompt_used', ''),
        'is_super_staff': is_super_staff
    }
    
    return render(request, 'hotel_hunter/strategy_report.html', context)



def call_grok_analysis(prompt):
    """
    Calls Grok API with web search enabled to analyze hotel strategies.
    Uses xai_sdk for Agent Tools API support.
    """
    api_key = os.environ.get('GROK_API_KEY')
    if not api_key:
        print("GROK_API_KEY not found.")
        return None

    try:
        client = Client(api_key=api_key)
        
        # Initialize chat with web_search tool
        chat = client.chat.create(
            model="grok-4-1-fast", 
            tools=[web_search()], 
        )
        
        chat.append(user(prompt))
        
        # Get the full response synchronously
        response = chat.sample()
        
        full_response = response.content
        
        # Clean Markdown
        if "```json" in full_response:
            full_response = full_response.split("```json")[1].split("```")[0].strip()
        elif "```" in full_response:
            full_response = full_response.split("```")[1].split("```")[0].strip()
            
        return json.loads(full_response).get('analysis_results', [])

    except Exception as e:
        print(f"Grok SDK Error: {e}")
        return None

@login_required
def check_strategy_status(request):
    """
    API call to check status of specific strategies.
    Expects GET param 'ids' (comma separated).
    """
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    ids = request.GET.get('ids', '').split(',')
    ids = [i.strip() for i in ids if i.strip()]
    
    if not ids:
        return JsonResponse({'statuses': {}})
        
    results = {}
    for sid in ids:
        strat = db.get_hotel_strategy(uid, sid)
        if strat:
            results[sid] = strat.get('status', 'unknown')
    
    return JsonResponse({'statuses': results})

@login_required
def download_prompt(request, strategy_id):
    """
    Download the prompt used to generate a strategy report as a text file.
    """
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    strategy = db.get_hotel_strategy(uid, strategy_id)
    if not strategy:
        return HttpResponse("Strategy not found", status=404)
    
    prompt_text = strategy.get('prompt_used', 'Prompt not available for this report.')
    
    response = HttpResponse(prompt_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="strategy_{strategy_id}_prompt.txt"'
    return response
