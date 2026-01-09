import os
import json
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings

class Command(BaseCommand):
    help = 'Adds stable BenefitId to all card JSONs'

    def handle(self, *args, **options):
        cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
        
        if not os.path.exists(cards_dir):
            self.stdout.write(self.style.ERROR(f"Directory not found: {cards_dir}"))
            return

        files = [f for f in os.listdir(cards_dir) if f.endswith('.json')]
        self.stdout.write(f"Processing {len(files)} files...")

        for filename in files:
            filepath = os.path.join(cards_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                benefits = data.get('Benefits', [])
                if not benefits:
                    continue
                    
                modified = False
                existing_ids = set()
                
                # First pass: collect existing IDs (if any) to avoid collisions
                for b in benefits:
                    if 'BenefitId' in b:
                        existing_ids.add(b['BenefitId'])

                for b in benefits:
                    if 'BenefitId' not in b:
                        # Generate ID
                        # Prefer Short Desc, then Desc
                        base_text = b.get('BenefitDescriptionShort') or b.get('BenefitDescription')
                        if not base_text:
                            base_text = "benefit"
                            
                        slug = slugify(base_text)
                        
                        # Handle collisions
                        candidate = slug
                        counter = 1
                        while candidate in existing_ids:
                            candidate = f"{slug}-{counter}"
                            counter += 1
                        
                        b['BenefitId'] = candidate
                        existing_ids.add(candidate)
                        modified = True
                
                if modified:
                    # Save back
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=4)
                    self.stdout.write(self.style.SUCCESS(f"Updated {filename}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {e}"))
