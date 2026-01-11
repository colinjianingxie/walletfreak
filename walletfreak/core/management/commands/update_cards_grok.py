import os
import json
import requests
import datetime
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Updates credit card data using Grok API with relational file structure versioning'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cards',
            type=str,
            help='Comma-separated list of card slugs to update (existing or new)',
        )
        parser.add_argument(
            '--auto-seed',
            action='store_true',
            help='Automatically seed the database after update',
        )
        parser.add_argument(
            '--premium-only',
            action='store_true',
            help='Only update premium tier cards (annual_fee > 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which cards would be updated without making API calls',
        )

    def handle(self, *args, **options):
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        self.master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards', 'master')
        if not os.path.exists(self.master_dir):
            os.makedirs(self.master_dir)

        card_slugs_arg = options.get('cards')
        auto_seed = options.get('auto_seed')
        premium_only = options.get('premium_only')
        dry_run = options.get('dry_run')  # Django converts --dry-run to dry_run
        
        if card_slugs_arg:
            slugs = [s.strip() for s in card_slugs_arg.split(',') if s.strip()]
        else:
            # If no args, update ALL existing cards
            slugs = [d for d in os.listdir(self.master_dir) if os.path.isdir(os.path.join(self.master_dir, d))]

        # Filter for premium tier if requested
        if premium_only:
            filtered_slugs = []
            for slug in slugs:
                header_path = os.path.join(self.master_dir, slug, 'header.json')
                if os.path.exists(header_path):
                    try:
                        with open(header_path, 'r') as f:
                            header_data = json.load(f)
                        annual_fee = header_data.get('annual_fee') or 0
                        if annual_fee > 0:
                            filtered_slugs.append(slug)
                            self.stdout.write(f"✓ {slug} is premium (annual_fee: ${annual_fee})")
                        else:
                            self.stdout.write(self.style.WARNING(f"✗ Skipping {slug} (annual_fee: ${annual_fee})"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"✗ Skipping {slug} (error reading header: {e})"))
                else:
                    # New card without header - skip if premium-only
                    self.stdout.write(self.style.WARNING(f"✗ Skipping {slug} (no header.json found)"))
            slugs = filtered_slugs
            self.stdout.write(f"\nFiltered to {len(slugs)} premium cards")

        # Dry-run mode: just show what would be updated
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\n🔍 DRY RUN MODE - No API calls will be made\n"))
            self.stdout.write(f"The following {len(slugs)} cards would be updated:\n")
            for i, slug in enumerate(slugs, 1):
                header_path = os.path.join(self.master_dir, slug, 'header.json')
                if os.path.exists(header_path):
                    with open(header_path, 'r') as f:
                        header_data = json.load(f)
                    name = header_data.get('name', slug)
                    annual_fee = header_data.get('annual_fee') or 0
                    self.stdout.write(f"  {i}. {name} (${annual_fee}/year)")
                else:
                    self.stdout.write(f"  {i}. {slug} (NEW CARD)")
            self.stdout.write(f"\nTo actually update these cards, run without --dry-run flag")
            return

        self.stdout.write(f"Processing {len(slugs)} cards...")
        updated_slugs = []

        for slug in slugs:
            self.stdout.write(f"Processing {slug}...")
            
            # 1. Hydrate (Load existing data or create template)
            current_data = self.hydrate_card_data(slug)
            
            # 2. Construct Prompt
            prompt = self.construction_prompt(current_data, slug)
            
            # 3. Call API
            # For new cards, apply_url might be missing, Grok handles it via web search
            apply_url = current_data.get('application_link')
            new_data = self.call_grok_api(api_key, prompt, apply_url)
            
            if new_data:
                # 4. Dehydrate & Save (Versioning Logic)
                try:
                    self.dehydrate_and_save(slug, new_data)
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated/created {slug}"))
                    updated_slugs.append(slug)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error saving {slug}: {e}"))
            else:
                self.stdout.write(self.style.ERROR(f"Failed to get valid response for {slug}"))

        # Auto-seed logic
        if auto_seed and updated_slugs:
            self.stdout.write("Running auto-seed...")
            from django.core.management import call_command
            try:
                cards_arg = ",".join(updated_slugs)
                # Apply types=all implied? seed_db defaults to all types if not specified? 
                # seed_db requires checking implementation. 
                # It seems seed_db without types seeds all types if card is specified.
                call_command('seed_db', cards=cards_arg)
                self.stdout.write(self.style.SUCCESS("Auto-seed completed."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Auto-seed failed: {e}"))

    def hydrate_card_data(self, slug):
        """
        Reads the relational files for a card and re-assembles them into a single 
        monolithic JSON object for the LLM context.
        """
        card_dir = os.path.join(self.master_dir, slug)
        header_path = os.path.join(card_dir, 'header.json')

        # New Card Template
        if not os.path.exists(header_path):
            return {
                "slug-id": slug,
                "name": slug.replace('-', ' ').title(),
                "issuer": "",
                "image_url": "",
                "application_link": "",
                "is_524": False,
                "active_indices": {
                    "benefits": [],
                    "earning_rates": [],
                    "sign_up_bonus": []
                },
                "benefits": [],
                "earning_rates": [],
                "sign_up_bonus": [],
                "questions": [] # We map 'card_questions' to 'questions' for LLM simplicity
            }

        # Existing Card
        with open(header_path, 'r') as f:
            data = json.load(f)

        active_indices = data.get('active_indices', {})

        # Helper to load active sub-items
        def load_sub_items(key, directory, id_list):
            items = []
            subdir_path = os.path.join(card_dir, directory)
            if not os.path.exists(subdir_path):
                return items
            
            for item_id in id_list:
                item_path = os.path.join(subdir_path, f"{item_id}.json")
                if os.path.exists(item_path):
                    with open(item_path, 'r') as f:
                        items.append(json.load(f))
            return items

        # Benefits
        data['benefits'] = load_sub_items('benefits', 'benefits', active_indices.get('benefits', []))
        
        # Earning Rates
        data['earning_rates'] = load_sub_items('earning_rates', 'earning_rates', active_indices.get('earning_rates', []))
        
        # Sign Up Bonuses
        data['sign_up_bonus'] = load_sub_items('sign_up_bonus', 'sign_up_bonus', active_indices.get('sign_up_bonus', []))
        
        # Questions (Load all from dir, as they don't have active_index usually, or implement index?)
        # For now, let's load all .json in card_questions
        questions = []
        q_dir = os.path.join(card_dir, 'card_questions')
        if os.path.exists(q_dir):
            for fname in sorted(os.listdir(q_dir)):
                if fname.endswith('.json'):
                    with open(os.path.join(q_dir, fname), 'r') as f:
                        questions.append(json.load(f))
        data['questions'] = questions

        return data

    def dehydrate_and_save(self, slug, new_data):
        """
        Splits the monolithic JSON from LLM into relational files with versioning.
        """
        card_dir = os.path.join(self.master_dir, slug)
        if not os.path.exists(card_dir):
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

        # Update permissible header fields
        for key in header_keys:
            if key in new_data:
                header_doc[key] = new_data[key]

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
            new_items = new_data.get(key, [])
            if not new_items: 
                return
            
            target_dir = os.path.join(card_dir, directory)
            if not os.path.exists(target_dir):
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
                        # Assumption: versioned_id is "{base_id}-v{N}"
                        # We stored base_id in the doc as `benefit_id` or `rate_id`
                        base_id = item.get(id_field)
                        if base_id:
                            base_id_map[base_id] = vid

            for index, item in enumerate(new_items):
                # Ensure item has a base ID
                base_id = item.get(id_field)
                if not base_id:
                    # Generator fallback if LLM forgets ID
                    # e.g. benefit-0
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
                    # Simple equality check of dictionaries after filtering keys
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
                        
                        # Deprecate old file
                        if old_item.get('valid_from') == today_str:
                             # If it was created today, we can just expire it today (effectively 0-day or effectively overwritten logic depending on interpretation, but safer than yesterday)
                             # Or we can treat it as a correction invalidating the previous one.
                             old_item['valid_until'] = today_str
                        else:
                             old_item['valid_until'] = yesterday_str
                        
                        old_item['is_active'] = False
                        with open(os.path.join(target_dir, f"{active_vid}.json"), 'w') as f:
                            json.dump(old_item, f, indent=4)
                            
                else:
                    # NEW ITEM
                    final_vid = f"{base_id}-v1"

                if should_create_new:
                    item['version'] = final_vid.split('-')[-1] # vN
                    item['valid_from'] = today_str
                    item['valid_until'] = None
                    item['is_active'] = True
                    
                    with open(os.path.join(target_dir, f"{final_vid}.json"), 'w') as f:
                        json.dump(item, f, indent=4)
                
                new_active_indices.append(final_vid)

            # Detect deletions (items in current_indices not in new_active_indices)
            # Should we deprecate them?
            # If the LLM didn't return them, assume they are gone?
            # Or should we be conservative?
            # User instruction: "Check whether there are any updated benefits... existing categories... specific"
            # Getting explicit logic might be safer. For now, let's trust the LLM's full list return.
            # If an item id from current is NOT in the new list of base_ids, we deprecate it.
            
            new_base_ids = set()
            for item in new_items:
                if item.get(id_field): new_base_ids.add(item.get(id_field))
            
            for vid in current_indices:
                old_item = current_items_map.get(vid)
                if old_item:
                    bid = old_item.get(id_field)
                    if bid and bid not in new_base_ids:
                        # Deprecate removed item
                        old_item['valid_until'] = yesterday_str
                        old_item['is_active'] = False
                        with open(os.path.join(target_dir, f"{vid}.json"), 'w') as f:
                            json.dump(old_item, f, indent=4)

            # Update header indices
            header_doc['active_indices'][directory] = new_active_indices

        # Process Subcollections
        process_sub_collection('benefits', 'benefits', 'benefit_id', 'benefit')
        process_sub_collection('earning_rates', 'earning_rates', 'rate_id', 'rate')
        process_sub_collection('sign_up_bonus', 'sign_up_bonus', 'offer_id', 'offer')

        # questions - usually just overwrite logic or simple "get all"
        # Let's simple overwrite/ensure existence for questions since they aren't strictly version-pointed in header
        # (Though we might want to version them later, standard files is okay)
        questions = new_data.get('questions', [])
        q_dir = os.path.join(card_dir, 'card_questions')
        if not os.path.exists(q_dir): os.makedirs(q_dir)
        
        # Clean current questions?
        # Maybe just write new ones.
        for index, q in enumerate(questions):
            q_id = q.get('question_id', f"q-{index}")
            q['question_id'] = q_id
            with open(os.path.join(q_dir, f"{q_id}.json"), 'w') as f:
                json.dump(q, f, indent=4)

        # 3. Save Header
        with open(header_path, 'w') as f:
            json.dump(header_doc, f, indent=4)


    def call_grok_api(self, api_key, prompt, apply_url=None):
        from urllib.parse import urlparse
        
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Build search sources
        sources = []
        if apply_url:
            try:
                parsed = urlparse(apply_url)
                domain = parsed.netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                if domain:
                    sources.append({
                        "type": "web",
                        "country": "US",
                        "allowed_websites": [domain]
                    })
                else:
                    sources.append({"type": "web"})
            except:
                sources.append({"type": "web"})
        else:
            # Fallback if no URL (New Card) - Wide search
            sources.append({"type": "web"})
            
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides JSON updates for credit cards."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4", # Updated as per user request
            "stream": False,
            "temperature": 0.2,
            "search_parameters": {
                "mode": "on", 
                "sources": sources,
                "return_citations": False,
                "max_search_results": 10
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 404:
                self.stdout.write(self.style.ERROR(f"API 404 Not Found. URL: {url}"))
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean Markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"API Request Failed: {e}"))
            if 'response' in locals():
                 self.stdout.write(self.style.ERROR(f"Response Body: {response.text}"))
            return None

    def get_all_unique_categories(self):
        """
        Loads the structured unique categories from categories_list.json.
        Returns a formatted string describing the hierarchy to help the LLM.
        """
        json_path = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards', 'categories_list.json')
        if not os.path.exists(json_path):
             # Fallback to old behavior or empty
             return "No categories found."
             
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            # Format as: "Parent Category (Children: Child1, Child2, ...)"
            lines = []
            for item in data:
                parent = item.get('CategoryName')
                children = item.get('CategoryNameDetailed', [])
                child_str = ", ".join(children)
                lines.append(f"- {parent}: [{child_str}]")
            
            return "\n".join(lines)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading categories list: {e}"))
            return "Error loading categories."

    def construction_prompt(self, current_json, slug):
        today = datetime.date.today().isoformat()
        
        # Get dynamic categories
        cat_hierarchy = self.get_all_unique_categories()
        
        # Strip internal fields from current_json to avoid confusing LLM
        clean_json = current_json.copy()
        clean_json.pop('active_indices', None)
        
        prompt = f"""
I want to do a websearch to get the latest updates for the credit card: "{clean_json.get('name', slug)}" (Slug: {slug}) as of {today}.

Here is the CURRENT known data (JSON):
{json.dumps(clean_json, indent=4)}

**TASK**:
1. Search the web (official issuer site preferred) for the current details of this card.
2. Return a JSON object with the UPDATED details.
3. Validate all fields against the schema below.

**VALID CATEGORIES HIERARCHY**:
{cat_hierarchy}

**CRITICAL INSTRUCTIONS FOR UPDATES (READ CAREFULLY)**:
1. **CONSERVATIVE UPDATES**: The "CURRENT known data" provided above is heavily curated. **DO NOT CHANGE** values (especially multipliers or credits) unless you find **EXPLICIT, RECENT EVIDENCE** in the web search results that contradicts it (e.g., a "devaluation" or "new offer").
2. **Ambiguity**: If web results are ambiguous or unclear, **KEEP THE CURRENT VALUE**. Do not guess.
3. **Categories**: You MUST choose categories ONLY from the "Valid Categories Hierarchy" above.
4. **Specificity**: For `benefit_category` and `earning_rates.category`, select the most specific child category if applicable.
5. **No Duplicates**: **DO NOT CREATE DUPLICATE CATEGORIES**.
6. **No Inventions**: Do NOT invent new categories not in the list.

**SCHEMA RULES (Snake Case)**:
- **slug-id**: Must remain "{slug}".
- **name**: Card Name.
- **issuer**: e.g., "American Express", "Chase", "Capital One".
- **image_url**: {clean_json.get('image_url') or "/static/images/credit_cards/" + slug + ".png"}
- **annual_fee**: Number (e.g. 95).
- **application_link**: Official URL.
- **min_credit_score**: Number (e.g. 670).
- **max_credit_score**: Number (e.g. 850).
- **points_value_cpp**: Number or null (e.g. 1.5, or null for cash back).
- **is_524**: Boolean (Willy apply to Chase 5/24 rule).
- **freak_verdict**: Short opinion string.

**SUB-COLLECTIONS**:
- **benefits**: List of objects.
    - `benefit_id`: (IMPORTANT) Keep existing ID if updating an existing benefit (e.g. "dining-credit"). Create logical ID for new ones (e.g. "disney-bundle").
    - `short_description`: e.g. "Uber Cash"
    - `description`: Full text.
    - `value`, `currency` (Cash/Points/Miles), `period` (Monthly/Annually).
    - `benefit_category`: List of strings (e.g. ["Rideshare", "Dining"]).
- **earning_rates**: List of objects.
    - `rate_id`: (IMPORTANT) Keep existing ID (e.g. "dining").
    - `multiplier`: Number (e.g. 4.0).
    - `category`: List of strings (e.g. ["Dining", "Resy Bookings"]). **Must be a list**.
    - `additional_details`: **REQUIRED**. Specific string detailing conditions (e.g. "on purchases made directly with airlines"). Must NOT be empty.
    - `is_default`: Boolean (True for "All other purchases").
- **sign_up_bonus**: List of objects (usually 1).
    - `offer_id`: e.g. "offer-1".
    - `value`: Number.
    - `terms`: e.g. "Spend $4k in 3 months".
    - `currency`: "Points"/"Miles"/"Cash".
- **questions**: List of objects. Generating 3-5 questions based on benefits is REQUIRED if list is empty.
    - `question_id`: e.g. "q-0".
    - `short_desc`: e.g. "Uber Cash".
    - `question`: "Do you use Uber...?"
    - `question_type`: "multiple_choice" or "boolean".
    - `choices`: ["Yes", "No", "Sometimes"].
    - `weights`: [1.0, 0.0, 0.5].
    - `benefit_category`: List of strings (e.g. ["Uber"]).

**INSTRUCTIONS**:
- If `sign_up_bonus` or `questions` are empty in the input, YOU MUST GENERATE them based on the web search data.
- For `sign_up_bonus`, if truly none exists, return an empty list.
- For `questions`, generate 3-5 generic usage questions to gauge if the card fits the user (based on its benefits).

**OUTPUT**:
Return ONLY the strictly valid JSON object. No markdown.
"""
        return prompt
