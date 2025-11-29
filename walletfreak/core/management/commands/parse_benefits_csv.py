import csv
from collections import defaultdict
from django.utils.text import slugify

def parse_benefits_csv(csv_path):
    """
    Parse the benefits CSV and return structured card data.
    
    CSV Format: Vendor,CardName,AnnualFee,BenefitDescription,Category,DollarValue,EffectiveDate
    
    Returns a dictionary mapping card names to their data structure:
    {
        'card_name': {
            'name': str,
            'issuer': str,
            'annual_fee': int,
            'benefits': [
                {
                    'description': str,
                    'category': str,  # 'Permanent', 'Annually', 'Monthly', etc.
                    'dollar_value': float or None,
                    'effective_date': str
                }
            ]
        }
    }
    """
    cards_dict = defaultdict(lambda: {
        'name': '',
        'issuer': '',
        'annual_fee': 0,
        'benefits': []
    })
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Use pipe as delimiter
        reader = csv.DictReader(f, delimiter='|', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            vendor = row['Vendor'].strip()
            card_name = row['CardName'].strip()
            annual_fee_str = row['AnnualFee'].strip()
            benefit_desc = row['BenefitDescription'].strip()
            category = row['Category'].strip()
            dollar_value_str = row['DollarValue'].strip()
            effective_date = row['EffectiveDate'].strip()
            
            # Parse annual fee
            annual_fee = 0
            if annual_fee_str:
                try:
                    annual_fee = int(annual_fee_str)
                except ValueError:
                    annual_fee = 0
            
            # Parse dollar value
            dollar_value = None
            if dollar_value_str and dollar_value_str.upper() != 'N/A':
                try:
                    dollar_value = float(dollar_value_str)
                except ValueError:
                    dollar_value = None
            
            # Initialize card if first time seeing it
            if not cards_dict[card_name]['name']:
                cards_dict[card_name]['name'] = card_name
                cards_dict[card_name]['issuer'] = vendor
                cards_dict[card_name]['annual_fee'] = annual_fee
            
            # Add benefit
            benefit = {
                'description': benefit_desc,
                'category': category,
                'dollar_value': dollar_value,
                'effective_date': effective_date
            }
            cards_dict[card_name]['benefits'].append(benefit)
    
    return dict(cards_dict)


def convert_to_firestore_format(cards_dict):
    """
    Convert parsed cards dictionary to Firestore-ready format.
    
    Returns a list of card documents ready for Firestore.
    """
    firestore_cards = []
    
    for card_name, card_data in cards_dict.items():
        # Create the card document
        card_doc = {
            'name': card_data['name'],
            'issuer': card_data['issuer'],
            'annual_fee': card_data['annual_fee'],
            'benefits': card_data['benefits'],
            'image_url': '',
            'referral_links': [],
            'user_type': []
        }
        
        firestore_cards.append(card_doc)
    
    return firestore_cards


def generate_cards_from_csv(csv_path):
    """
    Main function to parse CSV and return Firestore-ready card data.
    """
    cards_dict = parse_benefits_csv(csv_path)
    return convert_to_firestore_format(cards_dict)


if __name__ == '__main__':
    # For testing
    import os
    csv_path = os.path.join(os.path.dirname(__file__), '../../../default_cards_2025_11_27.csv')
    cards = generate_cards_from_csv(csv_path)
    print(f"Parsed {len(cards)} cards")
    for card in cards[:2]:  # Print first 2 as sample
        print(f"\n{card['name']} ({card['issuer']}):")
        print(f"  Benefits: {len(card['benefits'])}")