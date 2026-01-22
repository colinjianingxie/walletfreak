
import os
import django
import logging

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'walletfreak.settings')
django.setup()

from core.services.amadeus_service import AmadeusService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('core.services.amadeus_service')
logger.setLevel(logging.INFO)

def reproduce():
    service = AmadeusService()
    
    print("\n--- Scenario 1: Cast adults to int ---")
    # adults=2 (int), maxPrice="2000" (string)
    params = {
        'adults': 2, 
        'maxPrice': '2000',
    }
    
    results = service.search_hotel_offers_by_city(
        location_query='NYC',
        check_in='2026-01-22',
        check_out='2026-01-30',
        **params
    )
    print(f"Results S1: {len(results)}")

    print("\n--- Scenario 2: Remove priceRange and use string adults ---")
    # adults="2" (str), NO maxPrice
    params = {
        'adults': '2',
    }
    results = service.search_hotel_offers_by_city(
        location_query='NYC',
        check_in='2026-01-22',
        check_out='2026-01-30',
        **params
    )
    print(f"Results S2: {len(results)}")

    print("\n--- Scenario 3: Cast adults to int AND remove priceRange ---")
    # adults=2 (int), NO maxPrice
    params = {
        'adults': 2,
    }
    results = service.search_hotel_offers_by_city(
        location_query='NYC',
        check_in='2026-01-22',
        check_out='2026-01-30',
        **params
    )
    print(f"Results S3: {len(results)}")

if __name__ == "__main__":
    reproduce()
