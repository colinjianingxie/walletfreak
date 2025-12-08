import csv
from collections import defaultdict
from django.utils.text import slugify

def parse_signup_bonuses_csv(csv_path):
    """
    Parse the signup bonuses CSV and return a dictionary of bonuses.
    
    CSV Format: Vendor|CardName|EffectiveDate|Terms|SignUpBonusValue|Currency|slug-id
    """
    bonuses = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                # robust key: prioritize slug-id
                slug_id = row.get('slug-id')
                key = (slug_id or '').strip() or row['CardName'].strip()
                
                # Parse value
                value = 0
                try:
                    value = int(row['SignUpBonusValue'].strip())
                except ValueError:
                    pass
                    
                bonuses[key] = {
                    'terms': row['Terms'].strip(),
                    'value': value,
                    'currency': row['Currency'].strip(),
                    'effective_date': row['EffectiveDate'].strip()
                }
    except FileNotFoundError:
        print(f"Warning: Signup bonus CSV not found at {csv_path}")
        
    return bonuses

def parse_earning_rates_csv(csv_path):
    """
    Parse the earning rates CSV and return a dictionary of earning rates by card.
    
    CSV Format: Vendor|CardName|EarningRate|Currency|BenefitCategory|AdditionalDetails|slug-id
    
    Returns a dictionary mapping card keys (slug or name) to their earning rates:
    {
        'card_key': {
            'earning_rates': [
                {
                    'rate': float,
                    'currency': str,  # 'points', 'miles', 'cash back', etc.
                    'category': str,  # 'Travel', 'Dining', 'All Purchases', etc.
                    'details': str
                }
            ]
        }
    }
    """
    rates_dict = defaultdict(lambda: {'earning_rates': []})
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                # robust key: prioritize slug-id
                slug_id = row.get('slug-id')
                key = (slug_id or '').strip() or row['CardName'].strip()
                
                # Parse earning rate
                rate = 0.0
                try:
                    rate = float(row['EarningRate'].strip())
                except ValueError:
                    pass
                
                earning_rate = {
                    'rate': rate,
                    'currency': row['Currency'].strip(),
                    'category': row['BenefitCategory'].strip(),
                    'details': row.get('AdditionalDetails', '').strip()
                }
                
                rates_dict[key]['earning_rates'].append(earning_rate)
    except FileNotFoundError:
        print(f"Warning: Earning rates CSV not found at {csv_path}")
    
    return dict(rates_dict)

