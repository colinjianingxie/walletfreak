
import os
import json
import glob

import argparse

def extract_program_ids():
    parser = argparse.ArgumentParser(description='Extract loyalty program IDs.')
    parser.add_argument('--type', choices=['airline', 'hotel', 'bank', 'other'], help='Filter by program type (e.g. airline, hotel)')
    args = parser.parse_args()

    directory = '/Users/xie/Desktop/projects/walletfreak/walletfreak/walletfreak_data/program_loyalty'
    pattern = os.path.join(directory, '*.json')
    files = glob.glob(pattern)
    
    program_data = []
    
    print(f"Found {len(files)} files in {directory}...")
    
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if 'program_id' in data:
                    p_id = data['program_id']
                    p_name = data.get('program_name', 'Unknown')
                    p_type = data.get('type', 'unknown')
                    
                    if args.type and args.type.lower() != p_type.lower():
                        continue
                        
                    program_data.append((p_id, p_name, p_type))
                else:
                    print(f"Warning: 'program_id' not found in {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error reading {os.path.basename(file_path)}: {e}")
            
    # Sort by ID
    program_data.sort(key=lambda x: x[0])
    
    print(f"\n--- Extracted Program Data (ID: Name) [Filter: {args.type if args.type else 'All'}] ---")
    for p_id, p_name, p_type in program_data:
        print(f"{p_id}: {p_name} ({p_type})")
        
    print(f"\nTotal Programs: {len(program_data)}")

if __name__ == "__main__":
    extract_program_ids()
