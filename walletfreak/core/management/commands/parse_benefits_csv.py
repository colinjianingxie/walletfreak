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

                # Parse SpendAmount
                spend_amount = 0
                try:
                    spend_amount = int(row.get('SpendAmount', '0').strip())
                except ValueError:
                    pass

                # Parse SignupDurationMonths
                duration_months = 0
                try:
                    duration_months = int(row.get('SignupDurationMonths', '0').strip())
                except ValueError:
                    pass
                    
                bonuses[key] = {
                    'terms': row['Terms'].strip(),
                    'value': value,
                    'currency': row['SignUpBonusType'].strip(),
                    'effective_date': row['EffectiveDate'].strip(),
                    'spend_amount': spend_amount,
                    'duration_months': duration_months
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
                    'details': row.get('AdditionalDetails', '').strip(),
                    'is_default': row.get('IsDefault', '').strip().lower() == 'yes'
                }
                
                rates_dict[key]['earning_rates'].append(earning_rate)
    except FileNotFoundError:
        print(f"Warning: Earning rates CSV not found at {csv_path}")
    
    return dict(rates_dict)

def parse_master_cards_csv(csv_path):
    """
    Parse the master credit cards CSV (default_credit_cards.csv).
    
    CSV Format: Vendor|CardName|PointsValueCpp|slug-id|ImageURL|MinCreditScore|MaxCreditScore|ApplicationLink
    
    Returns a dictionary:
    {
        'card_key': {
            'points_value_cpp': float,
            'image_url': str,
            'min_credit_score': int or None,
            'max_credit_score': int or None,
            'application_link': str
        }
    }
    """
    master_data = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                # robust key: prioritize slug-id
                slug_id = row.get('slug-id')
                key = (slug_id or '').strip() or row['CardName'].strip()
                
                # Parse CPP
                cpp = 0.0
                val_str = row.get('PointsValueCpp', '').strip()
                if val_str and val_str.upper() != 'N/A':
                    try:
                        cpp = float(val_str)
                    except ValueError:
                        pass
                
                image_url = row.get('ImageURL', '').strip()

                # Parse MinCreditScore
                min_score = None
                min_score_str = row.get('MinCreditScore', '').strip()
                if min_score_str and min_score_str.upper() != 'N/A':
                    try:
                        min_score = int(min_score_str)
                    except ValueError:
                        pass

                # Parse MaxCreditScore
                max_score = None
                max_score_str = row.get('MaxCreditScore', '').strip()
                if max_score_str and max_score_str.upper() != 'N/A':
                    try:
                        max_score = int(max_score_str)
                    except ValueError:
                        pass

                # Parse ApplicationLink
                app_link = (row.get('ApplicationLink') or '').strip()
                        
                master_data[key] = {
                    'points_value_cpp': cpp,
                    'image_url': image_url,
                    'min_credit_score': min_score,
                    'max_credit_score': max_score,
                    'application_link': app_link
                }
    except FileNotFoundError:
        print(f"Warning: Master cards CSV not found at {csv_path}")
        
    return master_data

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
            numeric_type_str = row.get('NumericType', '').strip()
            
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
                'numeric_value': numeric_value,
                'numeric_type': numeric_type_str
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


import os

def find_local_image(slug):
    """
    Find local image for a given slug by searching the directory for an exact match.
    This handles case-sensitivity differences between macOS (dev) and Linux (prod).
    Returns relative path (e.g., 'images/credit_cards/slug.PNG') or None.
    """
    if not slug:
        return None
        
    # helper to find static root during management command execution
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    static_images_dir = os.path.join(base_dir, 'static', 'images', 'credit_cards')
    
    # Supported extensions (case-insensitive check)
    extensions = ['.png', '.jpg', '.jpeg', '.webp', '.avif']
    
    # Iterate through the directory to find the actual filename
    # This ensures we get the correct casing (e.g. 'Card.PNG') instead of what we requested ('Card.png')
    # which works on Mac but fails on Linux.
    if not os.path.exists(static_images_dir):
        return None

    try:
        for filename in os.listdir(static_images_dir):
            name, ext = os.path.splitext(filename)
            # Check if slug matches (case-insensitive) and extension is valid
            if name.lower() == slug.lower() and ext.lower() in extensions:
                return f"images/credit_cards/{filename}"
    except OSError:
        pass
        
    return None

