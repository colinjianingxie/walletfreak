from django.core.management.base import BaseCommand
import os
from core.management.commands.parse_benefits_csv import generate_cards_from_csv

class Command(BaseCommand):
    help = 'Debug CSV parsing'

    def handle(self, *args, **options):
        base_dir = '/Users/xie/Desktop/projects/walletfreak/walletfreak'
        csv_path = os.path.join(base_dir, 'default_card_benefits.csv')
        signup_csv_path = os.path.join(base_dir, 'default_signup.csv')
        rates_csv_path = os.path.join(base_dir, 'default_rates.csv')
        master_csv_path = os.path.join(base_dir, 'default_credit_cards.csv')
        
        self.stdout.write("Running generate_cards_from_csv...")
        cards = generate_cards_from_csv(csv_path, signup_csv_path, rates_csv_path, master_csv_path)
        
        found = False
        for i, card in enumerate(cards):
            slug = card.get('slug', '')
            name = card.get('name', '')
            if slug == 'Percent' or name == 'Percent':
                self.stdout.write(self.style.ERROR(f"FOUND 'Percent' CARD at index {i}!"))
                self.stdout.write(f"Slug: {slug}")
                self.stdout.write(f"Name: {name}")
                self.stdout.write(f"Benefits count: {len(card.get('benefits', []))}")
                # Print first benefit to see where it came from
                if card.get('benefits'):
                    b = card['benefits'][0]
                    self.stdout.write(f"First Benefit: {b}")
                found = True
        
        if not found:
            self.stdout.write(self.style.SUCCESS("Percent card NOT found in generate_cards_from_csv output."))
