
import os
import sys
import csv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "walletfreak.settings")

from core.management.commands.parse_benefits_csv import parse_benefits_csv

def debug():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'default_card_benefits.csv')
    
    print(f"Reading from: {csv_path}")
    
    # Custom parser to track line numbers
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        for i, row in enumerate(reader, start=2): # Start 2 because line 1 is header
            slug = (row.get('slug-id') or '').strip()
            name = (row.get('CardName') or '').strip()
            
            key = slug if slug else name
            
            if not key or key == '0' or key == '75' or key.lower() == 'none':
                print(f"\n[Line {i}] Found suspicious key '{key}'")
                print(f"  CardName: {name}")
                print(f"  slug-id: {slug}")
                print(f"  Raw dictionary: {row}")
                sys.exit(1)

if __name__ == "__main__":
    debug()
