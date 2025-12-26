import csv
import json
import os

def load_category_map(json_path):
    mapping = {}
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for group in data:
                hl_name = group.get('CategoryName', 'Unknown')
                details = group.get('CategoryNameDetailed', [])
                for detail in details:
                    mapping[detail] = hl_name
        return mapping
    except Exception as e:
        print(f"Error loading mapping: {e}")
        return {}

def parse_category_field(raw_str):
    if not raw_str:
        return []
    try:
        data = json.loads(raw_str)
        if isinstance(data, list):
            return [str(x) for x in data]
        return [str(data)]
    except json.JSONDecodeError:
        return [raw_str]

def audit():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_path = os.path.join(base_dir, 'default_category_mapping.json')
    rates_path = os.path.join(base_dir, 'default_rates.csv')
    benefits_path = os.path.join(base_dir, 'default_card_benefits.csv')

    category_map = load_category_map(mapping_path)
    print(f"Loaded {len(category_map)} detailed categories form mapping.")

    print("\n" + "="*50)
    print("AUDITING RATES (default_rates.csv)")
    print("="*50)
    
    try:
        with open(rates_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            unmapped_count = 0
            duplicate_count = 0
            
            # Store rates by slug for duplicate detection
            rates_by_slug = {} # slug -> list of (line_num, [categories])

            for i, row in enumerate(reader, start=2): # Header is 1
                raw_cat = row.get('RateCategory', '')
                cats = parse_category_field(raw_cat)
                slug = row.get('slug-id', 'unknown_slug')
                
                # Mapping Check
                for c in cats:
                    if c not in category_map:
                        unmapped_count += 1
                        print(f"[FAIL] Row {i}: Unmapped Rate Category '{c}'")
                        print(f"       Card: {row.get('CardName', 'Unknown')}")
                        print(f"       Rate: {row.get('EarningRate', '')} {row.get('Currency', '')} ({raw_cat})")
                        print("-" * 30)

                # Collect for Duplicate Check
                if slug not in rates_by_slug:
                    rates_by_slug[slug] = []
                rates_by_slug[slug].append({'line': i, 'categories': cats, 'card_name': row.get('CardName')})

            # Duplicate Check logic
            print("\n" + "-"*50)
            print("Checking for DUPLICATE rate categories per card...")
            print("-"*50)
            
            allowed_duplicate_groups = {"Protection", "Financial & Rewards", "Travel Perks"}

            for slug, entries in rates_by_slug.items():
                seen_cats = {} # cat_string -> line_number
                for entry in entries:
                    for c in entry['categories']:
                        # Check high-level group
                        hl_group = category_map.get(c, "Unknown")
                        
                        if c in seen_cats:
                            if hl_group not in allowed_duplicate_groups:
                                duplicate_count += 1
                                print(f"[FAIL] CARD: {entry['card_name']} (slug: {slug})")
                                print(f"       Duplicate Category: '{c}' (Group: {hl_group})")
                                print(f"       Conflict between Row {seen_cats[c]} and Row {entry['line']}")
                                print("-" * 30)
                        else:
                            seen_cats[c] = entry['line']

            if unmapped_count == 0 and duplicate_count == 0:
                print("All rate categories mapped and unique successfully.")
            else:
                if unmapped_count > 0:
                    print(f"Found {unmapped_count} unmapped rate categories.")
                if duplicate_count > 0:
                    print(f"Found {duplicate_count} duplicate rate category definitions.")


    except FileNotFoundError:
        print(f"Error: {rates_path} not found")

    print("\n" + "="*50)
    print("AUDITING BENEFITS (default_card_benefits.csv)")
    print("="*50)

    try:
        with open(benefits_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            unmapped_count = 0
            for i, row in enumerate(reader, start=2):
                raw_cat = row.get('BenefitCategory', '')
                cats = parse_category_field(raw_cat)
                
                for c in cats:
                    if c not in category_map:
                        unmapped_count += 1
                        print(f"[FAIL] Row {i}: Unmapped Benefit Category '{c}'")
                        print(f"       Card: {row.get('CardName', 'Unknown')}")
                        print(f"       Benefit: {row.get('BenefitDescription', '')[:60]}...")
                        print(f"       Category Field: {raw_cat}")
                        print("-" * 30)
                        
            if unmapped_count == 0:
                print("All benefit categories mapped successfully.")
            else:
                print(f"Found {unmapped_count} unmapped benefit categories.")

    except FileNotFoundError:
        print(f"Error: {benefits_path} not found")

if __name__ == "__main__":
    audit()
