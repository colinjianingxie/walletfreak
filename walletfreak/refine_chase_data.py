
import json
import re

def refine_chase_data():
    input_path = 'walletfreak_data/chase_hotels/chase_hotels_data.json'
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Loaded {len(data)} hotels.")
        
        updated_count = 0
        
        for hotel in data:
            # Update Type
            hotel['type'] = "The Edit"
            
            # Parse Address
            raw_addr = hotel.get('address', '')
            if raw_addr:
                parts = [p.strip() for p in raw_addr.split(',')]
                
                # Default values
                addr_line = raw_addr
                city = ""
                state = ""
                zip_code = ""
                country = hotel.get('country', '')
                
                # Heuristic parsing based on user example: "1170 Broadway, New York, NY 10001, United States"
                # Pattern: [Address Line], [City], [State Zip], [Country]
                # OR [Address], [City], [Country]
                
                if len(parts) >= 3:
                    # Attempt to extract country from last part if it matches
                    if parts[-1].lower() == country.lower() or parts[-1].lower() in ['united states', 'usa', 'us']:
                        # Last part is country
                        pass
                    
                    # Try to parse "NY 10001" style from second to last
                    state_zip_part = parts[-2]
                    # Regex for State Zip (2 chars + space + digits)
                    match = re.search(r'([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', state_zip_part)
                    if match:
                        state = match.group(1)
                        zip_code = match.group(2)
                        city = parts[-3]
                        addr_line = ", ".join(parts[:-3])
                    else:
                        # Fallback for international or non-standard US
                        # Just take first part as address line, rest as city? 
                        # This is very loose. Let's aim for the specific US format requested first.
                        addr_line = parts[0]
                        city = parts[1] if len(parts) > 1 else ""
                        
                hotel['address_line'] = addr_line
                hotel['city'] = city
                hotel['state'] = state
                hotel['zip_code'] = zip_code
                # Country is already there or we leave it
            
            updated_count += 1
            
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        print(f"Successfully refined {updated_count} hotels.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    refine_chase_data()
