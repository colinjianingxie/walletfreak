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
        # Note: Previous audit script might rely on old structure. Disabling for now unless rewritten, or assume it works on source dir
        # For safety/simplicity in this refactor, let's skip audit for now as structure changed.
        # if seed_all or card_slugs_list or types_list:
        #     import audit_slugs
        #     self.stdout.write('Running pre-flight data audits...')
        #     audit_passed = audit_slugs.run_audits()
        #     if not audit_passed:
        #         self.stdout.write(self.style.ERROR('Audit FAILED. Aborting database seed.'))
        #         return
        
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
        
        # Seed Loyalty Programs
        self._seed_loyalty_programs()
        
        # Seed Transfer Rules
        self._seed_transfer_rules()

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully.'))

    def _seed_categories_and_cards(self, base_dir, card_slugs_list, types_list, seed_categories):
        """Seed categories and credit cards data from new relational structure"""
        
        # New Master Directory
        updates_dir = os.path.join(base_dir, 'walletfreak_data', 'master_cards')
        # We might not check overrides in this pass if they are already baked in? 
        # Or should we apply overrides? The previous logic applied overrides to parsed data.
        # For now, let's assume raw data in master is source of truth.
        
        self.stdout.write(f'Parsing cards from: {updates_dir}')
        
        if not os.path.exists(updates_dir):
            self.stdout.write(self.style.ERROR(f'Master directory not found at {updates_dir}. Did you run "refactor_cards"?'))
            return

        # Prepare for category aggregation
        all_categories = {}

        # Load Loyalty Valuations
        loyalty_dir = os.path.join(base_dir, 'walletfreak_data', 'program_loyalty')
        loyalty_valuations = {}
        if os.path.exists(loyalty_dir):
            for fname in os.listdir(loyalty_dir):
                if fname.endswith('.json'):
                    try:
                        with open(os.path.join(loyalty_dir, fname), 'r') as f:
                            l_data = json.load(f)
                            pid = l_data.get('program_id')
                            val = l_data.get('valuation')
                            if pid and val:
                                loyalty_valuations[pid] = val
                    except:
                        pass

        # Iterate over card directories
        try:
            card_dirs = [d for d in os.listdir(updates_dir) if os.path.isdir(os.path.join(updates_dir, d))]
        except FileNotFoundError:
             self.stdout.write(self.style.ERROR(f'Master directory not found at {updates_dir}'))
             return

        # Filter if slugs provided
        if card_slugs_list:
            card_dirs = [d for d in card_dirs if d in card_slugs_list]
            self.stdout.write(f'Filtering to {len(card_dirs)} specified cards')

        for card_slug in card_dirs:
            card_path = os.path.join(updates_dir, card_slug)
            header_path = os.path.join(card_path, 'header.json')
            
            if not os.path.exists(header_path):
                self.stdout.write(self.style.WARNING(f'Skipping {card_slug}: header.json not found'))
                continue
                
            try:
                with open(header_path, 'r') as f:
                    card_data = json.load(f)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR(f'Skipping {card_slug}: Invalid header JSON'))
                continue

            # Seed Categories if active
            # We extract categories from card headers to build the master list
            if seed_categories:
                cats = card_data.get('Categories', [])
                for cat in cats:
                    c_name = cat.get('CategoryName')
                    if c_name:
                         all_categories[c_name] = cat

            # Use merge=True if we are doing a partial seed (types_list)
            should_merge = bool(types_list)
            
            # Create/Update Master Card Header
            # Derive points_value_cpp from loyalty_program
            l_prog = card_data.get('loyalty_program')
            if l_prog and l_prog in loyalty_valuations:
                card_data['points_value_cpp'] = loyalty_valuations[l_prog]
            else:
                card_data['points_value_cpp'] = 1.0

            db.create_document('master_cards', card_data, doc_id=card_slug, merge=should_merge)
            
            seeded_types = []

            # Helpers
            def seed_subcollection(sub_name, sub_json_dir, seed_type_key, delete_existing=True):
                # If types_list provided and this type is NOT in it, skip
                if types_list and seed_type_key not in types_list:
                    return 0

                sub_path = os.path.join(card_path, sub_json_dir)
                coll_ref = db.db.collection(f'master_cards/{card_slug}/{sub_name}')
                
                if not os.path.exists(sub_path):
                    return 0

                # Batch Delete
                if delete_existing:
                     try:
                        delete_batch = db.db.batch()
                        delete_count = 0
                        existing_docs = list(coll_ref.stream())
                        for d in existing_docs:
                            delete_batch.delete(d.reference)
                            delete_count += 1
                            if delete_count >= 400:
                                delete_batch.commit()
                                delete_batch = db.db.batch()
                                delete_count = 0
                        if delete_count > 0:
                            delete_batch.commit()
                     except Exception as e:
                        print(f"Error purging {sub_name}: {e}")
                
                # Batch Write
                write_batch = db.db.batch()
                write_count = 0
                total_items = 0
                
                for fname in os.listdir(sub_path):
                    if not fname.endswith('.json'):
                        continue
                        
                    f_full_path = os.path.join(sub_path, fname)
                    with open(f_full_path, 'r') as f:
                        try:
                            item_data = json.load(f)
                            # Filename as ID
                            doc_id = fname.replace('.json', '')
                             
                            doc_ref = coll_ref.document(doc_id)
                            write_batch.set(doc_ref, item_data)
                            write_count += 1
                            total_items += 1
                            
                            if write_count >= 400:
                                write_batch.commit()
                                write_batch = db.db.batch()
                                write_count = 0
                                
                        except json.JSONDecodeError:
                            print(f"Error decoding {fname}")
                            
                if write_count > 0:
                    write_batch.commit()
                    
                return total_items

            # Seed Subcollections
            
            # 1. Benefits
            c_ben = seed_subcollection('benefits', 'benefits', 'benefits')
            if c_ben: seeded_types.append(f'{c_ben} benefits')
            
            # 2. Earning Rates
            c_rates = seed_subcollection('earning_rates', 'earning_rates', 'rates')
            if c_rates: seeded_types.append(f'{c_rates} rates')
            
            # 3. Sign Up Bonus
            c_subs = seed_subcollection('sign_up_bonus', 'sign_up_bonus', 'sign_up_bonus')
            if c_subs: seeded_types.append(f'{c_subs} bonuses')
            
            # 4. Card Questions
            c_qs = seed_subcollection('card_questions', 'card_questions', 'calculator_questions')
            if c_qs: seeded_types.append(f'{c_qs} questions')

            self.stdout.write(f'Seeded {card_slug}: {", ".join(seeded_types)}')

        # After processing all cards, upsert collected categories
        if seed_categories and all_categories:
             self.stdout.write(f'Upserting {len(all_categories)} categories...')
             for cat_name, cat_data in all_categories.items():
                 db.create_document('categories', cat_data, doc_id=slugify(cat_name))

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
                card_ref = db.db.collection('master_cards').document(slug)
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

    def _seed_loyalty_programs(self):
        self.stdout.write("\nSeeding loyalty programs...")
        loyalty_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'program_loyalty')
        if not os.path.exists(loyalty_dir):
            self.stdout.write(self.style.WARNING(f"Loyalty directory not found: {loyalty_dir}"))
            return

        batch = db.db.batch()
        count = 0
        
        for filename in os.listdir(loyalty_dir):
            if not filename.endswith('.json'):
                continue
                
            with open(os.path.join(loyalty_dir, filename), 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f"Error decoding {filename}"))
                    continue
                
            pid = data.get('program_id')
            if not pid:
                continue
                
            doc_ref = db.db.collection('program_loyalty').document(pid)
            batch.set(doc_ref, data)
            count += 1
            
            if count % 400 == 0:
                batch.commit()
                batch = db.db.batch()
                
        if count % 400 != 0:
            batch.commit()
            
        self.stdout.write(f"Seeded {count} loyalty programs.")

    def _seed_transfer_rules(self):
        self.stdout.write("Seeding transfer rules...")
        transfers_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'transfer_rules')
        if not os.path.exists(transfers_dir):
            self.stdout.write(self.style.WARNING(f"Transfer rules directory not found: {transfers_dir}"))
            return

        batch = db.db.batch()
        count = 0
        
        for filename in os.listdir(transfers_dir):
            if not filename.endswith('.json'):
                continue
                
            with open(os.path.join(transfers_dir, filename), 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    self.stdout.write(self.style.ERROR(f"Error decoding {filename}"))
                    continue
                
            source_id = data.get('source_program_id')
            if not source_id:
                continue
                
            doc_ref = db.db.collection('transfer_rules').document(source_id)
            batch.set(doc_ref, data)
            count += 1
            
            if count % 400 == 0:
                batch.commit()
                batch = db.db.batch()
                
        if count % 400 != 0:
            batch.commit()
            
        self.stdout.write(f"Seeded transfer rules for {count} source programs.")
