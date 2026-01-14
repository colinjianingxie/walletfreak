from django.core.management.base import BaseCommand
from core.services import db

class Command(BaseCommand):
    help = 'Check user cards status'

    def handle(self, *args, **options):
        self.stdout.write("Checking users...")
        users_ref = db.db.collection('users')
        users = list(users_ref.stream())
        
        for user in users:
            uid = user.id
            email = user.get('email')
            self.stdout.write(f"\nUser: {email} ({uid})")
            
            cards_ref = users_ref.document(uid).collection('user_cards')
            cards = list(cards_ref.stream())
            self.stdout.write(f"  Total Cards (Raw): {len(cards)}")
            
            for card in cards:
                data = card.to_dict()
                status = data.get('status')
                self.stdout.write(f"    - ID: {card.id} | Status: '{status}'")

            # Check get_user_cards method output
            try:
                active_via_method = db.get_user_cards(uid, status='active')
                self.stdout.write(f"  > db.get_user_cards(status='active') count: {len(active_via_method)}")
            except Exception as e:
                self.stdout.write(f"  > Error calling get_user_cards: {e}")
