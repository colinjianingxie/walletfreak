
import os
import csv
import json
import ast

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATES_DIR_NAME = 'walletfreak_credit_cards'
UPDATES_DIR = os.path.join(BASE_DIR, UPDATES_DIR_NAME)

FILES = {
    'card_info': os.path.join(BASE_DIR, 'default_credit_cards.csv'),
    'benefits': os.path.join(BASE_DIR, 'default_card_benefits.csv'),
    'rates': os.path.join(BASE_DIR, 'default_rates.csv'),
    'signup': os.path.join(BASE_DIR, 'default_signup.csv'),
    'questions': os.path.join(BASE_DIR, 'calculators/credit_card_questions.csv'),
}
MAPPING_FILE = os.path.join(BASE_DIR, 'default_category_mapping.json')

def load_csv_data(filepath):
    """Load CSV data, returning headers and list of rows."""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return [], []
    
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        return reader.fieldnames, list(reader)

def load_json_data(filepath):
    """Load JSON data."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_csv_section(headers, rows):
    """Format rows into pipe-delimited string with header."""
    if not headers:
        return ""
    
    # Header line
    lines = [" | ".join(headers)]
    
    # Data lines
    for row in rows:
        values = [str(row.get(h, '')) for h in headers]
        lines.append(" | ".join(values))
        
    return "\n".join(lines)

def extract_categories(slug_data):
    """Extract all unique categories from benefits and rates."""
    categories = set()
    
    # 1. Benefits (BenefitCategory column, comma-separated)
    for row in slug_data.get('benefits', []):
        cat_str = row.get('BenefitCategory', '')
        if cat_str:
            # Handle comma separation
            cats = [c.strip() for c in cat_str.split(',') if c.strip()]
            categories.update(cats)
            
    # 2. Rates (RateCategory column, JSON list string or list)
    for row in slug_data.get('rates', []):
        cat_str = row.get('RateCategory', '')
        if cat_str:
            try:
                # Could be a string rep of a list "['a', 'b']"
                # Use ast.literal_eval for safety if it looks like python list, or json.loads
                # default_rates.csv uses "['Amazon']" which is valid python list repr (single quotes) 
                # but NOT valid JSON (double quotes required). `ast.literal_eval` handles both usually.
                # However, if it's already a list object (not expected from CSV reader), handle that.
                if cat_str.startswith('[') and cat_str.endswith(']'):
                    cats = ast.literal_eval(cat_str)
                    if isinstance(cats, list):
                        categories.update([str(c) for c in cats])
                else:
                    # Maybe just a string?
                    categories.add(cat_str.strip())
            except (ValueError, SyntaxError):
                # Fallback, just treat as string if parse fails
                categories.add(cat_str.strip())
                
    return categories

def filter_category_mapping(all_mappings, used_categories):
    """
    Filter the full mapping to only include categories present in used_categories.
    Returns a list of dicts with the same structure but filtered CategoryNameDetailed.
    """
    filtered_output = []
    
    # Pre-process mapping for easy lookup or iteration
    # Iterate over headers (CategoryName groups)
    for group in all_mappings:
        group_name = group.get('CategoryName')
        icon = group.get('Icon')
        detailed = group.get('CategoryNameDetailed', [])
        
        # Find intersection
        matched_detailed = [d for d in detailed if d in used_categories]
        
        if matched_detailed:
            filtered_output.append({
                "CategoryName": group_name,
                "Icon": icon,
                "CategoryNameDetailed": matched_detailed
            })
            
    return filtered_output

def populate_files():
    """Read all data and populate slug files."""
    print("Loading data...")
    
    # Load all CSV datasets
    data_cache = {}
    for key, path in FILES.items():
        headers, rows = load_csv_data(path)
        data_cache[key] = {
            'headers': headers,
            'rows': rows
        }
    
    # Load mapping
    full_mapping = load_json_data(MAPPING_FILE)
    
    # Get all slugs from card_info
    slugs = set()
    card_rows = data_cache['card_info']['rows']
    for row in card_rows:
        if row.get('slug-id'):
            slugs.add(row['slug-id'])
            
    print(f"Found {len(slugs)} cards.")
    
    if not os.path.exists(UPDATES_DIR):
        os.makedirs(UPDATES_DIR)

    for slug in slugs:
        filename = f"{slug}.txt"
        filepath = os.path.join(UPDATES_DIR, filename)
        
        # Filter rows for this slug
        slug_data = {}
        for key in FILES.keys():
            all_rows = data_cache[key]['rows']
            slug_rows = [r for r in all_rows if r.get('slug-id') == slug]
            slug_data[key] = slug_rows
            
        # Extract categories
        used_cats = extract_categories(slug_data)
        
        # Filter mapping
        filtered_mapping = filter_category_mapping(full_mapping, used_cats)
        mapping_json_str = json.dumps(filtered_mapping, indent=4)
        
        # Construct content sections
        sections = []
        
        # 1. Card Info
        sections.append(format_csv_section(data_cache['card_info']['headers'], slug_data['card_info']))
        
        # 2. Benefits
        sections.append(format_csv_section(data_cache['benefits']['headers'], slug_data['benefits']))
        
        # 3. Rates
        sections.append(format_csv_section(data_cache['rates']['headers'], slug_data['rates']))
        
        # 4. Signup
        sections.append(format_csv_section(data_cache['signup']['headers'], slug_data['signup']))
        
        # 5. Questions
        sections.append(format_csv_section(data_cache['questions']['headers'], slug_data['questions']))
        
        # 6. Category Mapping
        sections.append(mapping_json_str)
        
        # Join with separator
        full_content = "\n---\n".join(sections)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
    print(f"Populated {len(slugs)} files in {UPDATES_DIR_NAME}/")

def validate_csv_section(section_name, lines, file_slug):
    """Validate a CSV section."""
    lines = [l for l in lines if l.strip()]
    if not lines:
        return True 
        
    header = lines[0].strip()
    headers = [h.strip() for h in header.split('|')]
    headers = [h.strip() for h in headers]
    
    num_cols = len(headers)
    
    issues = []
    
    for i, line in enumerate(lines[1:], start=2): 
        row = line.strip()
        cols = [c.strip() for c in row.split('|')]
        
        if len(cols) != num_cols:
             issues.append(f"Line {i}: Column count mismatch. Expected {num_cols}, got {len(cols)}.")
        
        if 'slug-id' in headers:
            try:
                slug_idx = headers.index('slug-id')
                row_slug = cols[slug_idx] if len(cols) > slug_idx else None
                if row_slug and row_slug != file_slug:
                     issues.append(f"Line {i}: slug-id '{row_slug}' does not match filename slug '{file_slug}'.")
            except ValueError:
                pass 

    if issues:
        print(f"  [{file_slug}.txt Error] {section_name}:")
        for issue in issues:
            print(f"    - {issue}")
        return False
    return True

def validate_updates():
    """Iterate through all .txt files and validate formats."""
    files = [f for f in os.listdir(UPDATES_DIR) if f.endswith('.txt')]
    print(f"\nValidating {len(files)} files...")

    for filename in files:
        filepath = os.path.join(UPDATES_DIR, filename)
        file_slug = filename.replace('.txt', '')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            continue 

        sections = content.split('\n---\n')
        
        if len(sections) != 6:
             pass # warning optional
        
        section_names = [
            "Card Info",
            "Benefits",
            "Rates",
            "Signup Bonus",
            "Questions",
            "Category Mapping"
        ]
        
        for i, section_content in enumerate(sections):
            if i >= len(section_names):
                continue
            
            name = section_names[i]
            
            if i == 5: # Category Mapping
                try:
                    json_str = section_content.strip()
                    if json_str:
                        json.loads(json_str)
                except json.JSONDecodeError as e:
                     print(f"[{filename}] Error in {name}: Invalid JSON - {e}")
            else:
                 lines = section_content.strip().split('\n')
                 validate_csv_section(name, lines, file_slug)

if __name__ == "__main__":
    populate_files()
    validate_updates()
