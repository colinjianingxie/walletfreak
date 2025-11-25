from django.shortcuts import render, Http404
from core.services import db
import random

def personality_list(request):
    try:
        personalities = db.get_personalities()
    except Exception as e:
        print(f"Warning: Failed to fetch personalities: {e}")
        personalities = []
    return render(request, 'cards/personality_list.html', {'personalities': personalities})

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
            
    return render(request, 'cards/personality_detail.html', {
        'personality': personality,
        'recommended_cards': recommended_cards
    })

def card_list(request):
    try:
        cards = db.get_cards()
    except Exception as e:
        print(f"Warning: Failed to fetch cards: {e}")
        cards = []
    return render(request, 'cards/card_list.html', {'cards': cards})

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
