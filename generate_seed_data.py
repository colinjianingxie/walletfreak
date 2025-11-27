import csv
import re

def parse_fee(fee_str):
    if not fee_str:
        return 0
    # Extract number from string like "$95" or "$0 intro, then $95"
    # If multiple numbers, usually the first one or the "then" one?
    # For "$0 intro, then $95", the annual fee is effectively $95 long term.
    # For "$0", it's 0.
    # Let's look for the last number if there are multiple, assuming "intro then X".
    # Or just regex for `\$(\d+)` and take the max?
    # "$0 intro, then $95" -> 0 and 95. Max is 95.
    # "$0" -> 0.
    # "$325" -> 325.
    matches = re.findall(r'\$(\d+(?:,\d{3})*)', fee_str)
    if not matches:
        return 0
    vals = [int(m.replace(',', '')) for m in matches]
    return max(vals)

def parse_benefits_from_row(row):
    benefits = []
    
    # Map columns to reset periods
    col_map = {
        'Permanent Benefits': 'annual', # Treating permanent as annual/ongoing
        'Monthly Reset Benefits': 'monthly',
        'Quarterly Reset Benefits': 'quarterly',
        'Semi-annually Reset Benefits': 'semi-annual',
        'Annual Calendar Reset Benefits': 'calendar_year',
        'Anniversary Year Reset Benefits': 'anniversary',
        'Temporary / Intro / Other Benefits': 'intro'
    }

    for col_name, reset_period in col_map.items():
        text = row.get(col_name, '').strip()
        if not text:
            continue
            
        # Split by newlines or bullets
        # The text often starts with "- ".
        # We can split by "\n- " or just "\n" and clean up.
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('- '):
                line = line[2:]
            elif line.startswith('• '):
                line = line[2:]
                
            # Determine type and amount
            b_type = 'credit' if '$' in line else 'perk'
            amount = 0
            if '$' in line:
                try:
                    match = re.search(r'\$(\d+(?:,\d{3})*)', line)
                    if match:
                        amount = int(match.group(1).replace(',', ''))
                except:
                    pass
            
            benefits.append({
                'id': f'benefit_{len(benefits)}',
                'name': line,
                'description': line,
                'type': b_type,
                'amount': amount,
                'reset_period': reset_period
            })
            
    return benefits

cards_data = []
with open('walletfreak/cards_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        card = {
            'name': row['Card Name'].strip(),
            'issuer': row['Provider'].strip(),
            'annual_fee': parse_fee(row['Annual Fee']),
            'rewards_structure': {'details': row['Permanent Benefits'].strip()},
            'benefits': parse_benefits_from_row(row)
        }
        cards_data.append(card)

# Write to file
import json
with open('walletfreak/core/management/commands/cards_seed_data.py', 'w') as f:
    f.write("cards_data = " + json.dumps(cards_data, indent=4))
