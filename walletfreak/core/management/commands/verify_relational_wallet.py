
from django.core.management.base import BaseCommand
from core.services import db
import json

class Command(BaseCommand):
    help = 'Verifies wallet hydration logic'

    def handle(self, *args, **options):
        uid = 'test_user_verification'
        card_slug = 'american-express-gold-card'
        
        self.stdout.write(f"1. Adding {card_slug} to user {uid}...")
        success = db.add_card_to_user(uid, card_slug)
        
        if not success:
            self.stdout.write(self.style.ERROR("Failed to add card. Does master card exist?"))
            return

        self.stdout.write("Card added successfully.")
        
        self.stdout.write("2. Fetching user wallet...")
        wallet = db.get_user_cards(uid)
        
        found = False
        for card in wallet:
            if card.get('id') == card_slug:
                found = True
                self.stdout.write(self.style.SUCCESS(f"Found card: {card.get('name')}"))
                
                # Check hydration
                benefits = card.get('benefits', [])
                rates = card.get('earning_rates', [])
                
                self.stdout.write(f"Benefits count: {len(benefits)}")
                self.stdout.write(f"Rates count: {len(rates)}")
                
                if len(benefits) > 0:
                    self.stdout.write(f"Sample Benefit: {benefits[0].get('benefit_id')} ({benefits[0].get('value')})")
                else:
                    self.stdout.write(self.style.WARNING("No benefits found! Hydration might be failing."))
                    
                if len(rates) > 0:
                    self.stdout.write(f"Sample Rate: {rates[0].get('rate_id')} ({rates[0].get('multiplier')})")
                
                # Verify Reference
                ref = card.get('card_ref')
                self.stdout.write(f"Card Ref: {ref}")
                
        if not found:
            self.stdout.write(self.style.ERROR("Card not found in wallet!"))
            
        self.stdout.write("Verification complete.")
