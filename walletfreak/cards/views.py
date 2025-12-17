from django.shortcuts import render, Http404
from core.services import db
import random

def personality_list(request):
    import json
    try:
        personalities = db.get_personalities()
    except Exception as e:
        print(f"Warning: Failed to fetch personalities: {e}")
        personalities = []
    
    # Fetch quiz questions from Firestore
    try:
        quiz_questions = db.get_quiz_questions()
    except Exception as e:
        print(f"Warning: Failed to fetch quiz questions: {e}")
        quiz_questions = []

    # Get user's assigned personality if authenticated
    assigned_personality = None
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                assigned_personality = db.get_user_assigned_personality(uid)
            except Exception as e:
                print(f"Warning: Failed to fetch user personality: {e}")
    


    # Convert personalities and cards to JSON for JavaScript
    personalities_json = json.dumps(personalities)
    questions_json = json.dumps(quiz_questions)
    
    return render(request, 'cards/personality_list.html', {
        'personalities': personalities,
        'personalities_json': personalities_json,
        'questions_json': questions_json,
        'assigned_personality': assigned_personality
    })

def personality_detail(request, personality_id):
    import json
    try:
        personality = db.get_personality_by_slug(personality_id)
    except Exception:
        raise Http404("Personality not found")
        
    if not personality:
        raise Http404("Personality not found")
    
    # Ensure slug is available for template
    personality['slug'] = personality['id']
    
    # Fetch recommended cards for the slots
    # We need to fetch full card details for each card in the slots
    
    # Create a map of all cards for easy lookup
    all_cards_map = {}
    try:
        all_cards = db.get_cards()
        for card in all_cards:
            all_cards_map[card['id']] = card
            all_cards_map[card.get('slug')] = card # Support slug lookup too
    except Exception:
        pass

    # Hydrate slots with card objects
    # --- OPTIMIZATION START ---
    # Only keep cards that are actually used in the slots
    slots = personality.get('slots', [])
    needed_card_slugs = set()
    for slot in slots:
        for card_slug in slot.get('cards', []):
            needed_card_slugs.add(card_slug)
            
    # Filter all_cards_map to only needed cards
    # Use slugs to look up IDs if needed, then rebuild map with IDs
    optimized_cards_map = {}
    
    # We need to find the card objects for the slugs
    for slug in needed_card_slugs:
        card = all_cards_map.get(slug)
        if card:
            optimized_cards_map[card['id']] = card
            
    # Also ensure we have the referenced cards by ID if they were standard IDs
    for card_id in needed_card_slugs:
        if card_id in all_cards_map:
             optimized_cards_map[all_cards_map[card_id]['id']] = all_cards_map[card_id]

    # Replace the main map with the optimized one for the loop below
    # We only want to process and send these cards
    all_cards_map = optimized_cards_map
    # --- OPTIMIZATION END ---

    # Hydrate slots with card objects (Restored)
    if 'slots' in personality:
        for slot in personality['slots']:
            hydrated_cards = []
            for card_slug in slot.get('cards', []):
                card = all_cards_map.get(card_slug)
                if card:
                    hydrated_cards.append(card)
            # Find cards by ID if slug didn't work (fallback)
            if not hydrated_cards:
                 for card_slug in slot.get('cards', []):
                    # Try to find by ID in our optimized map
                     for c in all_cards_map.values():
                         if str(c.get('id')) == str(card_slug):
                             hydrated_cards.append(c)
                             break
            slot['hydrated_cards'] = hydrated_cards

    # --- ENRICHMENT LOGIC (Copied from card_list) ---
    
    # Get user wallet and personality for matching
    wallet_card_ids = set()
    user_personality = None
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                user_cards = db.get_user_cards(uid)
                wallet_card_ids = {c['card_id'] for c in user_cards}
            except Exception:
                pass
            try:
                user_personality = db.get_user_assigned_personality(uid)
            except Exception:
                pass

    # Categories Mapping
    categories_map = {
        'Travel': ['travel', 'flight', 'hotel', 'mile', 'vacation', 'rental car', 'transit'],
        'Hotel': ['hotel', 'marriott', 'hilton', 'hyatt', 'ihg'],
        'Flights': ['flight', 'airline', 'delta', 'united', 'southwest', 'british airways', 'avios', 'aeroplan'],
        'Dining': ['dining', 'restaurant', 'food', 'eats'],
        'Groceries': ['groceries', 'supermarket', 'whole foods'],
        'Gas': ['gas'],
        'Student': ['student'],
        'Cash Back': ['cash back', 'cash rewards'],
        'Luxury': ['lounge', 'luxury', 'platinum', 'reserve']
    }

    # Enrich all cards in the map
    user_match_scores = {}
    
    for card in all_cards_map.values():
        # 1. Categories
        card_cats = set()
        text_to_check = (card.get('name', '') + ' ' + str(card.get('rewards_structure', '')) + ' ' + str(card.get('benefits', ''))).lower()
        for cat, keywords in categories_map.items():
            if any(k in text_to_check for k in keywords):
                card_cats.add(cat)
        if card.get('annual_fee', 0) == 0:
            card_cats.add('No Annual Fee')
        card['categories'] = sorted(list(card_cats))

        # 2. Wallet Status
        card['in_wallet'] = card.get('id') in wallet_card_ids

        # 3. Match Score
        if request.user.is_authenticated and user_personality:
            personality_categories = set(user_personality.get('focus_categories', []))
            score = 50
            card_categories = set(card.get('categories', []))
            if personality_categories:
                category_overlap = len(card_categories & personality_categories)
                score += min(30, category_overlap * 10)
            
            annual_fee = card.get('annual_fee', 0)
            if annual_fee == 0: score += 10
            elif annual_fee > 500: score -= 10
            
            if card.get('in_wallet', False): score -= 30
            
            score = max(0, min(100, score))
            card['match_score'] = score
            user_match_scores[card['id']] = score

    # Store match scores in session or context if needed, but mainly we updated the card objects themselves 
    # which will be serialized into cards_json.
    
    cards_json = json.dumps(all_cards_map, default=str)
    
    return render(request, 'cards/personality_detail.html', {
        'personality': personality,
        'cards_json': cards_json,
        'wallet_card_ids': list(wallet_card_ids),
        'user_match_scores': user_match_scores
    })


