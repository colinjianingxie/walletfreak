from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import db
from django.utils.text import slugify
import os
import json

class Command(BaseCommand):
    help = 'Seeds the Firestore database with initial data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # 1. Credit Cards Data - Parse from CSV
        from .parse_benefits_csv import generate_cards_from_csv
        
        # Get the CSV paths
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        csv_path = os.path.join(base_dir, 'default_card_benefits.csv')
        signup_csv_path = os.path.join(base_dir, 'default_signup.csv')
        rates_csv_path = os.path.join(base_dir, 'default_rates.csv')
        # points_csv_path variable is effectively the master_csv_path
        master_csv_path = os.path.join(base_dir, 'default_credit_cards.csv')
        
        self.stdout.write(f'Parsing cards from: {csv_path}')
        self.stdout.write(f'Parsing signup bonuses from: {signup_csv_path}')
        self.stdout.write(f'Parsing earning rates from: {rates_csv_path}')
        self.stdout.write(f'Parsing master cards data from: {master_csv_path}')
        
        cards_data = generate_cards_from_csv(csv_path, signup_csv_path, rates_csv_path, master_csv_path=master_csv_path)
        
        card_slug_map = {} # Name -> Slug

        for card in cards_data:
            if card.get('slug'):
                slug = card['slug']
            else:
                slug = slugify(card['name'])
            
            card_slug_map[card['name']] = slug
            
            db.create_document('credit_cards', card, doc_id=slug)
            earning_rates_count = len(card.get('earning_rates', []))
            self.stdout.write(f'Seeded card: {card["name"]} with {len(card["benefits"])} benefits and {earning_rates_count} earning rates')

        # 2. Personalities Data with Wallet Setup
        json_path = os.path.join(settings.BASE_DIR, 'default_personalities.json')
        try:
            with open(json_path, 'r') as f:
                personalities = json.load(f)
                
            for p in personalities:
                slug = p['slug']
                
                # Map wallet setup card slugs (they should already be slugified in JSON)
                # Note: The JSON structure might be slightly different from what was in quiz_data.py
                # In JSON, 'slots' contains 'cards' which are lists of slugs.
                # We might need to adapt this if 'wallet_setup' was expected.
                # Looking at default_personalities.json, it has 'slots'.
                # But the original code used p.get('wallet_setup', []).
                # Let's check if we need to transform 'slots' to 'wallet_setup' or if 'slots' IS the new structure.
                # The JSON has 'slots'. The original code used 'wallet_setup'.
                # If the model expects 'wallet_setup', we might need to change it or the model.
                # However, looking at the previous seed_personalities.py, it just did .set(p).
                # So if seed_personalities.py works with 'slots', then seed_db.py should probably also just save 'p' or adapt.
                # The original seed_db.py constructed p_data.
                # Let's try to just save the personality object as is, similar to seed_personalities.py, 
                # OR adapt it if seed_db.py logic was specific.
                # Original seed_db.py:
                # p_data = { 'name': ..., 'tagline': ..., 'description': ..., 'wallet_setup': ..., 'avatar_url': ... }
                # The JSON has 'slots'.
                # Let's assume we should save the whole object 'p' as seed_personalities.py does.
                
                db.create_document('personalities', p, doc_id=slug)
                self.stdout.write(f'Seeded personality: {p["name"]}')
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find {json_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {json_path}'))
        
        # 3. Quiz Questions Data
        quiz_json_path = os.path.join(settings.BASE_DIR, 'default_quiz_questions.json')
        try:
            with open(quiz_json_path, 'r') as f:
                quiz_questions = json.load(f)
                
            for question in quiz_questions:
                question_id = f'stage_{question["stage"]}'
                db.create_document('quiz_questions', question, doc_id=question_id)
                self.stdout.write(f'Seeded quiz question: Stage {question["stage"]}')
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find {quiz_json_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {quiz_json_path}'))

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
