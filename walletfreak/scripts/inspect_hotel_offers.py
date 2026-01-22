import os
import sys
import logging
import json
from amadeus import Client, ResponseError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("amadeus_debug")

# Load env vars manually for script or assume they are in env
client_id = os.environ.get('AMADEUS_CLIENT_ID')
client_secret = os.environ.get('AMADEUS_CLIENT_SECRET')

if not client_id or not client_secret:
    print("❌ Missing API Keys in environment variables.")
    sys.exit(1)

amadeus = Client(
    client_id=client_id,
    client_secret=client_secret,
    hostname='test'
)

try:
    print("1. Searching for hotels in PAR (Paris)...")
    # Step 1: Get Hotel IDs
    hotels_response = amadeus.reference_data.locations.hotels.by_city.get(cityCode='PAR')
    
    if not hotels_response.data:
        print("⚠️ No hotels found in PAR.")
        sys.exit(0)
        
    print(f"✅ Found {len(hotels_response.data)} hotels.")
    
    # Step 2: Get Offers for the first 5 hotels
    hotel_ids = [h['hotelId'] for h in hotels_response.data[:5]]
    print(f"2. Fetching offers for IDs: {hotel_ids}")
    
    offers_response = amadeus.shopping.hotel_offers_search.get(hotelIds=",".join(hotel_ids))
    
    if offers_response.data:
        print("✅ Found offers!")
        first_offer = offers_response.data[0]
        print(json.dumps(first_offer, indent=2))
    else:
        print("⚠️ No offers found for these hotels.")

except ResponseError as error:
    print(f"❌ Error: {error}")
    if hasattr(error, 'response'):
        print(f"Status: {error.response.status_code}")
        print(error.response.body)
