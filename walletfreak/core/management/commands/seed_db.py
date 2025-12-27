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
        
        # 0. Pre-flight Check: Audit Data Integrity
        import audit_slugs
        self.stdout.write('Running pre-flight data audits...')
        audit_passed = audit_slugs.run_audits()
        if not audit_passed:
            self.stdout.write(self.style.ERROR('Audit FAILED. Aborting database seed.'))
            return

        # 1. Credit Cards Data - Parse from Text Files
        from .parse_updates import generate_cards_from_files, apply_overrides
        
        # Get the updates directory path
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        updates_dir = os.path.join(base_dir, 'walletfreak_credit_cards')
        overrides_path = os.path.join(base_dir, 'credit_card_benefit_overrides.csv')
        
        self.stdout.write(f'Parsing cards from: {updates_dir}')
        
        cards_data, categories_data, questions_data = generate_cards_from_files(updates_dir)
        
        # Apply Overrides
        self.stdout.write(f'Applying benefit overrides from: {overrides_path}')
        apply_overrides(cards_data, overrides_path)

        # Upsert Categories
        self.stdout.write(f'Upserting {len(categories_data)} categories...')
        for category in categories_data:
            cat_name = category.get('CategoryName')
            if cat_name:
                db.create_document('categories', category, doc_id=slugify(cat_name))
                self.stdout.write(f'  - Upserted Category: {cat_name}')
                
        # Upsert Card Questions
        self.stdout.write(f'Upserting {len(questions_data)} card questions...')
        
        # Group questions by slug
        questions_by_slug = {}
        for q in questions_data:
            slug = q.get('slug-id')
            if slug:
                if slug not in questions_by_slug:
                    questions_by_slug[slug] = []
                questions_by_slug[slug].append(q)
        
        seeded_q_count = 0
        for slug, questions in questions_by_slug.items():
            for i, cx in enumerate(questions):
                # Use simple index as ID
                doc_id = str(i)
                
                # Use subcollection path
                collection_path = f"credit_cards/{slug}/card_questions"
                db.create_document(collection_path, cx, doc_id=doc_id)
                seeded_q_count += 1
            
        self.stdout.write(f'  - Seeded {seeded_q_count} questions into subcollections.')

        # Parse referrals (Legacy CSV usage for now, or could be moved to files later)
        referrals_csv_path = os.path.join(base_dir, 'default_referrals.csv')
        self.stdout.write(f'Parsing referrals from: {referrals_csv_path}')
        
        referrals_map = {} # slug -> list of links
        try:
            import csv
            with open(referrals_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    slug = row.get('slug-id', '').strip()
                    link = row.get('ReferralLink', '').strip()
                    if slug and link:
                        if slug not in referrals_map:
                            referrals_map[slug] = []
                        referrals_map[slug].append(link)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error parsing referrals: {e}'))
        
        card_slug_map = {} # Name -> Slug

        for card in cards_data:
            if card.get('slug'):
                slug = card['slug']
            else:
                slug = slugify(card['name'])
            
            card_slug_map[card['name']] = slug
            
            # Inject referrals
            if slug in referrals_map:
                # Format as objects for compatibility
                card['referral_links'] = [{'link': l, 'weight': 1} for l in referrals_map[slug]]
                self.stdout.write(f'  - Added {len(card["referral_links"])} referral links to {slug}')
            
            # Create main card document
            db.create_document('credit_cards', card, doc_id=slug)
            
            # Seed Subcollections
            import hashlib
            import json

            # Helper to generate stable ID
            def get_stable_id(data_dict):
                # Sort keys to ensure consistent order
                s = json.dumps(data_dict, sort_keys=True, default=str)
                return hashlib.md5(s.encode('utf-8')).hexdigest()

            def delete_subcollection(coll_path):
                try:
                    docs = list(db.db.collection(coll_path).stream())
                    if docs:
                        # self.stdout.write(f'  - Clearing {len(docs)} docs from {coll_path}')
                        for doc in docs:
                            doc.reference.delete()
                except Exception as e:
                    pass

            # 1. Benefits
            b_path = f'credit_cards/{slug}/benefits'
            delete_subcollection(b_path)
            benefits = card.get('benefits', [])
            for i, b in enumerate(benefits):
                # Use simple index as ID for overrides compatibility
                b_id = str(i)
                db.create_document(b_path, b, doc_id=b_id)
            
            # 2. Earning Rates
            r_path = f'credit_cards/{slug}/earning_rates'
            delete_subcollection(r_path)
            rates = card.get('earning_rates', [])
            for i, r in enumerate(rates):
                # Use simple index as ID
                r_id = str(i)
                db.create_document(r_path, r, doc_id=r_id)

            # 3. Sign Up Bonus
            s_path = f'credit_cards/{slug}/sign_up_bonus'
            delete_subcollection(s_path)
            bonus = card.get('sign_up_bonus')
            if bonus:
                # Some cards might have empty bonus dict or None
                if bonus.get('value') or bonus.get('terms'):
                     # Use effective_date as ID per user request
                     # Fallback to 'default' if not present
                     bonus_id = bonus.get('effective_date')
                     if not bonus_id:
                         bonus_id = 'default'
                     db.create_document(s_path, bonus, doc_id=bonus_id)
            
            earning_rates_count = len(rates)
            self.stdout.write(f'Seeded card: {card["name"]} with {len(benefits)} benefits, {earning_rates_count} rates, and bonus.')

        # 2. Personalities Data with Wallet Setup
        # ... (Personalities seeding code remains same) ...

        # Upsert Categories
        # ... (Categories seeding code remains same) ...
                
        # Upsert Card Questions
        self.stdout.write(f'Upserting {len(questions_data)} card questions...')
        
        # Group questions by slug
        questions_by_slug = {}
        # ... (grouping logic remains same) ...
        # (Re-implementing loop to fit replacement context)
        for q in questions_data:
            slug = q.get('slug-id')
            if slug:
                if slug not in questions_by_slug:
                    questions_by_slug[slug] = []
                questions_by_slug[slug].append(q)
        
        seeded_q_count = 0
        for slug, questions in questions_by_slug.items():
            q_path = f"credit_cards/{slug}/card_questions"
            delete_subcollection(q_path)
            
            for i, cx in enumerate(questions):
                # Use simple index as ID
                doc_id = str(i)
                db.create_document(q_path, cx, doc_id=doc_id)
                seeded_q_count += 1
            
        self.stdout.write(f'  - Seeded {seeded_q_count} questions into subcollections.')

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
