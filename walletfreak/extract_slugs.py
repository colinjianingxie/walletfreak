"""
Extract slugs and merged categories from walletfreak_credit_cards directory.
"""
import os
import json
from collections import OrderedDict

CARDS_DIR = os.path.join(os.path.dirname(__file__), 'walletfreak_credit_cards')

def extract_slugs():
    """Extract slug IDs from filenames in the credit cards directory."""
    slugs = []
    for filename in os.listdir(CARDS_DIR):
        if filename.endswith('.json'):
            slug = filename.replace('.json', '')
            slugs.append(slug)
    return sorted(slugs)


def extract_merged_categories():
    """
    Extract and merge all categories from all card JSON files.
    Returns a list of category objects with merged CategoryNameDetailed.
    """
    # Use OrderedDict to preserve category order and track icons
    categories = OrderedDict()
    
    for filename in sorted(os.listdir(CARDS_DIR)):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(CARDS_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                card_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not parse {filename}: {e}")
            continue
        
        card_categories = card_data.get('Categories', [])
        for cat in card_categories:
            cat_name = cat.get('CategoryName')
            icon = cat.get('Icon')
            detailed = cat.get('CategoryNameDetailed', [])
            
            if not cat_name:
                continue
            
            if cat_name not in categories:
                categories[cat_name] = {
                    'CategoryName': cat_name,
                    'Icon': icon,
                    'CategoryNameDetailed': set()
                }
            
            # Merge CategoryNameDetailed values
            for detail in detailed:
                categories[cat_name]['CategoryNameDetailed'].add(detail)
    
    # Convert sets to sorted lists for output
    result = []
    for cat_data in categories.values():
        result.append({
            'CategoryName': cat_data['CategoryName'],
            'Icon': cat_data['Icon'],
            'CategoryNameDetailed': sorted(cat_data['CategoryNameDetailed'])
        })
    
    return result


if __name__ == '__main__':
    print("=== SLUGS ===")
    for slug in extract_slugs():
        print(slug)
    
    print("\n=== MERGED CATEGORIES ===")
    merged_categories = extract_merged_categories()
    print(json.dumps(merged_categories, indent=4))
