from django.shortcuts import render, Http404
from core.services import db

def personality_list(request):
    personalities = db.get_personalities()
    return render(request, 'cards/personality_list.html', {'personalities': personalities})

def personality_detail(request, personality_id):
    personality = db.get_personality_by_slug(personality_id)
    if not personality:
        raise Http404("Personality not found")
    
    # Fetch recommended cards
    recommended_cards = []
    for card_id in personality.get('recommended_cards', []):
        card = db.get_card_by_slug(card_id)
        if card:
            recommended_cards.append(card)
            
    return render(request, 'cards/personality_detail.html', {
        'personality': personality,
        'recommended_cards': recommended_cards
    })

def card_list(request):
    cards = db.get_cards()
    return render(request, 'cards/card_list.html', {'cards': cards})

import random

def card_detail(request, card_id):
    card = db.get_card_by_slug(card_id)
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
