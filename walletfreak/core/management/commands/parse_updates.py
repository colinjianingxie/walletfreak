import os
import json
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

def is_float(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

def process_json_card(data):
    """
    Transforms JSON card data into the structure expected by Firestore.
    """
    if not data:
        return None, [], []

    # Map Basic Info
    card_doc = {
        'name': data.get('CardName'),
        'slug': data.get('slug-id'),
        'issuer': data.get('Vendor'),
        'annual_fee': int(data.get('AnnualFee', 0)) if str(data.get('AnnualFee', '0')).isdigit() else 0,
        'image_url': data.get('ImageURL'),
        'application_link': data.get('ApplicationLink'),
        'is_524': bool(data.get('Is524')),
        'min_credit_score': int(data.get('MinCreditScore')) if str(data.get('MinCreditScore', '')).isdigit() else None,
        'max_credit_score': int(data.get('MaxCreditScore')) if str(data.get('MaxCreditScore', '')).isdigit() else None,
        'points_value_cpp': float(data.get('PointsValueCpp')) if is_float(data.get('PointsValueCpp')) else 0.0,
        'processor_vendor': data.get('ProcessorVendor'),
    }

    # Benefits
    processed_benefits = []
    raw_benefits = data.get('Benefits', [])
    for b in raw_benefits:
        # Category is usually a list of strings in the new JSON
        category = b.get('BenefitCategory')
        if not isinstance(category, list):
            category = [category] if category else []
            
        # Time Category / Period Values Logic
        time_category = b.get('TimeCategory', '') or ''
        dollar_value = float(b.get('DollarValue')) if is_float(b.get('DollarValue')) else None
        
        period_values = {}
        if dollar_value:
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
                period_values[str(current_year)] = dollar_value

        processed_benefits.append({
            'description': b.get('BenefitDescription'),
            'additional_details': b.get('AdditionalDetails'),
            'category': category,
            'time_category': time_category,
            'dollar_value': dollar_value,
            'period_values': period_values,
            'enrollment_required': str(b.get('EnrollmentRequired', 'False')).lower() == 'true' if isinstance(b.get('EnrollmentRequired'), str) else bool(b.get('EnrollmentRequired')),
            'effective_date': b.get('EffectiveDate'),
            'benefit_id': b.get('BenefitId'),
            'short_description': b.get('BenefitDescriptionShort') or b.get('BenefitDescription'),
            'benefit_type': b.get('BenefitType'),
            'numeric_value': float(b.get('NumericValue')) if is_float(b.get('NumericValue')) else None,
            'numeric_type': b.get('NumericType'),
        })
    card_doc['benefits'] = processed_benefits
    
    # Earning Rates
    processed_rates = []
    raw_rates = data.get('EarningRates', [])
    for r in raw_rates:
        category = r.get('RateCategory')
        if not isinstance(category, list):
            category = [category] if category else []
            
        processed_rates.append({
            'rate': float(r.get('EarningRate')) if is_float(r.get('EarningRate')) else 0.0,
            'currency': r.get('Currency'),
            'category': category,
            'details': r.get('AdditionalDetails'),
            'is_default': str(r.get('IsDefault', 'False')).lower() == 'true' if isinstance(r.get('IsDefault'), str) else bool(r.get('IsDefault'))
        })
    card_doc['earning_rates'] = processed_rates
    
    # Signup Bonuses (List)
    processed_bonuses = []
    raw_bonuses = data.get('SignUpBonuses', [])
    # In case it's a dict (old format or edge case), wrap it
    if isinstance(raw_bonuses, dict):
        raw_bonuses = [raw_bonuses]
        
    for s in raw_bonuses:
        processed_bonuses.append({
             'value': int(s.get('SignUpBonusValue')) if str(s.get('SignUpBonusValue', '')).isdigit() else 0,
             'currency': s.get('SignUpBonusType'), 
             'terms': s.get('Terms'),
             'effective_date': s.get('EffectiveDate'),
             'spend_amount': int(s.get('SpendAmount')) if str(s.get('SpendAmount', '')).isdigit() else 0,
             'duration_months': int(s.get('SignupDurationMonths')) if str(s.get('SignupDurationMonths', '')).isdigit() else 0,
        })
    card_doc['sign_up_bonus'] = processed_bonuses # Now a list

    # Freak Verdict
    card_doc['freak_verdict'] = data.get('FreakVerdict')
    
    # Questions
    card_doc['questions'] = data.get('Questions', [])

    return card_doc, data.get('Categories', [])

def generate_cards_from_files(directory):
    """
    Reads all .json files in directory, parses them, and returns:
    - cards: list of card documents (with embedded questions and benefits etc)
    - categories: list of unique category objects (merged from all files)
    - questions: [] (now embedded in cards)
    """
    cards = []
    all_categories = {} # map Name -> Category Object (to deduplicate)
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return [], [], []

    files = [f for f in os.listdir(directory) if f.endswith('.json')]
    print(f"Found {len(files)} JSON files in {directory}")

    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r') as f:
                raw_data = json.load(f)
            
            card_doc, categories = process_json_card(raw_data)
            
            if card_doc:
                cards.append(card_doc)
            
            # Merge categories
            for cat in categories:
                name = cat.get('CategoryName')
                if name:
                    if name not in all_categories:
                        all_categories[name] = cat
                    else:
                        # Merge detailed items
                        existing_detailed = set(all_categories[name].get('CategoryNameDetailed', []))
                        new_detailed = set(cat.get('CategoryNameDetailed', []))
                        combined = list(existing_detailed.union(new_detailed))
                        all_categories[name]['CategoryNameDetailed'] = combined
                        
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            
    return cards, list(all_categories.values()), []

def parse_benefit_overrides_csv(csv_path):
    """
    Parse the benefit overrides CSV.
    CSV Format: slug-id|benefit_index|period_key|numeric_value
    """
    import csv 
    overrides = defaultdict(lambda: defaultdict(dict))
    
    if not os.path.exists(csv_path):
        print(f"Warning: Benefit overrides CSV not found at {csv_path}")
        return overrides
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                slug = row.get('slug-id', '').strip()
                if not slug:
                    continue
                    
                try:
                    benefit_idx = int(row['benefit_index'].strip())
                    period_key = row['period_key'].strip()
                    val = float(row['numeric_value'].strip())
                    
                    overrides[slug][benefit_idx][period_key] = val
                except (ValueError, KeyError) as e:
                    # skip malformed rows
                    continue
    except Exception as e:
        logger.error(f"Error parsing benefit overrides: {e}")
        
    return overrides

def apply_overrides(cards, overrides_csv_path):
    """
    Applies benefit overrides to the list of card objects.
    """
    if not overrides_csv_path:
        return cards
        
    overrides = parse_benefit_overrides_csv(overrides_csv_path)
    if not overrides:
        return cards
        
    print(f"Applying overrides for {len(overrides)} cards...")
    
    for card in cards:
        slug = card.get('slug')
        if slug in overrides:
            card_overrides = overrides[slug]
            benefits = card.get('benefits', [])
            
            for idx, period_updates in card_overrides.items():
                if 0 <= idx < len(benefits):
                    # update period_values
                    if 'period_values' not in benefits[idx] or benefits[idx]['period_values'] is None:
                        benefits[idx]['period_values'] = {}
                    
                    for p_key, p_val in period_updates.items():
                        benefits[idx]['period_values'][p_key] = p_val
                        
    return cards
