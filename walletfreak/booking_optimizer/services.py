import json
import os
import csv
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from core.services.amadeus_service import AmadeusService

DATA_DIR = '/Users/xie/Desktop/projects/walletfreak/walletfreak/walletfreak_data'

class HotelSearchService:
    def __init__(self):
        self.amadeus_service = AmadeusService()

    def load_hotel_mapping(self):
        """Loads partial hotel mapping from CSV."""
        # Use simple memoization or Django cache for file read if needed, but per-request is ok for now or class-level.
        # Ideally, we cache this.
        cached = cache.get('hotel_code_mapping')
        if cached:
            return cached

        mapping = {}
        path = os.path.join(DATA_DIR, 'hotel_code_mapping.csv')
        if os.path.exists(path):
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Chain Code']:
                        mapping[row['Chain Code']] = {
                            'chain_name': row['Chain Name'],
                            'program_id': row['Program ID'],
                            'program_name': row['Loyalty Program']
                        }
        
        # Cache for longer duration as file changes rarely
        cache.set('hotel_code_mapping', mapping, 86400)
        return mapping

    def get_brand_class(self, program_id):
        """Maps loyalty program to CSS class name for color bars."""
        if not program_id: return 'independent'
        if 'hyatt' in program_id: return 'hyatt'
        if 'hilton' in program_id: return 'hilton'
        if 'marriott' in program_id: return 'marriott'
        if 'ihg' in program_id: return 'ihg'
        return 'independent'

    def search_hotels(self, location_query, check_in_raw, check_out_raw, guests='1'):
        """
        Orchestrates the hotel search: cache lookup -> API call -> data processing.
        """
        hotels = []
        
        # Basic Date Validation
        if check_in_raw == check_out_raw: 
            try: 
                check_out_raw = (datetime.strptime(check_in_raw, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
            except: pass

        search_params = {
            'check_in': check_in_raw,
            'check_out': check_out_raw,
            'adults': guests
        }

        # Cache Key
        cache_key = f"hotel_search_{location_query}_{search_params['check_in']}_{search_params['check_out']}_{search_params['adults']}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data
        
        # Check API Creds
        if not (settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET):
            print("Amadeus credentials missing.")
            return []

        try:
            # Fetch from Amadeus
            api_results = self.amadeus_service.search_hotel_offers_by_city(location_query, **search_params)
            
            # Load Mapping
            hotel_mapping = self.load_hotel_mapping()
            
            for offer in api_results:
                try:
                    hotel_data = offer.get('hotel', {})
                    offers_data = offer.get('offers', [])
                    if not offers_data: continue
                    
                    price_obj = offers_data[0].get('price', {})
                    cash_price = float(price_obj.get('total', 0))
                    currency = price_obj.get('currency', 'USD')
                    
                    chain_code = hotel_data.get('chainCode', '')
                    mapped = hotel_mapping.get(chain_code, {})
                    
                    hotel_name = hotel_data.get('name', 'Unknown Hotel').title()
                    brand_name = mapped.get('chain_name', chain_code)
                    program_id = mapped.get('program_id', '')
                    program_name = mapped.get('program_name', '')
                    
                    # Mock Rating for demo stability
                    rating = 4.5 
                    
                    # ID for HTML
                    hid = hotel_data.get('hotelId', '0')
                    
                    # Construct Data Object for JSON flow
                    hotel_json_obj = {
                        'hotel_id': hid,
                        'name': hotel_name,
                        'location_code': hotel_data.get('cityCode', location_query.upper()),
                        'brand_name': brand_name,
                        'program_id': program_id,
                        'program_name': program_name,
                        'price': cash_price,
                        'currency': currency,
                        'rating': rating,
                        'chain_code': chain_code
                    }

                    hotels.append({
                        'id_safe': hid,
                        'name': hotel_name,
                        'location_text': f"{hotel_data.get('cityCode', 'ETH')} • {brand_name or 'Independent'}",
                        'price': cash_price,
                        'currency': currency,
                        'rating': rating,
                        'brand': brand_name,
                        'brand_class': self.get_brand_class(program_id),
                        'json_data': json.dumps(hotel_json_obj)
                    })

                except Exception as e:
                    print(f"Parse Error in search result: {e}")
                    continue
            
            # Cache results
            if hotels:
                cache.set(cache_key, hotels, 3600)
                
        except Exception as e:
            print(f"Amadeus Error: {e}")
            
        return hotels