def card_list(request):
    import json
    from django.core.paginator import Paginator
    try:
        all_cards = db.get_cards()
    except Exception as e:
        print(f"Warning: Failed to fetch cards: {e}")
        all_cards = []

    # Get user's wallet cards and personality if authenticated
    wallet_card_ids = set()
    user_personality = None
    user_match_scores = {}
    
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                user_cards = db.get_user_cards(uid)
                wallet_card_ids = {card['card_id'] for card in user_cards}
            except Exception as e:
                print(f"Warning: Failed to fetch user cards: {e}")
            
            try:
                user_personality = db.get_user_assigned_personality(uid)
            except Exception as e:
                print(f"Warning: Failed to fetch user personality: {e}")

    # Derive categories for each card
    categories_map = {
        'Travel': ['travel', 'flight', 'hotel', 'mile', 'vacation', 'rental car', 'transit'],
        'Hotel': ['hotel', 'marriott', 'hilton', 'hyatt', 'ihg'],
        'Flights': ['flight', 'airline', 'delta', 'united', 'southwest', 'british airways', 'avios', 'aeroplan'],
        'Dining': ['dining', 'restaurant', 'food', 'eats'],
        'Groceries': ['groceries', 'supermarket', 'whole foods'],
        'Gas': ['gas'],
        'Student': ['student'],
        'Cash Back': ['cash back', 'cash rewards'],
        'Luxury': ['lounge', 'luxury', 'platinum', 'reserve']
    }

    for card in all_cards:
        card_cats = set()
        # Check description and benefits
        text_to_check = (card.get('name', '') + ' ' + str(card.get('rewards_structure', '')) + ' ' + str(card.get('benefits', ''))).lower()
        
        for cat, keywords in categories_map.items():
            if any(k in text_to_check for k in keywords):
                card_cats.add(cat)
        
        # Special cases based on fee
        if card.get('annual_fee', 0) == 0:
            card_cats.add('No Annual Fee')
            
        card['categories'] = sorted(list(card_cats))
        
        # Mark if card is in wallet
        card['in_wallet'] = card.get('id') in wallet_card_ids

        # --- Earning Display Logic (for List View) ---
        earning = card.get('earning_rates') or card.get('rewards_structure') or []
        
        # If no earning rates found, extract from benefits with benefit_type "Multiplier" or "Cashback"
        if not earning:
             benefits = card.get('benefits', [])
             earning = [
                 {
                     'category': b.get('short_description') or b.get('name') or b.get('title') or b.get('description', 'Purchase'),
                     'rate': b.get('numeric_value') or b.get('value') or b.get('multiplier', 0),
                     'currency': 'cash' if b.get('benefit_type') == 'Cashback' else (b.get('currency', 'points'))
                 }
                 for b in benefits 
                 if b.get('benefit_type') in ['Multiplier', 'Cashback']
             ]

        # Format for display (Top 3 rates)
        # We prefer specific categories over generic ones for the summary
        display_items = []
        if earning:
             # Sort by rate descending
             try:
                 sorted_earning = sorted(earning, key=lambda x: float(x.get('rate') or x.get('multiplier') or x.get('value') or 0), reverse=True)
             except Exception:
                 sorted_earning = earning

             count = 0
             for item in sorted_earning:
                 if count >= 3: break
                 
                 cat = item.get('category') or item.get('cat') or item.get('description') or 'Purchase'
                 rate = item.get('rate') or item.get('multiplier') or item.get('value') or 0
                 currency = item.get('currency', 'points')
                 
                 # Skip if rate is 0 or 1 (usually base rate) unless it's unique
                 if float(rate) <= 1 and len(sorted_earning) > 1:
                     continue
                     
                 # Format rate
                 try:
                     val = float(rate)
                     is_int = val.is_integer()
                     
                     if str(currency).lower() in ['cash', 'cashback'] or '%' in str(rate):
                        if '%' in str(rate):
                            # It's already a string like "3%", strip it to check value or just leave it
                            # But if it came in as 3.0, we might want to clean it up.
                            # Assuming rate might be "3.0" or 3.0
                            clean_val = int(val) if is_int else val
                            rate_str = f"{clean_val}%"
                        else:
                            clean_val = int(val) if is_int else val
                            rate_str = f"{clean_val}%"
                     else:
                        clean_val = int(val) if is_int else val
                        rate_str = f"{clean_val}x"
                 except Exception:
                     # Fallback for non-numeric rates
                     rate_str = str(rate)
                 
                 # Simplified category name
                 cat = cat.replace('Purchases', '').replace('Select', '').strip()
                 
                 display_items.append({'rate': rate_str, 'category': cat})
                 count += 1
        
        card['earning_display'] = display_items

    # Calculate match percentages for authenticated users
    if request.user.is_authenticated and user_personality:
        # Get personality preferences
        personality_categories = set()
        if 'focus_categories' in user_personality:
            personality_categories = set(user_personality['focus_categories'])
        
        for card in all_cards:
            score = 50  # Base score
            
            # Category alignment (up to +30 points)
            card_categories = set(card.get('categories', []))
            if personality_categories:
                category_overlap = len(card_categories & personality_categories)
                score += min(30, category_overlap * 10)
            
            # Annual fee consideration (up to +20 or -20 points)
            annual_fee = card.get('annual_fee', 0)
            if annual_fee == 0:
                score += 10  # Bonus for no fee
            elif annual_fee > 500:
                score -= 10  # Penalty for high fee
            
            # Already in wallet penalty (-30 points)
            if card.get('in_wallet', False):
                score -= 30
            
            # Ensure score is between 0 and 100
            score = max(0, min(100, score))
            
            user_match_scores[card['id']] = score
    
    # Get filter options - ensure we only get valid, non-empty issuers
    issuers = sorted(list(set(
        c.get('issuer').strip()
        for c in all_cards
        if c.get('issuer') and c.get('issuer').strip()
    )))
    
    # Collect all actual categories from cards
    actual_categories = set()
    for card in all_cards:
        actual_categories.update(card['categories'])
    
    all_categories = sorted(list(actual_categories))
    
    # Fee range
    fees = [c.get('annual_fee', 0) for c in all_cards]
    min_fee = min(fees) if fees else 0
    max_fee = max(fees) if fees else 1000

    # Apply filters (Server-side fallback)
    selected_issuers = [i.strip() for i in request.GET.getlist('issuer')]
    selected_categories = request.GET.getlist('category')
    min_fee_filter = request.GET.get('min_fee')
    max_fee_filter = request.GET.get('max_fee')
    search_query = request.GET.get('search', '').lower()
    wallet_filter = request.GET.get('wallet', '')  # 'in', 'out', or ''
    sort_by = request.GET.get('sort', 'match')  # Default sort by match
    
    filtered_cards = all_cards
    
    if selected_issuers:
        filtered_cards = [c for c in filtered_cards if c.get('issuer', '').strip() in selected_issuers]
        
    if selected_categories:
        filtered_cards = [c for c in filtered_cards if any(cat in c.get('categories', []) for cat in selected_categories)]

    if min_fee_filter:
        try:
            filtered_cards = [c for c in filtered_cards if c.get('annual_fee', 0) >= int(min_fee_filter)]
        except ValueError:
            pass
            
    if max_fee_filter:
        try:
            filtered_cards = [c for c in filtered_cards if c.get('annual_fee', 0) <= int(max_fee_filter)]
        except ValueError:
            pass
        
    if search_query:
        # Handle aliases
        if search_query == 'amex':
            search_query = 'american express'
            
        filtered_cards = [c for c in filtered_cards if search_query in c.get('name', '').lower() or search_query in c.get('issuer', '').lower()]
    
    # Apply wallet filter
    if wallet_filter == 'in':
        filtered_cards = [c for c in filtered_cards if c.get('in_wallet', False)]
    elif wallet_filter == 'out':
        filtered_cards = [c for c in filtered_cards if not c.get('in_wallet', False)]
    
    # Apply sorting
    if sort_by == 'match' and user_match_scores:
        filtered_cards = sorted(filtered_cards, key=lambda c: user_match_scores.get(c['id'], 0), reverse=True)
    elif sort_by == 'name':
        filtered_cards = sorted(filtered_cards, key=lambda c: c.get('name', '').lower())
    elif sort_by == 'fee_low':
        filtered_cards = sorted(filtered_cards, key=lambda c: c.get('annual_fee', 0))
    elif sort_by == 'fee_high':
        filtered_cards = sorted(filtered_cards, key=lambda c: c.get('annual_fee', 0), reverse=True)

    # Pagination
    paginator = Paginator(filtered_cards, 200)  # Show all cards (client-side filtering)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Create cards dictionary for modal
    all_cards_dict = {}
    for card in all_cards:
        all_cards_dict[card['id']] = card
    
    cards_json = json.dumps(all_cards_dict, default=str)

    context = {
        'cards': page_obj,
        'page_obj': page_obj,
        'total_cards': len(filtered_cards),
        'cards_json': cards_json,
        'wallet_card_ids': list(wallet_card_ids),  # Pass to JavaScript for button state
        'issuers': issuers,
        'categories': all_categories,
        'selected_issuers': selected_issuers,
        'selected_categories': selected_categories,
        'search_query': search_query,
        'min_fee': min_fee,
        'max_fee': max_fee,
        'current_min_fee': min_fee_filter or min_fee,
        'current_max_fee': max_fee_filter or max_fee,
        'wallet_filter': wallet_filter,
        'user_match_scores': user_match_scores,
        'sort_by': sort_by
    }
    return render(request, 'cards/card_list.html', context)


def card_detail(request, card_id):
    try:
        card = db.get_card_by_slug(card_id)
    except Exception:
        raise Http404("Card not found")
        
    if not card:
        raise Http404("Card not found")
    
    # Referral Rotation Logic
    active_link = None
    if card.get('referral_links'):
        links = card['referral_links']
        # Simple weighted choice
        # links structure: [{'link': 'url', 'weight': 1}, ...]
        try:
            population = [l['link'] for l in links]
            weights = [l.get('weight', 1) for l in links]
            active_link = random.choices(population, weights=weights, k=1)[0]
        except Exception:
            pass
            
    return render(request, 'cards/card_detail.html', {'card': card, 'active_link': active_link})
