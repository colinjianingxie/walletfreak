import os
import json
from django.conf import settings

def get_all_card_vendors():
    """
    Reads all JSON files in the 'walletfreak_credit_cards' directory 
    and returns a sorted list of unique Vendors.
    """
    vendors = set()
    
    # Path to credit cards directory relative to project root
    # Assuming standard django layout where settings.BASE_DIR is 'walletfreak/walletfreak'
    cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'master_cards')
    
    if not os.path.exists(cards_dir):
        # Fallback for different project structures or if dir is missing
        print(f"Warning: Credit cards directory not found at {cards_dir}")
        return []

    try:
        for filename in os.listdir(cards_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(cards_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        vendor = data.get('Vendor')
                        if vendor:
                            vendors.add(vendor)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {filename}")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
    except Exception as e:
        print(f"Error accessing directory {cards_dir}: {e}")
        return []

    return sorted(list(vendors))
