import csv
import json
import os
import ast

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
        # Text files use python list repr (e.g. ['Generic Dining'])
        if raw_str.startswith('[') and raw_str.endswith(']'):
            return ast.literal_eval(raw_str)
        return [raw_str]
    except Exception:
        # Fallback to single string
        return [raw_str]

def audit():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_path = os.path.join(base_dir, 'default_category_mapping.json')
    cards_dir = os.path.join(base_dir, 'walletfreak_credit_cards')
    
    category_map = load_category_map(mapping_path)
    print(f"Loaded {len(category_map)} detailed categories form mapping.")

    if not os.path.exists(cards_dir):
        print(f"Error: Directory {cards_dir} not found.")
        return

    files = [f for f in os.listdir(cards_dir) if f.endswith('.txt')]
    print(f"Scanning {len(files)} files in {cards_dir}...\n")

    unmapped_rates_count = 0
    unmapped_benefits_count = 0
    duplicate_rates_count = 0
    
    allowed_duplicate_groups = {"Protection", "Financial & Rewards", "Travel Perks"}
    
    for filename in files:
        filepath = os.path.join(cards_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            parts = content.split('\n---\n')
            
            # --- INFO Section (for Name/Slug) ---
            slug = filename # fallback
            card_name = filename
            if len(parts) > 0 and parts[0].strip():
                lines = parts[0].strip().split('\n')
                if len(lines) > 1:
                    headers = [h.strip() for h in lines[0].split('|')]
                    vals = [v.strip() for v in lines[1].split('|')]
                    row = dict(zip(headers, vals))
                    slug = row.get('slug-id', filename)
                    card_name = row.get('CardName', filename)

            # --- BENEFITS Audit ---
            if len(parts) > 1 and parts[1].strip():
                lines = parts[1].strip().split('\n')
                if len(lines) > 1:
                    headers = [h.strip() for h in lines[0].split('|')]
                    
                    for i, line in enumerate(lines[1:], start=1):
                         vals = [v.strip() for v in line.split('|')]
                         if not vals or len(vals) != len(headers): continue
                         b_row = dict(zip(headers, vals))
                         
                         cat_raw = b_row.get('BenefitCategory', '')
                         cats = parse_category_field(cat_raw)
                         
                         for c in cats:
                            if c not in category_map:
                                unmapped_benefits_count += 1
                                print(f"[FAIL] {slug} (Benefit): Unmapped Category '{c}'")
                                print(f"       Desc: {b_row.get('BenefitDescription', '')[:60]}...")
                                print("-" * 30)

            # --- RATES Audit ---
            if len(parts) > 2 and parts[2].strip():
                lines = parts[2].strip().split('\n')
                if len(lines) > 1:
                    headers = [h.strip() for h in lines[0].split('|')]
                    
                    seen_rate_cats = {} # cat -> line_idx
                    
                    for i, line in enumerate(lines[1:], start=1):
                        vals = [v.strip() for v in line.split('|')]
                        if not vals or len(vals) != len(headers): continue
                        r_row = dict(zip(headers, vals))
                        
                        cat_raw = r_row.get('RateCategory', '')
                        cats = parse_category_field(cat_raw)
                        
                        for c in cats:
                            # 1. Map Check
                            if c not in category_map:
                                unmapped_rates_count += 1
                                print(f"[FAIL] {slug} (Rate): Unmapped Category '{c}'")
                                print(f"       Rate: {r_row.get('EarningRate')} {r_row.get('Currency')}")
                                print("-" * 30)
                            
                            # 2. Duplicate Check within Card
                            hl_group = category_map.get(c, "Unknown")
                            if c in seen_rate_cats:
                                if hl_group not in allowed_duplicate_groups:
                                    duplicate_rates_count += 1
                                    print(f"[FAIL] {slug} (Rate): Duplicate Category '{c}'")
                                    print(f"       Conflict with previous entry")
                                    print("-" * 30)
                            else:
                                seen_rate_cats[c] = i

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("\n" + "="*50)
    print("AUDIT SUMMARY")
    print("="*50)
    
    if unmapped_rates_count == 0 and unmapped_benefits_count == 0 and duplicate_rates_count == 0:
        print("AUDIT PASSED: All categories mapped and clean.")
    else:
        if unmapped_rates_count > 0:
            print(f"Found {unmapped_rates_count} unmapped rate categories.")
        if unmapped_benefits_count > 0:
            print(f"Found {unmapped_benefits_count} unmapped benefit categories.")
        if duplicate_rates_count > 0:
            print(f"Found {duplicate_rates_count} duplicate rate category definitions.")
        print("AUDIT FAILED.")

if __name__ == "__main__":
    audit()
