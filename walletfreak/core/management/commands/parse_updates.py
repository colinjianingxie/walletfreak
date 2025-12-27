import os
import csv
import json
import logging
from io import StringIO
from collections import defaultdict
from core.services import db

logger = logging.getLogger(__name__)

SECTIONS = [
    "Card Info",
    "Benefits",
    "Rates",
    "Signup Bonus",
    "Questions",
    "Category Mapping"
]

def parse_csv_section(content):
    """Parses a CSV-like section (pipe-delimited) into a list of dicts."""
    if not content.strip():
        return []
    
    # Use StringIO to treat string as file for csv module
    f = StringIO(content.strip())
    reader = csv.DictReader(f, delimiter='|')
    
    # helper to strip whitespace from keys and values
    cleaned_rows = []
    try:
        data = list(reader)
        # The reader keys might have whitespace if not careful, but DictReader usually handles headers well if they are standard.
        # However, our file format might have spaces around pipes like "Vendor | CardName"
        # csv.DictReader with delimiter='|' considers " Vendor " as the key if strictly parsing.
        # Let's clean headers and values manually to be safe.
        
        # Actually, let's re-read with a better approach towards whitespace if needed.
        # But `populate_updates.py` writes with ` | `.
        # So `a | b` becomes headers `a ` and ` b`.
        # We need to strip keys and values.
        
        # DictReader uses the first line as fieldnames.
        if not Reader_Fieldnames_Cleaned(reader):
             # If headers have spaces, we need to map them.
             pass

    except csv.Error as e:
        logger.error(f"Error parsing CSV section: {e}")
        return []
        
    for row in data:
        cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
        cleaned_rows.append(cleaned_row)
        
    return cleaned_rows

def Reader_Fieldnames_Cleaned(reader):
    # This is slightly tricky with DictReader after it's been iterated or read.
    # So instead, let's just parse manually to be robust against " | " spacing.
    return True

def parse_csv_content_robust(content):
    """
    Manually parses pipe-delimited content to handle ' | ' spacing gracefully.
    """
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    if not lines:
        return []
    
    headers = [h.strip() for h in lines[0].split('|')]
    rows = []
    
    for line in lines[1:]:
        values = [v.strip() for v in line.split('|')]
        # Combine headers and values
        # specific handling if lengths differ?
        row_dict = {}
        for i, h in enumerate(headers):
            val = values[i] if i < len(values) else ''
            row_dict[h] = val
        rows.append(row_dict)
        
    return rows

