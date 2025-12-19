import csv
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_csv_info(filename):
    slugs = set()
    columns = []
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            columns = reader.fieldnames
            for row in reader:
                s = row.get('slug-id')
                if s:
                    slugs.add(s.strip())
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
    return slugs, columns

def get_txt_info(filename):
    slugs = set()
    path = os.path.join(BASE_DIR, filename)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if s:
                    slugs.add(s)
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
    return slugs, ["slug-id"]

def get_personality_info(filename):
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
    return slugs, ["(JSON Structure)"]

def print_diff(name, source_slugs, target_slugs, source_filename, target_filename):
    diff = source_slugs - target_slugs
    if diff:
        print(f"\n[FAIL] In {name} ({source_filename}) but NOT in Default Cards ({target_filename}):")
        for s in sorted(diff):
            print(f"  - {s}")
    else:
        print(f"\n[PASS] All slugs in {name} exist in Default Cards.")

def main():
    print("Starting Slug Audit...\n")

    # Files
    FILE_MASTER_CARDS = 'default_credit_cards.csv'
    FILE_CARDS = 'default_card_benefits.csv'
    FILE_SIGNUP = 'default_signup.csv'
    FILE_RATES = 'default_rates.csv'
    FILE_PERSONALITIES = 'default_personalities.json'

    # Load all info
    master_slugs, cols_master = get_csv_info(FILE_MASTER_CARDS)
    cards, cols_cards = get_csv_info(FILE_CARDS)
    signup, cols_signup = get_csv_info(FILE_SIGNUP)
    rates, cols_rates = get_csv_info(FILE_RATES)
    personalities, cols_personalities = get_personality_info(FILE_PERSONALITIES)
    
    # 1. Print File Columns
    print(">>> CHECK 1: File Columns")
    print(f"{FILE_MASTER_CARDS}: {', '.join(cols_master)}")
    print(f"{FILE_CARDS}: {', '.join(cols_cards)}")
    print(f"{FILE_SIGNUP}: {', '.join(cols_signup)}")
    print(f"{FILE_RATES}: {', '.join(cols_rates)}")
    print("-" * 60)

    # 2. Differences vs Master List
    print("\n>>> CHECK 2: Data Consistency (Vs Default Credit Cards Master)")
    
    print_diff("Benefits CSV", cards, master_slugs, FILE_CARDS, FILE_MASTER_CARDS)
    print_diff("Signup CSV", signup, master_slugs, FILE_SIGNUP, FILE_MASTER_CARDS)
    print_diff("Rates CSV", rates, master_slugs, FILE_RATES, FILE_MASTER_CARDS)

    # 3. Personality Integrity
    print("\n>>> CHECK 3: Personality References Integrity")
    unknown_cards = personalities - master_slugs
    if unknown_cards:
        print(f"\n[FAIL] The following cards are referenced in Personalities but DO NOT exist in Master Cards CSV:")
        for s in sorted(unknown_cards):
            print(f"  - {s}")
    else:
        print("\n[PASS] All card references in Personalities are valid.")

    # 3.5 Personality Duplicates Check
    print("\n>>> CHECK 3.5: Personality Duplicates Check")
    try:
        path = os.path.join(BASE_DIR, FILE_PERSONALITIES)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            has_duplicates = False
            for p in data:
                seen_cards = set()
                p_name = p.get('name', 'Unknown')
                slots = p.get('slots', [])
                for slot in slots:
                    cards = slot.get('cards', [])
                    for c in cards:
                        if c in seen_cards:
                            print(f"  [FAIL] Duplicate card '{c}' found in personality '{p_name}'")
                            has_duplicates = True
                        seen_cards.add(c)
            
            if not has_duplicates:
                print("\n[PASS] No duplicate cards found within any personality.")
    except Exception as e:
        print(f"Error checking duplicates: {e}")

    # 4. Global Missing Map
    print("\n>>> CHECK 4: Cross-Reference Map (Where are slugs missing?)")
    
    all_slugs = set(cards) | set(signup) | set(rates) | set(personalities)
    non_existent_slugs = all_slugs - master_slugs
    
    if non_existent_slugs:
        print("\n[!] The following slugs appear in auxiliary files but are missing from the Master Cards CSV:")
        for s in sorted(non_existent_slugs):
            found_in = []
            if s in cards: found_in.append("Benefits")
            if s in signup: found_in.append("Signup")
            if s in rates: found_in.append("Rates")
            if s in personalities: found_in.append("Personalities")
            print(f"  - {s} (Found in: {', '.join(found_in)})")
    else:
        print("\n[PASS] No slugs found outside of the Master Cards CSV.")

if __name__ == "__main__":
    main()
