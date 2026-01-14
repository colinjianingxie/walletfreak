import os
import json
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Ingests credit card data from a JSON file and updates the master record'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=False,
            help='Path to the JSON file (defaults to ../card_updates.json)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without writing to files'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if options['path']:
            file_path = options['path']
        else:
            file_path = os.path.join(settings.BASE_DIR, '..', 'card_updates.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        try:
            with open(file_path, 'r') as f:
                new_data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in file: {e}"))
            return

        slug = new_data.get('slug-id')
        if not slug:
             self.stdout.write(self.style.ERROR("Input JSON must contain 'slug-id' field"))
             return

        self.master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        if not os.path.exists(self.master_dir):
            if dry_run:
                self.stdout.write(self.style.WARNING(f"Would create master directory: {self.master_dir}"))
            else:
                os.makedirs(self.master_dir)

        self.stdout.write(f"Processing {slug} from {file_path}...")
        
        try:
            self.dehydrate_and_save(slug, new_data, dry_run=dry_run)
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"Dry run complete for {slug}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Successfully updated/created {slug}"))
                self.stdout.write(self.style.WARNING(f"\nNow run: python manage.py seed_db --cards {slug}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {slug}: {e}"))
            import traceback
            traceback.print_exc()

    def dehydrate_and_save(self, slug, new_data, dry_run=False):
        """
        Splits the monolithic JSON into relational files with versioning.
        Updates everything found in the new_data.
        """
        card_dir = os.path.join(self.master_dir, slug)
        if not os.path.exists(card_dir):
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"[NEW CARD] Would create directory: {card_dir}"))
            else:
                os.makedirs(card_dir)

        # 1. Header
        # Fields to keep in header
        header_keys = [
            "slug-id", "name", "issuer", "image_url", "annual_fee",
            "application_link", "min_credit_score", "max_credit_score",
            "is_524", "freak_verdict", "points_value_cpp", "show_in_calculators",
            "referral_links"
        ]
        
        # Load existing header to preserve active_indices and un-updated fields
        header_path = os.path.join(card_dir, 'header.json')
        if os.path.exists(header_path):
            with open(header_path, 'r') as f:
                header_doc = json.load(f)
        else:
            header_doc = {"slug-id": slug, "active_indices": {"benefits": [], "earning_rates": [], "sign_up_bonus": []}}
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"[HEADER] Would create new header.json"))

        # Update permissible header fields
        for key in header_keys:
            if key in new_data:
                old_val = header_doc.get(key)
                new_val = new_data[key]
                if old_val != new_val:
                    header_doc[key] = new_val
                    if dry_run:
                        self.stdout.write(self.style.WARNING(f"[HEADER] {key}: {old_val} -> {new_val}"))

        # 2. Versioning Helper
        today_str = datetime.date.today().isoformat()
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        def process_sub_collection(key, directory, id_field, normalized_id_prefix):
            """
            key: key in new_data (e.g., 'benefits')
            directory: subfolder name (e.g., 'benefits')
            id_field: user-facing ID field in item (e.g., 'benefit_id' or 'rate_id')
            normalized_id_prefix: prefix for file generation if ID missing
            """
            new_items = new_data.get(key)
            # If key is missing from input, do not update this section (SKIP)
            if new_items is None: 
                return
            
            target_dir = os.path.join(card_dir, directory)
            if not os.path.exists(target_dir):
                if dry_run:
                     self.stdout.write(self.style.WARNING(f"[{directory}] Would create directory"))
                else:
                    os.makedirs(target_dir)

            current_indices = header_doc['active_indices'].get(directory, [])
            new_active_indices = []

            # Load current items for comparison
            current_items_map = {} # versioned_id -> data
            base_id_map = {} # base_id (e.g. 'dining') -> currently_active_versioned_id (e.g. 'dining-v1')

            for vid in current_indices:
                path = os.path.join(target_dir, f"{vid}.json")
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        item = json.load(f)
                        current_items_map[vid] = item
                        # Extract base ID
                        base_id = item.get(id_field)
                        if base_id:
                            base_id_map[base_id] = vid

            for index, item in enumerate(new_items):
                # Ensure item has a base ID
                base_id = item.get(id_field)
                if not base_id:
                    # Generator fallback if missing
                    base_id = f"{normalized_id_prefix}-{index}"
                    item[id_field] = base_id

                # Check if we have an active version of this base_id
                active_vid = base_id_map.get(base_id)
                
                should_create_new = True
                final_vid = None
                
                if active_vid:
                    # Compare content (excluding metadata fields)
                    old_item = current_items_map[active_vid]
                    
                    # Prepare for comparison (ignoring version, dates)
                    ignore_keys = {'version', 'valid_from', 'valid_until', 'is_active'}
                    
                    # Deep compare relevant fields
                    old_clean = {k: v for k, v in old_item.items() if k not in ignore_keys}
                    new_clean = {k: v for k, v in item.items() if k not in ignore_keys}
                    
                    if old_clean == new_clean:
                        # NO CHANGE
                        should_create_new = False
                        final_vid = active_vid
                    else:
                        # CHANGED - Determine new version
                        # Parse old version number
                        try:
                            # Split by last hyphen
                            parts = active_vid.rsplit('-v', 1)
                            if len(parts) == 2:
                                current_v_num = int(parts[1])
                                new_v_num = current_v_num + 1
                            else:
                                new_v_num = 2
                        except:
                            new_v_num = 2
                        
                        final_vid = f"{base_id}-v{new_v_num}"
                        
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f"[{directory}] UPDATE {base_id}: {active_vid} -> {final_vid}"))
                            # Show specific diffs
                            for k, v in new_clean.items():
                                if old_clean.get(k) != v:
                                    self.stdout.write(f"    {k}: {old_clean.get(k)} -> {v}")

                        # Deprecate old file
                        # If created today, valid_until today (overwrite/correction logic)
                        if old_item.get('valid_from') == today_str:
                             old_item['valid_until'] = today_str
                        else:
                             old_item['valid_until'] = yesterday_str
                        
                        old_item['is_active'] = False
                        if not dry_run:
                            with open(os.path.join(target_dir, f"{active_vid}.json"), 'w') as f:
                                json.dump(old_item, f, indent=4)
                            
                else:
                    # NEW ITEM
                    final_vid = f"{base_id}-v1"
                    if dry_run:
                        self.stdout.write(self.style.SUCCESS(f"[{directory}] CREATE {final_vid}"))

                if should_create_new:

                    item['valid_from'] = today_str
                    item['valid_until'] = None
                    item['is_active'] = True
                    
                    if not dry_run:
                        with open(os.path.join(target_dir, f"{final_vid}.json"), 'w') as f:
                            json.dump(item, f, indent=4)
                
                new_active_indices.append(final_vid)

            # Detect deletions (items in current_indices not in new_active_indices)
            new_base_ids = set()
            for item in new_items:
                if item.get(id_field): new_base_ids.add(item.get(id_field))
            
            for vid in current_indices:
                old_item = current_items_map.get(vid)
                if old_item:
                    bid = old_item.get(id_field)
                    if bid and bid not in new_base_ids:
                        if dry_run:
                            self.stdout.write(self.style.ERROR(f"[{directory}] DELETE {vid}"))
                        # Deprecate removed item
                        old_item['valid_until'] = yesterday_str
                        old_item['is_active'] = False
                        if not dry_run:
                            with open(os.path.join(target_dir, f"{vid}.json"), 'w') as f:
                                json.dump(old_item, f, indent=4)

            # Update header indices
            header_doc['active_indices'][directory] = new_active_indices

        # Process Subcollections
        # We only process them if they are present in the JSON.
        # If the key is missing, we skip it (don't clear it).
        if 'benefits' in new_data:
            process_sub_collection('benefits', 'benefits', 'benefit_id', 'benefit')
        
        if 'earning_rates' in new_data:
            process_sub_collection('earning_rates', 'earning_rates', 'rate_id', 'rate')
        
        if 'sign_up_bonus' in new_data:
            process_sub_collection('sign_up_bonus', 'sign_up_bonus', 'offer_id', 'offer')

        # Questions
        if 'questions' in new_data:
            questions = new_data.get('questions', [])
            q_dir = os.path.join(card_dir, 'card_questions')
            if not os.path.exists(q_dir): 
                if dry_run:
                    self.stdout.write(self.style.SUCCESS("Would create questions directory"))
                else:    
                    os.makedirs(q_dir)
            
            for index, q in enumerate(questions):
                q_id = q.get('question_id', f"q-{index}")
                q['question_id'] = q_id
                # Questions don't have versioning logic currently, just simple overwrite check
                # For dry run, we can just say "Would update/create question"
                if dry_run:
                    self.stdout.write(f"[QUESTIONS] Would update/create {q_id}")
                else:
                    with open(os.path.join(q_dir, f"{q_id}.json"), 'w') as f:
                        json.dump(q, f, indent=4)

        # 3. Save Header
        if not dry_run:
            with open(header_path, 'w') as f:
                json.dump(header_doc, f, indent=4)
