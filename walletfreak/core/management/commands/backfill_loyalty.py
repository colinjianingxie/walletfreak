from django.core.management.base import BaseCommand
from core.services import db

class Command(BaseCommand):
    help = 'Backfill loyalty programs for all users based on their active cards'

    def handle(self, *args, **options):
        self.stdout.write('Starting loyalty program backfill...')
        
        users_ref = db.db.collection('users')
        users = users_ref.stream()
        
        count_users = 0
        count_programs = 0
        
        for user_doc in users:
            uid = user_doc.id
            self.stdout.write(f'Processing user {uid}...')
            count_users += 1
            
            # Get active cards
            user_cards = db.get_user_cards(uid, status='active', hydrate=True)
            
            for card in user_cards:
                loyalty_program = card.get('loyalty_program')
                
                if loyalty_program:
                    # Check if user already has this program
                    balance_ref = db.db.collection('users').document(uid).collection('loyalty_balances').document(loyalty_program)
                    if not balance_ref.get().exists:
                        # Add it with 0 balance
                        db.update_user_loyalty_balance(uid, loyalty_program, 0)
                        self.stdout.write(f'  - Added {loyalty_program} (from {card.get("name")})')
                        count_programs += 1
                        
        self.stdout.write(self.style.SUCCESS(f'Backfill complete. Processed {count_users} users, added {count_programs} programs.'))
