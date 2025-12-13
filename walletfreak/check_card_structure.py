import os
import django
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import db

def check_structure():
    cards = db.get_cards()
    if not cards:
        print("No cards found")
        return

    card = cards[0]
    print(f"Card: {card.get('name')}")
    print(f"Keys: {list(card.keys())}")
    
    benefits = card.get('benefits')
    print(f"Benefits type: {type(benefits)}")
    if isinstance(benefits, list):
         print(f"Benefits count: {len(benefits)}")
         if len(benefits) > 0:
             print(f"First benefit keys: {list(benefits[0].keys())}")
             print(f"First benefit sample: {benefits[0]}")
    else:
         print(f"Benefits value: {benefits}")
         
    credits = card.get('credits')
    print(f"Credits: {credits}")

check_structure()
