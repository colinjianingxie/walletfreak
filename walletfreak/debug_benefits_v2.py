
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services import db

def check_card_benefits(slug):
    print(f"Checking benefits for card: {slug}")
    card = db.get_card_by_slug(slug)
    
    if not card:
        print("Card not found!")
        # Try to find slug from name
        all_cards = db.get_cards()
        for c in all_cards:
            if 'Citi Strata' in c.get('name', ''):
                print(f"Found potential match: {c['name']} ({c['slug']})")
                check_card_benefits(c['slug'])
                return
        return

    benefits = card.get('benefits', [])
    print(f"Found {len(benefits)} benefits.")
    
    for i, b in enumerate(benefits):
        print(f"\nBenefit {i+1}:")
        print(f"Keys: {list(b.keys())}")
        print(f"BenefitDescriptionShort: {b.get('BenefitDescriptionShort')}")
        print(f"BenefitDescription: {b.get('BenefitDescription')}")
        print(f"title: {b.get('title')}")
        print(f"Full dict: {b}")

if __name__ == "__main__":
    check_card_benefits('citi-strata-elite-card')
