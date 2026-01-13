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
        parser.add_argument(
            '--update-types',
            type=str,
            default='all',
            help='Comma-separated list of components to update: header, bonus, benefits, rates, questions, all (default: all)',
        )
        parser.add_argument(
            '--prompt',
            action='store_true',
            help='Output the generated prompt for debugging without making API calls',
        )
    def handle(self, *args, **options):
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        self.master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        if not os.path.exists(self.master_dir):
            os.makedirs(self.master_dir)

        card_slugs_arg = options.get('cards')
        auto_seed = options.get('auto_seed')
        premium_only = options.get('premium_only')
        dry_run = options.get('dry_run')  # Django converts --dry-run to dry_run
        update_types_arg = options.get('update_types', 'all')
        
        # Parse and validate update_types
        valid_types = {'header', 'bonus', 'benefits', 'rates', 'questions', 'all'}
        update_types_list = [t.strip() for t in update_types_arg.split(',') if t.strip()]
        
        # Validate types
        invalid_types = set(update_types_list) - valid_types
        if invalid_types:
            self.stdout.write(self.style.ERROR(f"Invalid update types: {', '.join(invalid_types)}"))
            self.stdout.write(f"Valid types: {', '.join(valid_types)}")
            return
        
        # If 'all' is specified, update everything
        if 'all' in update_types_list:
            update_types_list = ['header', 'bonus', 'benefits', 'rates', 'questions']
        
        self.stdout.write(f"Update types: {', '.join(update_types_list)}")
        
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
            current_data = self.hydrate_card_data(slug, update_types_list)
            
            # 2. Construct Prompt
            prompt = self.construction_prompt(current_data, slug, update_types_list)
            
            # If prompt flag is set, output prompt and skip this card
            if options.get('prompt'):
                self.stdout.write(self.style.SUCCESS(f"\nGenerative Prompt for {slug}:"))
                self.stdout.write("-" * 50)
                self.stdout.write(prompt)
                self.stdout.write("-" * 50)
                
                # Write prompt to file for debugging/inspection
                prompt_file = os.path.join(settings.BASE_DIR, '..', 'card_updates.json')
                with open(prompt_file, 'w') as f:
                    f.write(prompt)
                self.stdout.write(self.style.SUCCESS(f"Prompt written to {prompt_file}"))
                
                continue
            
            # 3. Call API
            # For new cards, apply_url might be missing, Grok handles it via web search
            apply_url = current_data.get('application_link')
            new_data = self.call_grok_api(api_key, prompt, apply_url)
            
            if new_data:
                # 4. Dehydrate & Save (Versioning Logic)
                try:
                    self.dehydrate_and_save(slug, new_data, update_types_list)
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

    def hydrate_card_data(self, slug, update_types=None):
        """
        Reads the relational files for a card and re-assembles them into a single 
        monolithic JSON object for the LLM context.
        Only loads components specified in update_types to reduce API token usage.
        """
        if update_types is None:
            update_types = ['bonus', 'benefits', 'rates', 'questions']
        
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
                "benefits": [] if 'benefits' in update_types else None,
                "earning_rates": [] if 'rates' in update_types else None,
                "sign_up_bonus": [] if 'bonus' in update_types else None,
                "questions": [] if 'questions' in update_types else None
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

        # Only load components that will be updated
        if 'benefits' in update_types:
            data['benefits'] = load_sub_items('benefits', 'benefits', active_indices.get('benefits', []))
        else:
            data['benefits'] = None
        
        if 'rates' in update_types:
            data['earning_rates'] = load_sub_items('earning_rates', 'earning_rates', active_indices.get('earning_rates', []))
        else:
            data['earning_rates'] = None
        
        if 'bonus' in update_types:
            data['sign_up_bonus'] = load_sub_items('sign_up_bonus', 'sign_up_bonus', active_indices.get('sign_up_bonus', []))
        else:
            data['sign_up_bonus'] = None
        
        if 'questions' in update_types:
            questions = []
            q_dir = os.path.join(card_dir, 'card_questions')
            if os.path.exists(q_dir):
                for fname in sorted(os.listdir(q_dir)):
                    if fname.endswith('.json'):
                        with open(os.path.join(q_dir, fname), 'r') as f:
                            questions.append(json.load(f))
            data['questions'] = questions
        else:
            data['questions'] = None

        return data

    def dehydrate_and_save(self, slug, new_data, update_types=None):
        """
        Splits the monolithic JSON from LLM into relational files with versioning.
        Only processes components specified in update_types.
        """
        if update_types is None:
            update_types = ['bonus', 'benefits', 'rates', 'questions']
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

        # Process Subcollections - only if specified in update_types
        if 'benefits' in update_types:
            process_sub_collection('benefits', 'benefits', 'benefit_id', 'benefit')
        
        if 'rates' in update_types:
            process_sub_collection('earning_rates', 'earning_rates', 'rate_id', 'rate')
        
        if 'bonus' in update_types:
            process_sub_collection('sign_up_bonus', 'sign_up_bonus', 'offer_id', 'offer')

        # Questions - only if specified in update_types
        if 'questions' in update_types:
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
        json_path = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'categories_list.json')
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

    def construction_prompt(self, current_json, slug, update_types=None):
        if update_types is None:
            update_types = ['bonus', 'benefits', 'rates', 'questions']
        
        today = datetime.date.today().isoformat()
        
        # Get dynamic categories
        cat_hierarchy = self.get_all_unique_categories()
        
        # Strip internal fields from current_json to avoid confusing LLM
        clean_json = current_json.copy()
        clean_json.pop('active_indices', None)
        
        # Remove components not being updated from the JSON to reduce token usage
        if 'benefits' not in update_types:
            clean_json.pop('benefits', None)
        if 'rates' not in update_types:
            clean_json.pop('earning_rates', None)
        if 'bonus' not in update_types:
            clean_json.pop('sign_up_bonus', None)
        if 'questions' not in update_types:
            clean_json.pop('questions', None)
        
        # Build component-specific instructions
        components_to_update = []
        if 'header' in update_types:
            components_to_update.append("header (card metadata)")
        if 'bonus' in update_types:
            components_to_update.append("sign-up bonus")
        if 'benefits' in update_types:
            components_to_update.append("benefits")
        if 'rates' in update_types:
            components_to_update.append("earning rates")
        if 'questions' in update_types:
            components_to_update.append("questions")
        
        components_str = ", ".join(components_to_update)
        
        # Determine image_url instruction
        if clean_json.get('image_url'):
            image_url_instr = f'- **image_url**: "{clean_json["image_url"]}" (Keep as provided).'
        else:
            image_url_instr = '- **image_url**: null (Default to null if no image provided).'

        # 3. Clean application_link if needed (remove markdown)
        app_link = clean_json.get('application_link', '')
        if app_link and app_link.startswith('[') and '](' in app_link and app_link.endswith(')'):
             try:
                 # Extract URL from [text](url)
                 clean_json['application_link'] = app_link.split('](')[1][:-1]
             except:
                 pass
        
        prompt = f"""
I want to do a websearch to get the latest updates for the credit card: "{clean_json.get('name', slug)}" (Slug: {slug}) as of {today}.

**FOCUS**: This update is ONLY for: {components_str}. Do NOT update other components.

Here is the CURRENT known data (JSON):
{json.dumps(clean_json, indent=4)}

**TASK**:
1. Search the web (official issuer site preferred) for the current details of this card.
2. Return a JSON object with the UPDATED details for {components_str} ONLY.
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
{image_url_instr}
- **annual_fee**: Number (e.g. 95, 0 for no fee).
- **application_link**: Official URL to apply for the card.
- **min_credit_score**: Number (e.g. 670). Use 300 for secured cards.
- **max_credit_score**: Number (e.g. 850).
- **points_value_cpp**: Number or null (e.g. 1.5 for points cards, null for cash back).
- **is_524**: Boolean (true if applies to Chase 5/24 rule).
- **freak_verdict**: String: short opinion or "No Freak verdict for this card yet".
"""

        # Add header-specific instructions
        if 'header' in update_types:
            prompt += """
**HEADER FIELDS** (REQUIRED TO UPDATE):
ALL of these fields MUST be included in your response:
- `slug-id`: String (keep as provided)
- `name`: String (card name)
- `issuer`: String (e.g. "Citi", "Chase", "American Express")
- `image_url`: String (or null if not provided)
- `annual_fee`: Number (e.g. 95, use 0 for no fee)
- `application_link`: String (official application URL)
- `min_credit_score`: Number (e.g. 670, use 300 for secured cards)
- `max_credit_score`: Number (e.g. 850)
- `points_value_cpp`: Number or null (cents per point, null for cash back)
- `is_524`: Boolean (true/false), if having the card will affect chase 5/24 rule
- `freak_verdict`: String (brief verdict or "No Freak verdict for this card yet")
"""

        # Add component-specific schema instructions
        if 'benefits' in update_types:
            prompt += """
**BENEFITS** (REQUIRED TO UPDATE):
- **benefits**: List of objects.
- `benefit_id`: (IMPORTANT) Keep existing ID if updating an existing benefit (e.g. "dining-credit"). Create logical ID for new ones (e.g. "disney-bundle").
- `short_description`: e.g. "Uber Cash"
- `description`: Full text.
- `additional_details`: Brief context (e.g. "For prepaid hotel/vacation rental bookings").
- `benefit_category`: List of strings (e.g. ["Rideshare", "Dining"]).
- `benefit_type`: "Credit", "Perk", "Insurance".
- `numeric_value`: Float/Number (e.g. 200.0).
- `numeric_type`: "Cash", "Points", "Miles".
- `dollar_value`: Integer estimated dollar value (e.g. 200).
- `time_category`: "Annually (calendar year)", "Monthly", "One-time", "Per Use", "Quarterly".
- `enrollment_required`: Boolean.
- `effective_date`: String (YYYY-MM-DD) or null.

**CRITICAL FOR BENEFITS**:
- **SPLIT BUNDLED CREDITS**: If a card has a "total annual credit" composed of distinct parts (e.g., "$400 total credit" = "$200 Hotel Credit" + "$200 Airline Fee Credit"), you **MUST** create separate benefit objects for each distinct part. Do not bundle them.
- **Granularity**: We want detailed, separate benefits for tracking purposes.
"""


        if 'rates' in update_types:
            prompt += """
**EARNING RATES** (REQUIRED TO UPDATE):
- **earning_rates**: List of objects. **EVERY card MUST have at least one earning rate** - at minimum an "All Other Purchases" default rate.
- `rate_id`: (IMPORTANT) Keep existing ID (e.g. "dining"). For new cards, create logical IDs like "dining", "travel", "all-other".
- `multiplier`: Number (e.g. 4.0, 1.5, 1.0 for base rate).
- `category`: List of strings (e.g. ["Dining", "Resy Bookings"]). **Must be a list**. Use ["Financial Rewards", "All Purchases"] for the default rate.
- `additional_details`: **REQUIRED**. Specific string detailing conditions (e.g. "on purchases made directly with airlines"). Use "on all other purchases" for default.
- `is_default`: Boolean (True for "All other purchases" rate, False for bonus categories).

**CRITICAL**: You MUST generate earning rates for new cards. Every card earns something on purchases - research and include:
1. Bonus category rates (e.g., 3x on dining)
2. Default "all other purchases" rate (usually 1x or 1% or 2%)
"""


        if 'bonus' in update_types:
            prompt += """
**SIGN-UP BONUS** (REQUIRED TO UPDATE):
- **sign_up_bonus**: List of objects (usually 1).
- `offer_id`: (CRITICAL FOR VERSIONING) If an object exists in the current data's `sign_up_bonus`, you MUST maintain the SAME `offer_id` (e.g. "offer-1") when updating the value or terms of the current public offer. DO NOT create new IDs like "offer-75k" or "limited-time-offer". Only change the ID if this is a completely different promotion type (e.g., switching from points to cash back).
- `value`: Number (integer).
- `terms`: e.g. "Spend $4k in 3 months".
- `currency`: Exactly one of: "Points", "Miles", "Cash".
- If no sign-up bonus currently exists, return an empty list [].
- If a bonus existed but has expired with no replacement, return an empty list [].
"""

        if 'questions' in update_types:
            prompt += """
**QUESTIONS** (REQUIRED TO UPDATE):
- **questions**: List of objects. Generating 3-5 questions based on benefits is REQUIRED if list is empty.
- `question_id`: e.g. "q-0".
- `short_desc`: e.g. "Uber Cash".
- `question`: "Do you use Uber...?"
- `question_type`: "multiple_choice" or "boolean".
- `choices`: ["Yes", "No", "Sometimes"].
- `weights`: [1.0, 0.0, 0.5].
- `benefit_category`: List of strings (e.g. ["Uber"]).
- Generate 3-5 generic usage questions to gauge if the card fits the user (based on its benefits).
"""

        prompt += f"""
**OUTPUT**:
Return ONLY the strictly valid JSON object with these components: {components_str}. Include the slug-id, name, and issuer fields as well. No markdown.
"""
        return prompt

    def get_all_unique_categories(self):
        """
        Load categories from categories_list.json and format for LLM prompt.
        """
        categories_path = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'categories_list.json')
        
        try:
            with open(categories_path, 'r') as f:
                categories_data = json.load(f)
            
            # Format categories for the prompt
            formatted = []
            for parent_cat in categories_data:
                parent_name = parent_cat.get('CategoryName')
                children = parent_cat.get('CategoryNameDetailed', [])
                
                if children:
                    formatted.append(f"- **{parent_name}**: {', '.join(children)}")
                else:
                    formatted.append(f"- **{parent_name}**")
            
            return "\n".join(formatted)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error loading categories list: {e}"))
            return "Error loading categories."