def parse_points_conversions_csv(csv_path):
    """
    Parse the points conversions CSV and return a dictionary of CPP values.
    
    CSV Format: Vendor|CardName|PointsValueCpp|slug-id
    """
    cpp_values = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                # robust key: prioritize slug-id
                slug_id = row.get('slug-id')
                key = (slug_id or '').strip() or row['CardName'].strip()
                
                # Parse CPP
                cpp = 0.0
                val_str = row['PointsValueCpp'].strip()
                if val_str and val_str.upper() != 'N/A':
                    try:
                        cpp = float(val_str)
                    except ValueError:
                        pass
                        
                cpp_values[key] = cpp
    except FileNotFoundError:
        print(f"Warning: Points conversions CSV not found at {csv_path}")
        
    return cpp_values

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
                    'effective_date': str,
                    'short_description': str,
                    'benefit_type': str,
                    'numeric_value': float or None
                }
            ]
        }
    }
    """
    cards_dict = defaultdict(lambda: {
        'name': '',
        'slug': '',
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
            slug_id_val = row.get('slug-id')
            slug_id = (slug_id_val or '').strip()
            
            # robust key: prioritize slug-id
            key = slug_id if slug_id else card_name
            
            annual_fee_str = row['AnnualFee'].strip()
            benefit_desc = row['BenefitDescription'].strip()
            additional_details = row.get('AdditionalDetails', '').strip()
            category = row['BenefitCategory'].strip()
            time_category = row['TimeCategory'].strip()
            dollar_value_str = row['DollarValue'].strip()
            enrollment_required_str = row.get('EnrollmentRequired', 'False').strip()
            effective_date = row['EffectiveDate'].strip()
            short_desc = row.get('BenefitDescriptionShort', '').strip()
            benefit_type = row.get('BenefitType', '').strip()
            numeric_value_str = row.get('NumericValue', '').strip()
            
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

            # Parse enrollment required
            enrollment_required = enrollment_required_str.lower() == 'true'
            
            # Initialize card if first time seeing it
            if not cards_dict[key]['name']:
                cards_dict[key]['name'] = card_name
                cards_dict[key]['slug'] = slug_id
                cards_dict[key]['issuer'] = vendor
                cards_dict[key]['annual_fee'] = annual_fee
            
            # Add benefit
            # Parse numeric value
            numeric_value = None
            if numeric_value_str and numeric_value_str != 'N/A':
                try:
                    numeric_value = float(numeric_value_str)
                except ValueError:
                    pass

            # Calculate period value mappings based on time category
            period_values = {}
            if dollar_value:
                from datetime import datetime
                current_year = datetime.now().year
                
                if 'Monthly' in time_category:
                    per_month = dollar_value / 12
                    for month in range(1, 13):
                        period_key = f"{current_year}_{month:02d}"
                        period_values[period_key] = round(per_month, 2)
                elif 'Quarterly' in time_category:
                    per_quarter = dollar_value / 4
                    for quarter in range(1, 5):
                        period_key = f"{current_year}_Q{quarter}"
                        period_values[period_key] = round(per_quarter, 2)
                elif 'Semi-annually' in time_category:
                    per_half = dollar_value / 2
                    period_values[f"{current_year}_H1"] = round(per_half, 2)
                    period_values[f"{current_year}_H2"] = round(per_half, 2)
                else:
                    # Annual/Permanent - single period
                    period_values[str(current_year)] = dollar_value

            benefit = {
                'description': benefit_desc,
                'additional_details': additional_details,
                'category': category,
                'time_category': time_category,  # New field for frequency
                'dollar_value': dollar_value,
                'period_values': period_values,  # Pre-calculated mappings for each period
                'enrollment_required': enrollment_required,
                'effective_date': effective_date,
                'short_description': short_desc or benefit_desc,  # Fallback to full desc if short is missing
                'benefit_type': benefit_type,
                'numeric_value': numeric_value
            }
            benefit = {k: v for k, v in benefit.items()} # Ensure dict copy if needed, though not strictly necessary here
            cards_dict[key]['benefits'].append(benefit)

    # Post-process to generate rewards_summary
    for key, card_data in cards_dict.items():
        benefits = card_data['benefits']
        
        # Filter for multipliers and cashback
        earning_rates = []
        for b in benefits:
            b_type = b.get('benefit_type')
            val = b.get('numeric_value')
            short = b.get('short_description', '')
            
            if val:
                if b_type == 'Multiplier':
                    earning_rates.append((val, f"{val}x {short}"))
                elif b_type == 'Cashback':
                    earning_rates.append((val, f"{val}% {short}"))
        
        # Sort by value descending
        earning_rates.sort(key=lambda x: x[0], reverse=True)
        
        # Take top 2
        summary_parts = [rate[1] for rate in earning_rates[:2]]
        
        if summary_parts:
            card_data['rewards_summary'] = ", ".join(summary_parts)
        else:
            # Fallback to credits or generic
            credits = [b for b in benefits if b.get('benefit_type') == 'Credit' and b.get('numeric_value')]
            if credits:
                credits.sort(key=lambda x: x['numeric_value'], reverse=True)
                top_credit = credits[0]
                card_data['rewards_summary'] = f"${top_credit['numeric_value']} {top_credit['short_description']}"
            else:
                card_data['rewards_summary'] = "Various Benefits"

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
            'slug': card_data.get('slug', ''),
            'issuer': card_data['issuer'],
            'annual_fee': card_data['annual_fee'],
            'benefits': card_data['benefits'],
            'earning_rates': card_data.get('earning_rates', []),
            'image_url': '',
            'referral_links': [],
            'sign_up_bonus': card_data.get('sign_up_bonus', {}),
            'verdict': card_data.get('verdict', ''),
            'sign_up_bonus': card_data.get('sign_up_bonus', {}),
            'verdict': card_data.get('verdict', ''),
            'rewards_summary': card_data.get('rewards_summary', ''),
            'points_value_cpp': card_data.get('points_value_cpp', 0.0)
        }
        
        firestore_cards.append(card_doc)
    
    return firestore_cards


def generate_cards_from_csv(csv_path, signup_csv_path=None, rates_csv_path=None, points_csv_path=None):
    """
    Main function to parse CSV and return Firestore-ready card data.
    """
    cards_dict = parse_benefits_csv(csv_path)
    
    if signup_csv_path:
        signup_data = parse_signup_bonuses_csv(signup_csv_path)
        for card_name, card in cards_dict.items():
            if card_name in signup_data:
                card['sign_up_bonus'] = signup_data[card_name]
    
    if rates_csv_path:
        rates_data = parse_earning_rates_csv(rates_csv_path)
        for card_name, card in cards_dict.items():
            if card_name in rates_data:
                card['earning_rates'] = rates_data[card_name]['earning_rates']
    
    if points_csv_path:
        points_data = parse_points_conversions_csv(points_csv_path)
        for key, card in cards_dict.items():
            # Try key (slug-id usually)
            if key in points_data:
                card['points_value_cpp'] = points_data[key]
            # Fallback to name match if keys differ (though parse should handle it)
            elif card['name'] in points_data:
                card['points_value_cpp'] = points_data[card['name']]
                
    return convert_to_firestore_format(cards_dict)


if __name__ == '__main__':
    # For testing
    import os
    csv_path = os.path.join(os.path.dirname(__file__), '../../../default_cards_2025_11_27.csv')
    signup_csv_path = os.path.join(os.path.dirname(__file__), '../../../default_signup_2025_11_30.csv')
    cards = generate_cards_from_csv(csv_path, signup_csv_path)
    print(f"Parsed {len(cards)} cards")
    for card in cards[:2]:  # Print first 2 as sample
        print(f"\n{card['name']} ({card['issuer']}):")
        print(f"  Benefits: {len(card['benefits'])}")