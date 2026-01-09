from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import db
from django.utils.text import slugify
import os
import json

class Command(BaseCommand):
    help = 'Seeds the Firestore database with initial data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cards',
            type=str,
            help='Comma-separated list of card slugs to seed (e.g., chase-sapphire-preferred,amex-gold)',
        )
        parser.add_argument(
            '--types',
            type=str,
            help='Comma-separated list of data types to seed for cards: rates, benefits, calculator_questions, sign_up_bonus, freak_verdicts (or verdict)',
        )
        parser.add_argument(
            '--referrals',
            action='store_true',
            help='Seed referrals only',
        )
        parser.add_argument(
            '--personalities',
            action='store_true',
            help='Seed personalities only',
        )
        parser.add_argument(
            '--quiz-questions',
            action='store_true',
            help='Seed quiz questions only',
        )
        parser.add_argument(
            '--category-mapping',
            action='store_true',
            help='Seed category mapping only',
        )

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        
        # Parse options
        card_slugs = options.get('cards')
        types = options.get('types')
        seed_referrals = options.get('referrals')
        seed_personalities = options.get('personalities')
        seed_quiz_questions = options.get('quiz_questions')
        seed_category_mapping = options.get('category_mapping')
        
        # Convert comma-separated strings to lists
        card_slugs_list = [s.strip() for s in card_slugs.split(',') if s.strip()] if card_slugs else None
        types_list = [t.strip() for t in types.split(',') if t.strip()] if types else None
        
        # Normalize 'verdict' to 'freak_verdicts'
        if types_list:
             types_list = ['freak_verdicts' if t == 'verdict' else t for t in types_list]
        
        # Validate types
        valid_types = {'rates', 'benefits', 'calculator_questions', 'sign_up_bonus', 'freak_verdicts'}
        if types_list:
            invalid_types = set(types_list) - valid_types
            if invalid_types:
                self.stdout.write(self.style.ERROR(f'Invalid types: {", ".join(invalid_types)}'))
                self.stdout.write(f'Valid types: {", ".join(valid_types)}')
                return
        
        # Determine what to seed
        seed_all = not any([card_slugs, types, seed_referrals, seed_personalities, seed_quiz_questions, seed_category_mapping])
        
        # 0. Pre-flight Check: Audit Data Integrity (only if seeding cards)
        if seed_all or card_slugs_list or types_list:
            import audit_slugs
            self.stdout.write('Running pre-flight data audits...')
            audit_passed = audit_slugs.run_audits()
            if not audit_passed:
                self.stdout.write(self.style.ERROR('Audit FAILED. Aborting database seed.'))
                return
        
        # Get base directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # Seed categories and cards
        if seed_all or card_slugs_list or types_list or seed_category_mapping:
            self._seed_categories_and_cards(base_dir, card_slugs_list, types_list, seed_all or seed_category_mapping or bool(card_slugs_list))
        
        # Seed referrals
        if seed_all or seed_referrals or card_slugs_list:
            self._seed_referrals(base_dir, card_slugs_list)
        
        # Seed personalities
        if seed_all or seed_personalities:
            self._seed_personalities()
        
        # Seed quiz questions
        if seed_all or seed_quiz_questions:
            self._seed_quiz_questions()
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))

    def _seed_categories_and_cards(self, base_dir, card_slugs_list, types_list, seed_categories):
        """Seed categories and credit cards data"""
        from .parse_updates import generate_cards_from_files, apply_overrides
        
        updates_dir = os.path.join(base_dir, 'walletfreak_credit_cards')
        overrides_path = os.path.join(base_dir, 'credit_card_benefit_overrides.csv')
        
        self.stdout.write(f'Parsing cards from: {updates_dir}')
        
        # questions_data is now empty, questions are embedded in cards_data
        cards_data, categories_data, _ = generate_cards_from_files(updates_dir)
        
        # Apply Overrides
        self.stdout.write(f'Applying benefit overrides from: {overrides_path}')
        apply_overrides(cards_data, overrides_path)
        
        # Upsert Categories (if requested)
        if seed_categories:
            self.stdout.write(f'Upserting {len(categories_data)} categories...')
            for category in categories_data:
                cat_name = category.get('CategoryName')
                if cat_name:
                    db.create_document('categories', category, doc_id=slugify(cat_name))
                    self.stdout.write(f'  - Upserted Category: {cat_name}')
        
        # Filter cards if specific slugs requested
        if card_slugs_list:
            cards_data = [c for c in cards_data if c.get('slug') in card_slugs_list or slugify(c.get('name', '')) in card_slugs_list]
            self.stdout.write(f'Filtering to {len(cards_data)} specified cards')
        
        # Seed cards
        for card in cards_data:
            seeded_types = []
            
            if card.get('slug'):
                slug = card['slug']
            else:
                slug = slugify(card['name'])
            
            # Extract subcollection data before removing from main document
            benefits = card.get('benefits', [])
            rates = card.get('earning_rates', [])
            # bonus is now expected to be a list
            bonuses = card.get('sign_up_bonus', [])
            if isinstance(bonuses, dict): # Handling legacy/edge case if it returned a dict
                bonuses = [bonuses]
                
            questions = card.get('questions', [])
            
            # Remove redundant keys from main card document (now stored in subcollections)
            card.pop('benefits', None)
            card.pop('earning_rates', None)
            card.pop('sign_up_bonus', None)
            card.pop('questions', None)
            
            # Create main card document (without subcollection data) - always update main doc
            # Use merge=True if we are doing a partial seed (types_list) to avoid wiping other fields (e.g. referrals)
            should_merge = bool(types_list)
            db.create_document('credit_cards', card, doc_id=slug, merge=should_merge)
            
            # Freak Verdicts validation/logic
            if not types_list or 'freak_verdicts' in types_list:
                seeded_types.append('verdict')
            
            # Seed Subcollections based on types filter
            import hashlib
            import json

            def delete_subcollection(coll_path):
                try:
                    docs = list(db.db.collection(coll_path).stream())
                    if docs:
                        for doc in docs:
                            doc.reference.delete()
                except Exception as e:
                    pass
            
            # Benefits
            if not types_list or 'benefits' in types_list:
                b_path = f'credit_cards/{slug}/benefits'
                delete_subcollection(b_path)
                for i, b in enumerate(benefits):
                    b_id = b.get('benefit_id')
                    eff_date = b.get('effective_date')
                    if not b_id:
                         b_id = str(i)
                    
                    # Versioning: if effective_date exists, append it to make ID unique per version
                    doc_id = b_id
                    if eff_date:
                        doc_id = f"{b_id}_{eff_date}"

                    db.create_document(b_path, b, doc_id=doc_id)
                seeded_types.append(f'{len(benefits)} benefits')
            
            # Earning Rates
            if not types_list or 'rates' in types_list:
                r_path = f'credit_cards/{slug}/earning_rates'
                delete_subcollection(r_path)
                for i, r in enumerate(rates):
                    r_id = str(i)
                    db.create_document(r_path, r, doc_id=r_id)
                seeded_types.append(f'{len(rates)} rates')

            # Sign Up Bonus (List)
            if not types_list or 'sign_up_bonus' in types_list:
                s_path = f'credit_cards/{slug}/sign_up_bonus'
                # Do NOT delete subcollection for bonuses to preserve history of EffectiveDates
                # But actually, with the new system, we might be re-seeding the whole history from JSON?
                # If the JSON contains the full history, we technically *could* delete, but safe to just upsert.
                # If we want to clean up old ones that are NOT in the JSON, we should delete.
                # However, the previous logic explicitly said "Do NOT delete...". I'll trust that for now, 
                # or maybe the JSON *is* the source of truth now? 
                # Assuming JSON is source of truth, but let's stick to upserting for safety.
                
                count_bonus = 0
                for b in bonuses:
                    if b.get('value') or b.get('terms'):
                        bonus_id = b.get('effective_date')
                        if not bonus_id:
                            bonus_id = 'default'
                        db.create_document(s_path, b, doc_id=bonus_id)
                        count_bonus += 1
                seeded_types.append(f'{count_bonus} bonuses')
            
            # Card Questions (calculator_questions)
            if not types_list or 'calculator_questions' in types_list:
                if questions:
                    q_path = f"credit_cards/{slug}/card_questions"
                    delete_subcollection(q_path)
                    for i, cx in enumerate(questions):
                        doc_id = str(i)
                        db.create_document(q_path, cx, doc_id=doc_id)
                    seeded_types.append(f'{len(questions)} questions')
            
            self.stdout.write(f'Seeded card: {card["name"]} with {", ".join(seeded_types)}')

    def _seed_referrals(self, base_dir, card_slugs_list):
        """Seed referral links for cards"""
        import csv
        
        referrals_csv_path = os.path.join(base_dir, 'default_referrals.csv')
        self.stdout.write(f'Parsing referrals from: {referrals_csv_path}')
        
        referrals_map = {}  # slug -> list of links
        try:
            with open(referrals_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='|')
                for row in reader:
                    slug = row.get('slug-id', '').strip()
                    link = row.get('ReferralLink', '').strip()
                    if slug and link:
                        # Filter by card slugs if specified
                        if card_slugs_list and slug not in card_slugs_list:
                            continue
                        if slug not in referrals_map:
                            referrals_map[slug] = []
                        referrals_map[slug].append(link)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error parsing referrals: {e}'))
            return
        
        # Update cards with referral links
        for slug, links in referrals_map.items():
            try:
                card_ref = db.db.collection('credit_cards').document(slug)
                card_doc = card_ref.get()
                if card_doc.exists:
                    referral_links = [{'link': l, 'weight': 1} for l in links]
                    card_ref.update({'referral_links': referral_links})
                    self.stdout.write(f'  - Added {len(referral_links)} referral links to {slug}')
                else:
                    self.stdout.write(self.style.WARNING(f'  - Card {slug} not found, skipping referrals'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  - Error updating referrals for {slug}: {e}'))

    def _seed_personalities(self):
        """Seed personality data"""
        json_path = os.path.join(settings.BASE_DIR, 'default_personalities.json')
        try:
            with open(json_path, 'r') as f:
                personalities = json.load(f)
                
            for p in personalities:
                slug = p['slug']
                db.create_document('personalities', p, doc_id=slug)
                self.stdout.write(f'Seeded personality: {p["name"]}')
                
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Could not find {json_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {json_path}'))

    def _seed_quiz_questions(self):
        """Seed quiz questions data"""
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
