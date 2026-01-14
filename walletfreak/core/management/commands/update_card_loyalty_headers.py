import os
import json
import requests
import time
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Updates card headers with loyalty_program field using Grok AI matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without saving changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of cards to process (for testing)',
        )

    def handle(self, *args, **options):
        api_key = os.environ.get('GROK_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        dry_run = options.get('dry_run')
        limit = options.get('limit')

        # 1. Load Loyalty Programs
        loyalty_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'program_loyalty')
        programs = []
        if os.path.exists(loyalty_dir):
            for fname in sorted(os.listdir(loyalty_dir)):
                if fname.endswith('.json'):
                    with open(os.path.join(loyalty_dir, fname), 'r') as f:
                        data = json.load(f)
                        programs.append({
                            'id': data.get('program_id'),
                            'name': data.get('program_name')
                        })
        
        if not programs:
            self.stdout.write(self.style.ERROR("No loyalty programs found!"))
            return

        programs_str = "\n".join([f"- {p['id']}: {p['name']}" for p in programs])
        
        # 2. Iterate Cards
        master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
        if not os.path.exists(master_dir):
            self.stdout.write(self.style.ERROR("Master cards directory not found"))
            return

        card_slugs = sorted([d for d in os.listdir(master_dir) if os.path.isdir(os.path.join(master_dir, d))])
        
        if limit:
            card_slugs = card_slugs[:limit]
            
        self.stdout.write(f"Processing {len(card_slugs)} cards with {len(programs)} loyalty programs...")

        count_updated = 0
        count_skipped = 0

        for slug in card_slugs:
            header_path = os.path.join(master_dir, slug, 'header.json')
            if not os.path.exists(header_path):
                self.stdout.write(self.style.WARNING(f"Skipping {slug} (no header.json)"))
                continue

            with open(header_path, 'r') as f:
                header = json.load(f)

            # Skip if already has loyalty_program and it's not null (unless force? No, just skip for now to save tokens)
            # Actually user command implies populating it. Let's assume we want to fill it if missing or null.
            # But maybe we want to re-evaluate? Let's check if it exists.
            # if header.get('loyalty_program'):
            #    self.stdout.write(f"✓ {slug} already has loyalty_program: {header['loyalty_program']}")
            #    continue
            
            card_name = header.get('name', slug)
            issuer = header.get('issuer', 'Unknown')
            
            prompt = f"""
I have a credit card: "{card_name}" issued by "{issuer}".

I need to map this card to its **PRIMARY** loyalty program from the following specific list:

{programs_str}

**Rules**:
1. If the card earns points/miles directly in one of these programs (e.g. Delta Gold Amex -> Delta SkyMiles), select it.
2. If the card earns bank points that TRANSFER to these partners (e.g. Chase Sapphire -> Chase Ultimate Rewards), select the bank program (chase_ur).
3. If the card is a generic cash back card or belongs to a program NOT in the list, return null.

**Return ONLY a JSON object**:
{{
    "loyalty_program": "program_id_from_list_above" or null
}}
"""
            
            try:
                # Call Grok
                response_json = self.call_grok(api_key, prompt)
                
                if response_json:
                    loyalty_id = response_json.get('loyalty_program')
                    
                    # Validate ID
                    if loyalty_id:
                        valid_ids = [p['id'] for p in programs]
                        if loyalty_id not in valid_ids:
                             self.stdout.write(self.style.WARNING(f"⚠️ Grok returned invalid ID '{loyalty_id}' for {slug}. Setting to null."))
                             loyalty_id = None
                    
                    self.stdout.write(f"→ {slug}: {loyalty_id}")
                    
                    if not dry_run:
                        header['loyalty_program'] = loyalty_id
                        with open(header_path, 'w') as f:
                            json.dump(header, f, indent=4)
                        count_updated += 1
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to get valid response for {slug}"))
                    count_skipped += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {slug}: {e}"))
                count_skipped += 1
            
            # Rate limiting / be nice
            if not dry_run:
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"\nDone! Updated {count_updated} cards. Skipped/Failed {count_skipped}."))


    def call_grok(self, api_key, prompt):
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "messages": [
                {"role": "system", "content": "You are a precise data assistant. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "model": "grok-3", # Updated to valid model
            "stream": False,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            return json.loads(content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"API Error: {e}"))
            if 'response' in locals():
                 self.stdout.write(self.style.ERROR(f"Response Body: {response.text}"))
            return None
