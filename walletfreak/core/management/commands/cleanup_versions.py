import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Removes the "version" field from all JSON files in the master credit cards directory'

    def handle(self, *args, **options):
        master_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards', 'master')
        if not os.path.exists(master_dir):
            self.stdout.write(self.style.ERROR(f"Master directory not found: {master_dir}"))
            return

        self.stdout.write("Starting cleanup of 'version' field from JSON files...")
        
        updated_count = 0
        total_checked = 0

        # Walk through all directories in master
        for card_slug in os.listdir(master_dir):
            card_path = os.path.join(master_dir, card_slug)
            if not os.path.isdir(card_path):
                continue
                
            # Check subfolders: benefits, earning_rates, sign_up_bonus
            for sub in ['benefits', 'earning_rates', 'sign_up_bonus']:
                sub_dir = os.path.join(card_path, sub)
                if not os.path.exists(sub_dir):
                    continue
                    
                for fname in os.listdir(sub_dir):
                    if not fname.endswith('.json'):
                        continue
                        
                    f_path = os.path.join(sub_dir, fname)
                    total_checked += 1
                    
                    try:
                        with open(f_path, 'r') as f:
                            data = json.load(f)
                        
                        if 'version' in data:
                            del data['version']
                            
                            with open(f_path, 'w') as f:
                                json.dump(data, f, indent=4)
                            
                            updated_count += 1
                            # self.stdout.write(f"Updated {card_slug}/{sub}/{fname}")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing {f_path}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nCleanup complete. Checked {total_checked} files. Updated {updated_count} files."))
