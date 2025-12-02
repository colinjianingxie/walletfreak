from django.core.management.base import BaseCommand
from core.services import db
from django.utils.text import slugify
from core.quiz_data import PERSONALITIES, QUIZ_QUESTIONS
import os

class Command(BaseCommand):
    help = 'Seeds the Firestore database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # 1. Credit Cards Data - Parse from CSV
        from .parse_benefits_csv import generate_cards_from_csv
        
        # Get the CSV paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        csv_path = os.path.join(base_dir, 'default_cards_2025_11_27.csv')
        signup_csv_path = os.path.join(base_dir, 'default_signup_2025_11_30.csv')
        rates_csv_path = os.path.join(base_dir, 'default_rates_2025_11_30.csv')
        
        self.stdout.write(f'Parsing cards from: {csv_path}')
        self.stdout.write(f'Parsing signup bonuses from: {signup_csv_path}')
        self.stdout.write(f'Parsing earning rates from: {rates_csv_path}')
        
        cards_data = generate_cards_from_csv(csv_path, signup_csv_path, rates_csv_path)
        
        card_slug_map = {} # Name -> Slug

        for card in cards_data:
            slug = slugify(card['name'])
            card_slug_map[card['name']] = slug
            
            db.create_document('credit_cards', card, doc_id=slug)
            earning_rates_count = len(card.get('earning_rates', []))
            self.stdout.write(f'Seeded card: {card["name"]} with {len(card["benefits"])} benefits and {earning_rates_count} earning rates')

        # 2. Personalities Data with Wallet Setup
        for p in PERSONALITIES:
            slug = p['slug']
            
            # Map wallet setup card slugs (they should already be slugified in quiz_data.py)
            wallet_setup = p.get('wallet_setup', [])
            
            p_data = {
                'name': p['name'],
                'tagline': p.get('tagline', 'The Archetype'),
                'description': p['description'],
                'wallet_setup': wallet_setup,
                'avatar_url': ''
            }
            db.create_document('personalities', p_data, doc_id=slug)
            self.stdout.write(f'Seeded personality: {p["name"]} with {len(wallet_setup)} wallet categories')
        
        # 3. Quiz Questions Data
        for question in QUIZ_QUESTIONS:
            question_id = f'stage_{question["stage"]}'
            db.create_document('quiz_questions', question, doc_id=question_id)
            self.stdout.write(f'Seeded quiz question: Stage {question["stage"]}')

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
