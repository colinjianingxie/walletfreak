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
    # and credit cards dir is 'walletfreak/walletfreak/walletfreak_credit_cards'
    # Check if BASE_DIR is project root or app root. Usually BASE_DIR is project root.
    # Let's try to find it relative to manage.py which is usually at BASE_DIR.
    
    cards_dir = os.path.join(settings.BASE_DIR, 'walletfreak_credit_cards')
    
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
