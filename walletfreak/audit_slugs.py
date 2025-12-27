import os
import sys
import json
from collections import defaultdict

# Add current directory to path so we can import management commands if needed
# But simpler to just read files directly or duplicate lightweight parsing logic 
# to keep this script standalone and fast.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, 'walletfreak_credit_cards')

def parse_header_line(line):
    return [h.strip() for h in line.split('|')]

def parse_data_line(line):
    return [v.strip() for v in line.split('|')]

def get_cards_data(directory):
    """
    Reads all card files and returns a dictionary of data:
    {
        'slug': {
            'has_benefits': bool,
            'has_rates': bool,
            'has_signup': bool,
            'rate_integrity': bool, # one default, valid json
            'rates_error': str,
            'file': filename
        }
    }
    """
    cards_data = {}
    
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} not found.")
        return {}

    files = [f for f in os.listdir(directory) if f.endswith('.json')]
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            slug = data.get('slug-id')
            if not slug:
                print(f"[WARN] {filename}: Missing slug-id")
                continue
                
            # Benefits
            has_benefits = bool(data.get('Benefits'))

            # Rates
            has_rates = False
            rate_integrity = True
            rates_error = None
            
            rates = data.get('EarningRates', [])
            if rates:
                has_rates = True
                default_count = 0
                for r in rates:
                    # Check IsDefault
                    # JSON handles booleans directly usually, but check just in case
                    is_def = r.get('IsDefault')
                    if isinstance(is_def, str):
                        is_def = is_def.lower() == 'true'
                    if is_def:
                        default_count += 1
                        
                    # Check RateCategory (should be list in JSON)
                    cat = r.get('RateCategory')
                    if not isinstance(cat, list):
                         # If it's not a list, it might be a malformed string or null
                         # Our converter ensured lists, but check anyway
                         rate_integrity = False
                         rates_error = f"Invalid RateCategory type: {type(cat)}"

                if default_count != 1:
                    rate_integrity = False
                    rates_error = f"Found {default_count} default rates. Must be exactly 1."
            
            # Signup
            has_signup = bool(data.get('SignUpBonuses'))

            cards_data[slug] = {
                'has_benefits': has_benefits,
                'has_rates': has_rates,
                'has_signup': has_signup,
                'rate_integrity': rate_integrity,
                'rates_error': rates_error,
                'file': filename
            }

        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            
    return cards_data

def get_personality_slugs(filename):
    slugs = set()
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for p in data:
                slots = p.get('slots', [])
                for slot in slots:
                    cards = slot.get('cards', [])
                    for c in cards:
                        if c:
                            slugs.add(c.strip())
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filename}")
    return slugs

def run_audits():
    print("Starting Post-Migration Audit...\n")

    # 1. Load Cards from Files
    # (Source of Truth)
    print(f">>> Loading cards from {CARDS_DIR}...")
    cards_map = get_cards_data(CARDS_DIR)
    master_slugs = set(cards_map.keys())
    
    print(f"Found {len(master_slugs)} valid card files.")
    
    # 2. Check Card Integrity
    print("\n>>> CHECK 1: Card File Integrity")
    integrity_fail = False
    
    for slug, data in cards_map.items():
        issues = []
        if not data['has_rates']:
            issues.append("Missing Rates")
        if not data['rate_integrity']:
            issues.append(f"Rate Integrity Logic: {data['rates_error']}")
        
        # Benefits and Signup generally optional but good to note?
        # Assuming every card *should* have benefits?
        if not data['has_benefits']:
            # issues.append("Missing Benefits (Warning)")
            pass

        if issues:
            print(f"  [FAIL] {slug} ({data['file']}): {', '.join(issues)}")
            integrity_fail = True
    
    if not integrity_fail:
        print("[PASS] All card files have valid structure and rates.")
    
    # 3. Personality Check
    print("\n>>> CHECK 2: Personality References")
    FILE_PERSONALITIES = 'default_personalities.json'
    personality_slugs = get_personality_slugs(FILE_PERSONALITIES)
    
    unknown_cards = personality_slugs - master_slugs
    if unknown_cards:
        print(f"[FAIL] The following cards are referenced in Personalities but DO NOT exist in {CARDS_DIR}:")
        for s in sorted(unknown_cards):
            print(f"  - {s}")
    else:
        print("[PASS] All personality card references are valid.")

    # Summary
    print("\n" + "="*30)
    if integrity_fail or unknown_cards:
        print("AUDIT FAILED.")
        return False
    else:
        print("AUDIT PASSED.")
        return True

if __name__ == "__main__":
    success = run_audits()
    sys.exit(0 if success else 1)
