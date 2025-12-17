import csv
import os

def extract_slugs(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            # The CSV uses '|' as a delimiter based on inspection
            reader = csv.DictReader(csvfile, delimiter='|')
            
            slugs = []
            for row in reader:
                if 'slug-id' in row:
                    slugs.append(row['slug-id'])
                else:
                    print("Warning: 'slug-id' column not found in a row")

            # Print all slugs
            for slug in slugs:
                print(slug)
            
            print(f"\nTotal slugs found: {len(slugs)}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    csv_file_path = '/Users/xie/Desktop/projects/walletfreak/walletfreak/default_credit_cards.csv'
    extract_slugs(csv_file_path)
