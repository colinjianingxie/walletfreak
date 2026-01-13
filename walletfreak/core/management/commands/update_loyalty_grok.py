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

    def handle(self, *args, **options):
        self.api_key = os.environ.get('GROK_API_KEY')
        if not self.api_key:
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

        if update_type in ['loyalty', 'all']:
            self.update_loyalty_programs()
        
        if update_type in ['transfers', 'all']:
            self.update_transfer_rules()

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
            "model": "grok-2-1212", # Using latest model
            "stream": False,
            "temperature": 0.1, # Low temp for factual data
            "search_parameters": {
                "mode": "on", 
                "sources": [{"type": "web"}],
                "return_citations": False,
                "max_search_results": 10
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
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
        - `partner_hotel_brand`: (String) Hotel brand (e.g. "Marriott") or null.
        - `currency_group`: (String) "avios" if the currency is commonly called Avios (BA, Qatar, Iberia, Finnair, Aer Lingus), otherwise null.

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

        **Schema for each transfer rule:**
        - `source_program_id`: (String) The ID of the bank as provided above (e.g. `chase_ur`, `amex_mr`).
        - `destination_program_id`: (String) The ID of the partner program. You MUST use IDs consistent with standard loyalty program IDs (e.g., `united_mileageplus`, `ba_avios`, `marriott_bonvoy`).
        - `ratio`: (Number) Transfer ratio (e.g. 1.0, 0.5, 2.0). 1.0 means 1:1.
        - `transfer_time`: (String) e.g., "Instant", "24 hours", "2 days".
        - `min_transfer_amount`: (Number) Usually 1000.
        - `transfer_increment`: (Number) Usually 1000.
        - `current_bonus`: (Object)
            - `is_active`: (Boolean)
            - `bonus_multiplier`: (Number) e.g. 1.25 for 25% bonus. or 1.0 if none.
            - `expiry_date`: (String YYYY-MM-DD or null).
        - `is_one_way`: (Boolean) true.

        **Output:**
        Return a single JSON list containing ALL transfer rules found for ALL source programs.
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
             for k, v in data.items():
                if isinstance(v, list):
                    data = v
                    break

        if not isinstance(data, list):
             self.stdout.write(self.style.ERROR("API returned invalid format (expected list)"))
             return

        for item in data:
            src = item.get('source_program_id')
            dst = item.get('destination_program_id')
            
            if not src or not dst:
                continue
                
            filename = f"{src}_to_{dst}.json"
            file_path = os.path.join(self.transfers_dir, filename)
            
            if not self.dry_run:
                with open(file_path, 'w') as f:
                    json.dump(item, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"Saved {filename}"))
