import os
import json
import requests
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Updates loyalty programs and transfer rules using Grok API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='all',
            help='Type of data to update: "loyalty", "transfers", or "all"'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving files'
        )
        parser.add_argument(
            '--fix-iata',
            action='store_true',
            help='Backfill missing IATA codes for non-airline programs'
        )
        parser.add_argument(
            '--fix-hotels',
            action='store_true',
            help='Backfill partner hotel brands as a list for airline programs'
        )

    def handle(self, *args, **options):
        self.api_key = os.environ.get('GROK_API_KEY')
        if not self.api_key:
            # allow fix-iata without api key? No, fix-hotels needs API.
            # but fix-iata technically didn't use API in the logic I wrote (it was heuristic/random).
            # But let's keep the check for simplified flow.
            self.stdout.write(self.style.ERROR("GROK_API_KEY not found in environment variables"))
            return

        update_type = options['type']
        self.dry_run = options['dry_run']
        
        self.data_dir = os.path.join(settings.BASE_DIR, 'walletfreak_data')
        self.loyalty_dir = os.path.join(self.data_dir, 'program_loyalty')
        self.transfers_dir = os.path.join(self.data_dir, 'transfer_rules')
        
        # Ensure directories exist
        if not os.path.exists(self.loyalty_dir): os.makedirs(self.loyalty_dir)
        if not os.path.exists(self.transfers_dir): os.makedirs(self.transfers_dir)

        if update_type in ['loyalty', 'all'] and not (options.get('fix_iata') or options.get('fix_hotels')):
            self.update_loyalty_programs()
        
        if update_type in ['transfers', 'all'] and not (options.get('fix_iata') or options.get('fix_hotels')):
            self.update_transfer_rules()
            
        if options.get('fix_iata'):
            self.fix_missing_iata_codes()
            
        if options.get('fix_hotels'):
            self.fix_hotel_partners()

    def call_grok_api(self, prompt):
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides JSON data for travel loyalty programs."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "model": "grok-4", # Updated to match update_cards_grok.py
            "stream": False,
            "temperature": 0.1, 
            "search_parameters": {
                "mode": "on", 
                "sources": [{"type": "web"}],
                "return_citations": False,
                "max_search_results": 10
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 404:
                self.stdout.write(self.style.ERROR(f"API 404 Not Found. URL: {url}"))
            
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean Markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"API Request Failed: {e}"))
            if 'response' in locals() and hasattr(response, 'text'):
                 self.stdout.write(self.style.ERROR(f"Response Body: {response.text}"))
            return None

    def update_loyalty_programs(self):
        self.stdout.write(self.style.HTTP_INFO("\n=== Updating Loyalty Programs ==="))
        
        # Comprehensive list mapped to IDs
        programs_map = {
            # Banks
            "amex_mr": "American Express Membership Rewards",
            "chase_ur": "Chase Ultimate Rewards",
            "cap1_miles": "Capital One Miles",
            "citi_ty": "Citi ThankYou Rewards",
            "bilt_rewards": "Bilt Rewards",
            "wells_fargo": "Wells Fargo Rewards",
            
            # Star Alliance
            "united_mileageplus": "United MileagePlus",
            "aeroplan": "Air Canada Aeroplan",
            "lifemiles": "Avianca LifeMiles",
            "turkish_miles_smiles": "Turkish Airlines Miles&Smiles",
            "krisflyer": "Singapore Airlines KrisFlyer",
            "miles_and_more": "Lufthansa Miles & More",
            "ana_mileage_club": "ANA Mileage Club",
            "royal_orchid_plus": "Thai Airways Royal Orchid Plus",
            "miles_and_go": "TAP Air Portugal Miles&Go",
            "infinity_mileagelands": "EVA Air Infinity MileageLands",
            "miles_plus_bonus": "Aegean Airlines Miles+Bonus",
            "connectmiles": "Copa Airlines ConnectMiles",
            "asiana_club": "Asiana Airlines Asiana Club",

            # Oneworld
            "american_aadvantage": "American Airlines AAdvantage",
            "atmos_rewards": "Atmos Rewards (Alaska + Hawaiian)",
            "ba_executive_club": "British Airways Executive Club",
            "qatar_privilege_club": "Qatar Airways Privilege Club",
            "iberia_plus": "Iberia Plus",
            "finnair_plus": "Finnair Plus",
            "aerclub": "Aer Lingus AerClub",
            "cathay": "Cathay (Asia Miles)",
            "jal_mileage_bank": "Japan Airlines Mileage Bank",
            "qantas_frequent_flyer": "Qantas Frequent Flyer",
            "enrich": "Malaysia Airlines Enrich",
            "safar_flyer": "Royal Air Maroc Safar Flyer",

            # SkyTeam
            "delta_skymiles": "Delta SkyMiles",
            "flying_blue": "Air France / KLM Flying Blue",
            "virgin_flying_club": "Virgin Atlantic Flying Club",
            "skypass": "Korean Air SKYPASS",
            "aeromexico_rewards": "Aeromexico Rewards",
            "eurobonus": "SAS EuroBonus",
            "eastern_miles": "China Eastern Eastern Miles",
            "volare": "ITA Airways Volare",
            "garudamiles": "Garuda Indonesia GarudaMiles",
            "lotusmiles": "Vietnam Airlines Lotusmiles",

            # Non-Aligned
            "southwest_rapid_rewards": "Southwest Rapid Rewards",
            "jetblue_trueblue": "JetBlue TrueBlue",
            "emirates_skywards": "Emirates Skywards",
            "etihad_guest": "Etihad Guest",
            "matmid": "El Al Matmid",
            "frontier_miles": "Frontier Airlines FRONTIER Miles",

            # Hotels
            "marriott_bonvoy": "Marriott Bonvoy",
            "hilton_honors": "Hilton Honors",
            "world_of_hyatt": "World of Hyatt",
            "ihg_one_rewards": "IHG One Rewards",
            "choice_privileges": "Choice Privileges",
            "wyndham_rewards": "Wyndham Rewards",
            "accor_all": "Accor Live Limitless",
            "sonesta_travel_pass": "Sonesta Travel Pass",
            "best_western_rewards": "Best Western Rewards",
            "i_prefer": "I Prefer Hotel Rewards",
            "gha_discovery": "GHA Discovery",
            "leaders_club": "Leading Hotels of the World Leaders Club"
        }
        
        prompt_programs_list = "\n".join([f"- ID: {pid}, Name: {name}" for pid, name in programs_map.items()])

        prompt = f"""
        I need to populate a database of travel loyalty programs.
        Populate JSON data for the following programs (use these EXACT IDs):
        
        {prompt_programs_list}

        **Schema per Object:**
        - `program_id`: (String) Use the provided ID exactly.
        - `program_name`: (String) Full name.
        - `type`: (String) One of: `bank`, `airline`, `hotel`.
        - `logo_url`: (String) Official logo URL (or null).
        - `valuation`: (Number) Approximate cents per point (cpp) value (e.g. 2.0, 1.2). Use reputable blogs (TPG, OMAAT) for valuation.
        - `iata_code`: (String) 2-letter code for airlines (e.g. "DL"), null for banks/hotels.
        - `alliance`: (String) Airline alliance (e.g. "Star Alliance", "Oneworld", "SkyTeam") or null.
        - `partner_hotel_brand`: (List of Strings) List of hotel brands this airline partners with for earning/status (e.g. ["Marriott", "Hyatt"]). Return empty list [] if none or for non-airlines.
        - `currency_group`: (String) "Avios", "Miles", or "Points" based on the currency name. Default to "Points" if unclear.

        **Output:**
        Return a single JSON list containing objects for ALL requested programs.
        """
        
        if self.dry_run:
            self.stdout.write(f"Would request: {len(programs_map)} programs")
            return

        self.stdout.write(f"Fetching data for {len(programs_map)} programs...")
        data = self.call_grok_api(prompt)
        
        if not data:
            self.stdout.write(self.style.ERROR("Failed to get loyalty data"))
            return

        if isinstance(data, dict): # Handle if LLM returns a wrapper dict
            # Try to find list values
            for k, v in data.items():
                if isinstance(v, list):
                    data = v
                    break
        
        if not isinstance(data, list):
             self.stdout.write(self.style.ERROR("API returned invalid format (expected list)"))
             return

        for item in data:
            pid = item.get('program_id')
            if not pid:
                # Fallback to name slug if LLM failed
                pid = slugify(item.get('program_name', 'unknown')).replace('-', '_')
                item['program_id'] = pid
            
            # Use pid from map if possible to match EXACTLY? 
            # The prompt asked for exact IDs, so we trust reasonable compliance.
            
            file_path = os.path.join(self.loyalty_dir, f"{pid}.json")
            
            if not self.dry_run:
                with open(file_path, 'w') as f:
                    json.dump(item, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"Saved {pid}.json"))

    def update_transfer_rules(self):
        self.stdout.write(self.style.HTTP_INFO("\n=== Updating Transfer Rules ==="))
        
        sources = {
            "amex_mr": "American Express Membership Rewards", 
            "chase_ur": "Chase Ultimate Rewards", 
            "cap1_miles": "Capital One Miles", 
            "citi_ty": "Citi ThankYou Rewards", 
            "bilt_rewards": "Bilt Rewards", 
            "wells_fargo": "Wells Fargo Rewards"
        }
        
        prompt = f"""
        I need to map out the transfer partners for major US credit card point programs.
        Find ALL active transfer partners for the following source programs:
        {json.dumps(sources, indent=2)}

        **Output Schema:**
        Return a JSON LIST of objects, where each object represents one Source Program and contains all its transfer rules.
        
        [
          {{
            "source_program_id": "amex_mr",
            "transfer_partners": [
              {{
                "destination_program_id": "delta_skymiles",
                "ratio": 1.0,
                "transfer_time": "Instant",
                "min_transfer_amount": 1000,
                "transfer_increment": 1000,
                "is_one_way": true,
                "current_bonus": {{
                   "is_active": false,
                   "bonus_multiplier": 1.0,
                   "expiry_date": null
                }}
              }},
              ...
            ]
          }},
          ...
        ]

        **Rules:**
        - `destination_program_id`: Use consistent IDs (e.g. `united_mileageplus`, `ba_executive_club`).
        - `ratio`: Number (1.0 for 1:1).
        """

        if self.dry_run:
            self.stdout.write("Would request transfer rules...")
            return

        self.stdout.write("Fetching transfer rules...")
        data = self.call_grok_api(prompt)
        
        if not data:
            self.stdout.write(self.style.ERROR("Failed to get transfer data"))
            return

        if isinstance(data, dict):
             # check if wrapped
             for k, v in data.items():
                if isinstance(v, list):
                    data = v
                    break

        if not isinstance(data, list):
             self.stdout.write(self.style.ERROR("API returned invalid format (expected list)"))
             return

        for item in data:
            src = item.get('source_program_id')
            partners = item.get('transfer_partners', [])
            
            if not src:
                continue
                
            filename = f"{src}.json"
            file_path = os.path.join(self.transfers_dir, filename)
            
            # Sort partners by ID for consistency
            partners.sort(key=lambda x: x.get('destination_program_id', ''))
            item['transfer_partners'] = partners
            
            if not self.dry_run:
                with open(file_path, 'w') as f:
                    json.dump(item, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"Saved {filename} with {len(partners)} partners"))

    def fix_missing_iata_codes(self):
        self.stdout.write(self.style.HTTP_INFO("\n=== Backfilling Missing IATA Codes ==="))
        
        files = [f for f in os.listdir(self.loyalty_dir) if f.endswith('.json')]
        existing_codes = set()
        programs_to_udpate = []
        
        # First pass: collect existing codes
        for fname in files:
            with open(os.path.join(self.loyalty_dir, fname), 'r') as f:
                data = json.load(f)
                code = data.get('iata_code')
                if code:
                    existing_codes.add(code.upper())
                else:
                    programs_to_udpate.append((fname, data))

        self.stdout.write(f"Found {len(existing_codes)} existing IATA codes.")
        self.stdout.write(f"Found {len(programs_to_udpate)} programs needing codes.")
        
        for fname, data in programs_to_udpate:
            program_name = data.get('program_name', 'Unknown')
            pid = data.get('program_id', fname.replace('.json', ''))
            
            # Generate code logic
            candidate = None
            
            # Strategy 1: First letter of first two words
            parts = program_name.split()
            if len(parts) >= 2:
                candidate = (parts[0][0] + parts[1][0]).upper()
            
            # Strategy 2: First two letters of first word (if still collision or < 2 words)
            if not candidate or candidate in existing_codes:
                candidate = program_name[:2].upper()
            
            # Strategy 3: First letter + Second letter of ID
            if candidate in existing_codes:
                 candidate = pid[:2].upper()

            # Strategy 4: Brute force variations
            if candidate in existing_codes:
                # Try combinations of letters from name
                name_clean = program_name.replace(' ', '').upper()
                found = False
                for i in range(len(name_clean)):
                    for j in range(i + 1, len(name_clean)):
                        test = name_clean[i] + name_clean[j]
                        if test not in existing_codes:
                            candidate = test
                            found = True
                            break
                    if found: break
            
            # Last resort: Random letters (shouldn't happen with 2 chars and only 50 programs, 26*26=676 combos)
            import random
            import string
            while candidate in existing_codes:
                candidate = ''.join(random.choices(string.ascii_uppercase, k=2))

            existing_codes.add(candidate)
            data['iata_code'] = candidate
            
            self.stdout.write(f"Assigned {candidate} to {program_name} ({fname})")
            
            if not self.dry_run:
                with open(os.path.join(self.loyalty_dir, fname), 'w') as f:
                    json.dump(data, f, indent=2)

    def fix_hotel_partners(self):
        self.stdout.write(self.style.HTTP_INFO("\n=== Backfilling Hotel Partners ==="))
        
        files = [f for f in sorted(os.listdir(self.loyalty_dir)) if f.endswith('.json')]
        airlines = []
        
        # Load all programs
        for fname in files:
            with open(os.path.join(self.loyalty_dir, fname), 'r') as f:
                data = json.load(f)
                if data.get('type') == 'airline':
                    airlines.append((fname, data))

        if not airlines:
            self.stdout.write("No airlines found.")
            return

        self.stdout.write(f"Refining hotel partners for {len(airlines)} airlines...")

        # Batch them to save API calls? No, specific search per airline is safer for "partner_hotel_brand" specificity
        # Or batch of ~10. Let's do batch of 10.
        
        batch_size = 15
        for i in range(0, len(airlines), batch_size):
            batch = airlines[i:i + batch_size]
            program_list = "\n".join([f"- {d.get('program_name')} (ID: {d.get('program_id')})" for _, d in batch])
            
            prompt = f"""
            I am updating my database of airline loyalty programs.
            For the following airlines, list the **Hotel Loyalty Programs** they partner with for **hotel point transfers to the airline** or **rewards/status matching**.
            
            Airlines:
            {program_list}

            return a JSON list of objects:
            [
              {{
                "program_id": "airline_program_id",
                "partner_hotel_brand": ["Marriott", "Hyatt", "Hilton"] (List of strings, empty if none known)
              }}
            ]
            """
            
            if self.dry_run:
                self.stdout.write(f"Would request updates for batch {i//batch_size + 1}")
                continue

            self.stdout.write(f"Fetching hotel partners for batch {i//batch_size + 1}...")
            result = self.call_grok_api(prompt)
            
            if not result or not isinstance(result, list):
                self.stdout.write(self.style.ERROR("Failed to get response for hotel partners batch"))
                continue
            
            # Map results back
            result_map = {r.get('program_id'): r.get('partner_hotel_brand', []) for r in result}
            
            for fname, data in batch:
                pid = data.get('program_id')
                partners = result_map.get(pid)
                
                # Check for updates
                # Ensure partner_hotel_brand is a list
                current_partners = data.get('partner_hotel_brand')
                
                # Normalize current to list if it was a string
                if isinstance(current_partners, str):
                    if current_partners:
                        current_partners = [current_partners]
                    else:
                        current_partners = []
                elif current_partners is None:
                    current_partners = []
                
                if partners is not None:
                     # Merge or replace? Replace with better LLM data usually better.
                     # Remove duplicates
                     final_list = sorted(list(set(partners)))
                     data['partner_hotel_brand'] = final_list
                     self.stdout.write(f"Updated {data.get('program_name')}: {final_list}")
                     
                     with open(os.path.join(self.loyalty_dir, fname), 'w') as f:
                        json.dump(data, f, indent=2)