def convert_to_firestore_format(cards_dict):
    """
    Convert parsed cards dictionary to Firestore-ready format.
    
    Returns a list of card documents ready for Firestore.
    """
    firestore_cards = []
    
    for card_name, card_data in cards_dict.items():
        # Resolve local image dynamically
        slug = card_data.get('slug', '')
        local_image = find_local_image(slug)
        
        # Create the card document
        card_doc = {
            'name': card_data['name'],
            'slug': slug,
            'issuer': card_data['issuer'],
            'annual_fee': card_data['annual_fee'],
            'benefits': card_data['benefits'],
            'earning_rates': card_data.get('earning_rates', []),
            'image_url': card_data.get('image_url', ''),
            'referral_links': [],
            'sign_up_bonus': card_data.get('sign_up_bonus', {}),
            'verdict': card_data.get('verdict', ''),
            'local_image': local_image,
            'rewards_summary': card_data.get('rewards_summary', ''),
            'rewards_summary': card_data.get('rewards_summary', ''),
            'points_value_cpp': card_data.get('points_value_cpp', 0.0),
            'min_credit_score': card_data.get('min_credit_score'),
            'max_credit_score': card_data.get('max_credit_score'),
            'application_link': card_data.get('application_link', '')
        }
        
        firestore_cards.append(card_doc)
    
    return firestore_cards



def parse_benefit_overrides_csv(csv_path):
    """
    Parse the benefit overrides CSV.
    
    CSV Format: slug-id|benefit_index|period_key|numeric_value
    
    Returns a dictionary:
    {
        'slug-id': {
            benefit_index (int): {
                'period_key': numeric_value (float)
            }
        }
    }
    """
    overrides = defaultdict(lambda: defaultdict(dict))
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                slug = row['slug-id'].strip()
                try:
                    benefit_idx = int(row['benefit_index'].strip())
                    period_key = row['period_key'].strip()
                    val = float(row['numeric_value'].strip())
                    
                    overrides[slug][benefit_idx][period_key] = val
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"Warning: Benefit overrides CSV not found at {csv_path}")
        
    return overrides

def generate_cards_from_csv(csv_path, signup_csv_path=None, rates_csv_path=None, master_csv_path=None, overrides_csv_path=None):
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
    
    if master_csv_path:
        master_data = parse_master_cards_csv(master_csv_path)
        for key, card in cards_dict.items():
            # Try key (slug-id usually)
            data = None
            if key in master_data:
                data = master_data[key]
            # Fallback to name match
            elif card['name'] in master_data:
                data = master_data[card['name']]
            
            if data:
                card['points_value_cpp'] = data['points_value_cpp']
                if data['image_url']:
                    card['image_url'] = data['image_url']
                card['min_credit_score'] = data['min_credit_score']
                card['max_credit_score'] = data['max_credit_score']
                card['application_link'] = data['application_link']

    if overrides_csv_path:
        overrides_data = parse_benefit_overrides_csv(overrides_csv_path)
        for slug, card_overrides in overrides_data.items():
            # Find the card by slug
            target_card = None
            if slug in cards_dict:
                target_card = cards_dict[slug]
            
            if target_card:
                benefits = target_card['benefits']
                for idx, period_updates in card_overrides.items():
                    if 0 <= idx < len(benefits):
                        # Apply updates to period_values
                        if 'period_values' not in benefits[idx]:
                            benefits[idx]['period_values'] = {}
                        
                        for p_key, p_val in period_updates.items():
                            benefits[idx]['period_values'][p_key] = p_val
                
    return convert_to_firestore_format(cards_dict)


if __name__ == '__main__':
    # For testing
    import os
    csv_path = os.path.join(os.path.dirname(__file__), '../../../default_card_benefits.csv')
    signup_csv_path = os.path.join(os.path.dirname(__file__), '../../../default_signup.csv')
    rates_csv_path = os.path.join(os.path.dirname(__file__), '../../../default_rates.csv')
    
    cards = generate_cards_from_csv(csv_path, signup_csv_path, rates_csv_path=rates_csv_path)
    print(f"Parsed {len(cards)} cards")
    for card in cards[:5]:  # Print first 5 as sample
        print(f"\n{card['name']} ({card['issuer']}):")
        print(f"  Image URL: {card.get('image_url', 'N/A')}")
        EARNING_RATES = card.get('earning_rates', [])
        print(f"  Earning Rates: {len(EARNING_RATES)}")
        for rate in EARNING_RATES:
            print(f"    - {rate['rate']} {rate['currency']} ({rate['category']}) - Default: {rate.get('is_default')}")