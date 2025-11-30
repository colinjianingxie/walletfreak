import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import db

class Command(BaseCommand):
    help = 'Loads sign-up bonuses from CSV to Firestore'

    def handle(self, *args, **options):
        csv_path = os.path.join(settings.BASE_DIR, 'default_signup_2025_11_30.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV file not found at {csv_path}'))
            return

        self.stdout.write(f'Loading sign-up bonuses from {csv_path}...')
        
        # Fetch all cards first to create a lookup map
        all_cards = db.get_cards()
        card_map = {c['name'].lower().strip(): c['id'] for c in all_cards}
        
        updated_count = 0
        not_found_count = 0

        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                card_name = row['CardName'].strip()
                bonus_value = row['SignUpBonusValue']
                currency = row['Currency']
                terms = row['Terms']
                
                # Try to find the card
                card_id = card_map.get(card_name.lower())
                
                # fuzzy match if exact match fails (simple check for now)
                if not card_id:
                    # Try removing registered trademark symbols
                    clean_name = card_name.replace('®', '').replace('℠', '').strip().lower()
                    for db_name, db_id in card_map.items():
                        clean_db_name = db_name.replace('®', '').replace('℠', '').strip().lower()
                        if clean_name == clean_db_name:
                            card_id = db_id
                            break
                
                if card_id:
                    try:
                        # Convert value to int
                        try:
                            value = int(bonus_value)
                        except ValueError:
                            value = 0
                            
                        update_data = {
                            'sign_up_bonus': {
                                'value': value,
                                'currency': currency,
                                'terms': terms
                            }
                        }
                        
                        db.update_document('credit_cards', card_id, update_data)
                        self.stdout.write(self.style.SUCCESS(f'Updated {card_name}'))
                        updated_count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error updating {card_name}: {e}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Card not found: {card_name}'))
                    not_found_count += 1

        self.stdout.write(self.style.SUCCESS(f'Finished! Updated: {updated_count}, Not Found: {not_found_count}'))