def parse_update_file(filepath):
    """
    Parses a single .txt update file.
    Returns:
        card_data (dict): merged card data
        categories (list): list of category objects to upsert
        questions (list): list of question objects
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts = content.split('\n---\n')
    
    # Initialize containers
    card_info = {}
    benefits = []
    rates = []
    signup = {}
    questions = []
    category_mapping = []
    
    # We expect 6 parts in order, but let's be safe
    # The file structure is constant as per populate_updates.py
    
    # 1. Card Info
    if len(parts) > 0:
        rows = parse_csv_content_robust(parts[0])
        if rows:
            card_info = rows[0] # Should be single row
            
    # 2. Benefits
    if len(parts) > 1:
        benefits = parse_csv_content_robust(parts[1])
        
    # 3. Rates
    if len(parts) > 2:
        rates = parse_csv_content_robust(parts[2])
        
    # 4. Signup Bonus
    if len(parts) > 3:
        rows = parse_csv_content_robust(parts[3])
        if rows:
            signup = rows[0]
            
    # 5. Questions
    if len(parts) > 4:
        questions = parse_csv_content_robust(parts[4])
        
    # 6. Category Mapping
    if len(parts) > 5:
        try:
            category_mapping = json.loads(parts[5])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse category mapping JSON in {filepath}")
            
    return {
        'card_info': card_info,
        'benefits': benefits,
        'rates': rates,
        'signup': signup,
        'questions': questions,
        'category_mapping': category_mapping
    }

def process_card_data(parsed_data):
    """
    Transforms parsed strings into the structure expected by Firestore/Application.
    Similar to logic in parse_benefits_csv.py but adapted for the flat dicts.
    """
    info = parsed_data['card_info']
    if not info:
        return None, [], []
        
    # Basic Info
    card_doc = {
        'name': info.get('CardName'),
        'slug': info.get('slug-id'),
        'issuer': info.get('Vendor'),
        'annual_fee': int(info.get('AnnualFee', 0)) if info.get('AnnualFee', '0').isdigit() else 0,
        'image_url': info.get('ImageURL'),
        'application_link': info.get('ApplicationLink'),
        'is_524': info.get('Is524', 'True').lower() == 'true',
        'min_credit_score': int(info.get('MinCreditScore')) if info.get('MinCreditScore', '').isdigit() else None,
        'max_credit_score': int(info.get('MaxCreditScore')) if info.get('MaxCreditScore', '').isdigit() else None,
        'points_value_cpp': float(info.get('PointsValueCpp')) if is_float(info.get('PointsValueCpp')) else 0.0,
    }

    # Benefits
    processed_benefits = []
    for b in parsed_data['benefits']:
        # Deserialize category list if possible, or leave as string
        cat_raw = b.get('BenefitCategory')
        try:
            # It might be a list string "['a', 'b']" or just a string
            if cat_raw.startswith('[') and cat_raw.endswith(']'):
                # crude unsafe parse or json loads? default_rates uses single quotes often which is not JSON
                # but populate_updates uses ast.literal_eval. 
                import ast
                category = ast.literal_eval(cat_raw)
            else:
                 category = [cat_raw]
        except:
            category = [cat_raw]
            
        # Time Category / Period Values Logic
        # (Reusing logic from parse_benefits_csv.py)
        time_category = b.get('TimeCategory', '')
        dollar_value = float(b.get('DollarValue')) if is_float(b.get('DollarValue')) else None
        
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
                period_values[str(current_year)] = dollar_value

        processed_benefits.append({
            'description': b.get('BenefitDescription'),
            'additional_details': b.get('AdditionalDetails'),
            'category': category,
            'time_category': time_category,
            'dollar_value': dollar_value,
            'period_values': period_values,
            'enrollment_required': b.get('EnrollmentRequired', 'False').lower() == 'true',
            'effective_date': b.get('EffectiveDate'),
            'short_description': b.get('BenefitDescriptionShort') or b.get('BenefitDescription'), # Fallback
            'benefit_type': b.get('BenefitType'),
            'numeric_value': float(b.get('NumericValue')) if is_float(b.get('NumericValue')) else None,
            'numeric_type': b.get('NumericType'),
        })
    card_doc['benefits'] = processed_benefits
    
    # Earning Rates
    processed_rates = []
    for r in parsed_data['rates']:
        cat_raw = r.get('RateCategory')
        try:
            import ast
            if cat_raw.startswith('[') and cat_raw.endswith(']'):
                category = ast.literal_eval(cat_raw)
            else:
                category = [cat_raw]
        except:
             category = [cat_raw]
             
        processed_rates.append({
            'rate': float(r.get('EarningRate')) if is_float(r.get('EarningRate')) else 0.0,
            'currency': r.get('Currency'),
            'category': category,
            'details': r.get('AdditionalDetails'),
            'is_default': r.get('IsDefault', 'False').lower() == 'true'
        })
    card_doc['earning_rates'] = processed_rates
    
    # Signup Bonus
    s = parsed_data['signup']
    if s:
        card_doc['sign_up_bonus'] = {
            'value': int(s.get('SignUpBonusValue')) if s.get('SignUpBonusValue', '').isdigit() else 0,
            'currency': s.get('SignUpBonusType'), # Mapped from header 'SignUpBonusType' ? check file. File header says 'SignUpBonusType' column 6
            # In file: Vendor | CardName | EffectiveDate | Terms | SignUpBonusValue | SignUpBonusType | slug-id ...
            'terms': s.get('Terms'),
            'effective_date': s.get('EffectiveDate'),
            'spend_amount': int(s.get('SpendAmount')) if s.get('SpendAmount', '').isdigit() else 0,
            'duration_months': int(s.get('SignupDurationMonths')) if s.get('SignupDurationMonths', '').isdigit() else 0,
        }
    else:
        card_doc['sign_up_bonus'] = {}

    # Initial Rewards Summary Logic (simplified)
    # Sort simplified benefits to find top 2
    # Reuse logic from parse_benefits_csv if precise match needed, but here is a simple version:
    summary = ""
    # Find multipliers/cashback
    rates_summary = []
    for b in processed_benefits:
        if b.get('numeric_value'):
            if b.get('benefit_type') == 'Multiplier':
                rates_summary.append(f"{b['numeric_value']}x {b['short_description']}")
            elif b.get('benefit_type') == 'Cashback':
                rates_summary.append(f"{b['numeric_value']}% {b['short_description']}")
    
    if rates_summary:
        summary = ", ".join(rates_summary[:2])
    else:
        # Credits fall back
        credits = [b for b in processed_benefits if b.get('benefit_type') == 'Credit' and b.get('numeric_value')]
        if credits:
            credits.sort(key=lambda x: x['numeric_value'], reverse=True)
            top = credits[0]
            summary = f"${top['numeric_value']} {top['short_description']}"
        else:
             summary = "Various Benefits"
    card_doc['rewards_summary'] = summary
    
    return card_doc, parsed_data['category_mapping'], parsed_data['questions']

def is_float(s):
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

def generate_cards_from_files(directory):
    """
    Reads all .txt files in directory, parses them, and returns:
    - cards: list of card documents
    - categories: list of unique category objects (merged from all files)
    - questions: list of question objects
    """
    cards = []
    all_categories = {} # map Name -> Category Object (to deduplicate)
    all_questions = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return [], [], []

    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    print(f"Found {len(files)} update files in {directory}")

    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            raw_data = parse_update_file(filepath)
            card_doc, categories, questions = process_card_data(raw_data)
            
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
            
            # Collect questions
            if questions:
                all_questions.extend(questions)
                        
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()
            
    return cards, list(all_categories.values()), all_questions

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
