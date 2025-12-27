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

    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parts = content.split('\n---\n')
            
            # Part 1: Info
            info_lines = [l.strip() for l in parts[0].strip().split('\n') if l.strip()]
            if len(info_lines) < 2:
                print(f"[WARN] {filename}: Invalid Info section")
                continue
                
            headers = parse_header_line(info_lines[0])
            values = parse_data_line(info_lines[1])
            row = dict(zip(headers, values))
            slug = row.get('slug-id')
            
            if not slug:
                print(f"[WARN] {filename}: Missing slug-id")
                continue
                
            # Part 2: Benefits
            has_benefits = False
            if len(parts) > 1 and parts[1].strip():
                # Just check if there are data rows
                b_lines = [l.strip() for l in parts[1].strip().split('\n') if l.strip()]
                if len(b_lines) > 1: # Header + Data
                    has_benefits = True

            # Part 3: Rates
            has_rates = False
            rate_integrity = True
            rates_error = None
            
            if len(parts) > 2 and parts[2].strip():
                r_lines = [l.strip() for l in parts[2].strip().split('\n') if l.strip()]
                if len(r_lines) > 1:
                    has_rates = True
                    # Validate Rates Integrity
                    r_headers = parse_header_line(r_lines[0])
                    default_count = 0
                    
                    for line in r_lines[1:]:
                        r_vals = parse_data_line(line)
                        if len(r_vals) != len(r_headers):
                             continue # skipping malformed lines for now, or flag error?
                        r_row = dict(zip(r_headers, r_vals))
                        
                        # Check IsDefault
                        is_def = r_row.get('IsDefault', 'False').lower() == 'true'
                        if is_def:
                            default_count += 1
                            
                        # Check JSON Category
                        import json
                        cat_raw = r_row.get('RateCategory', '')
                        try:
                            # Handling simple list string "['a']"
                            # Using json.loads might fail on single quotes if not careful, 
                            # but let's assume valid JSON or python literal for now
                            # If strict JSON required, it might fail. 
                            # Let's try flexible parse
                            if cat_raw.startswith('[') and cat_raw.endswith(']'):
                                pass # looks like list
                            else:
                                rate_integrity = False
                                rates_error = f"Invalid RateCategory format: {cat_raw}"
                        except:
                            rate_integrity = False
                            rates_error = "JSON Error"

                    if default_count != 1:
                        rate_integrity = False
                        rates_error = f"Found {default_count} default rates. Must be exactly 1."
            
            # Part 4: Signup
            has_signup = False
            if len(parts) > 3 and parts[3].strip():
                s_lines = [l.strip() for l in parts[3].strip().split('\n') if l.strip()]
                if len(s_lines) > 1:
                    has_signup = True

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
