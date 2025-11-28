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
    
    # Get user's assigned personality if authenticated
    assigned_personality = None
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                assigned_personality = db.get_user_assigned_personality(uid)
            except Exception as e:
                print(f"Warning: Failed to fetch user personality: {e}")
    
    # Convert personalities to JSON for JavaScript
    personalities_json = json.dumps(personalities)
    
    return render(request, 'cards/personality_list.html', {
        'personalities': personalities,
        'personalities_json': personalities_json,
        'assigned_personality': assigned_personality
    })

def personality_detail(request, personality_id):
    try:
        personality = db.get_personality_by_slug(personality_id)
    except Exception:
        raise Http404("Personality not found")
        
    if not personality:
        raise Http404("Personality not found")
    
    # Fetch recommended cards
    recommended_cards = []
    try:
        for card_id in personality.get('recommended_cards', []):
            try:
                card = db.get_card_by_slug(card_id)
                if card:
                    recommended_cards.append(card)
            except Exception:
                continue
    except Exception:
        pass
            
    import sys
    sys.stderr.write(f"DEBUG: Fetched personality for {personality_id}: {personality}\n")
    return render(request, 'cards/personality_detail.html', {
        'personality': personality,
        'recommended_cards': recommended_cards
    })

def card_list(request):
    try:
        all_cards = db.get_cards()
    except Exception as e:
        print(f"Warning: Failed to fetch cards: {e}")
        all_cards = []

    # Get user's wallet cards if authenticated
    wallet_card_ids = set()
    if request.user.is_authenticated:
        uid = request.session.get('uid')
        if uid:
            try:
                user_cards = db.get_user_cards(uid)  # Get all user cards regardless of status
                wallet_card_ids = {card['card_id'] for card in user_cards}
            except Exception as e:
                print(f"Warning: Failed to fetch user cards: {e}")

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

    # Get filter options
    issuers = sorted(list(set(c.get('issuer') for c in all_cards if c.get('issuer'))))
    
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
    selected_issuers = request.GET.getlist('issuer')
    selected_categories = request.GET.getlist('category')
    min_fee_filter = request.GET.get('min_fee')
    max_fee_filter = request.GET.get('max_fee')
    search_query = request.GET.get('search', '').lower()
    wallet_filter = request.GET.get('wallet', '')  # 'in', 'out', or ''
    
    filtered_cards = all_cards
    
    if selected_issuers:
        filtered_cards = [c for c in filtered_cards if c.get('issuer') in selected_issuers]
        
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

    context = {
        'cards': filtered_cards,
        'issuers': issuers,
        'categories': all_categories,
        'selected_issuers': selected_issuers,
        'selected_categories': selected_categories,
        'search_query': search_query,
        'min_fee': min_fee,
        'max_fee': max_fee,
        'current_min_fee': min_fee_filter or min_fee,
        'current_max_fee': max_fee_filter or max_fee,
        'wallet_filter': wallet_filter
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
