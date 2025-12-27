import os

def extract_slugs(directory):
    if not os.path.exists(directory):
        print(f"Error: Directory not found at {directory}")
        return

    slugs = []

    files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    print(f"Scanning {len(files)} files in {directory}...\n")

    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # Read first few lines to get header and first data row
                lines = f.readlines()
                
                # Assume standard format:
                # Line 0: Header (Vendor | CardName | ... | slug-id | ...)
                # Line 1: Data
                
                if len(lines) < 2:
                    print(f"Warning: {filename} is empty or too short")
                    continue
                
                header_line = lines[0].strip()
                data_line = lines[1].strip()
                
                headers = [h.strip() for h in header_line.split('|')]
                values = [v.strip() for v in data_line.split('|')]
                
                if 'slug-id' in headers:
                    idx = headers.index('slug-id')
                    if idx < len(values):
                        slug = values[idx]
                        if slug:
                            slugs.append(slug)
                        else:
                            print(f"Warning: Empty slug-id in {filename}")
                    else:
                         print(f"Warning: Value missing for slug-id in {filename}")
                else:
                    print(f"Warning: 'slug-id' column not found in {filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Sort and Print
    slugs.sort()
    for slug in slugs:
        print(slug)
    
    print(f"\nTotal slugs found: {len(slugs)}")

if __name__ == "__main__":
    # directory relative to this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cards_dir = os.path.join(base_dir, 'walletfreak_credit_cards')
    extract_slugs(cards_dir)
