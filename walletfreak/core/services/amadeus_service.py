from amadeus import Client, ResponseError, Location
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class AmadeusService:
    def __init__(self):
        # Using 'test' environment for Sandbox keys.
        # ssl=False is added to bypass potential local certificate issues (NetworkError).
        self.client = Client(
            client_id=settings.AMADEUS_CLIENT_ID,
            client_secret=settings.AMADEUS_CLIENT_SECRET,
            hostname='test'
        )

    def resolve_city_code(self, keyword: str):
        """
        Resolve a city name to an IATA city code.
        """
        try:
            response = self.client.reference_data.locations.get(
                keyword=keyword,
                subType=Location.CITY
            )
            if response.data:
                # Return the first matching city code
                return response.data[0]['iataCode']
            return None
        except ResponseError as error:
            logger.error(f"Amadeus API Error (City Search): {repr(error)}")
            if hasattr(error, 'response'):
                logger.error(f"Response status: {error.response.status_code}")
                logger.error(f"Response body: {error.response.body}")
            return None

    def search_hotels_by_city(self, city_code: str, **kwargs):
        """
        Search for hotels in a specific city with optional filters.
        Supported kwargs:
        - radius: int
        - radiusUnit: str ('KM' or 'MILE')
        - chainCodes: str (comma separated)
        - amenities: str (comma separated)
        - ratings: str (comma separated)
        - hotelSource: str ('BEDBANK', 'DIRECTCHAIN', 'ALL')
        """
        try:
            # Prepare parameters
            cparams = {'cityCode': city_code}
            
            # Map valid parameters
            valid_params = ['radius', 'radiusUnit', 'chainCodes', 'amenities', 'ratings', 'hotelSource']
            for p in valid_params:
                if kwargs.get(p):
                    cparams[p] = kwargs[p]

            # Use 'reference-data/locations/hotels/by-city' which requires a city code
            # We unpack cparams into the get call
            response = self.client.reference_data.locations.hotels.by_city.get(**cparams)
            return response.data
        except ResponseError as error:
            logger.error(f"Amadeus API Error (Hotel Search): {repr(error)}")
            if hasattr(error, 'response'):
                logger.error(f"Response status: {error.response.status_code}")
                logger.error(f"Response body: {error.response.body}")
            return []

    def get_hotel_offers(self, hotel_ids: list):
        """
        Get offers for specific hotels.
        """
        try:
            # Limit to a reasonable number because API has limits on number of IDs
            # 50 is often the limit, sometimes less depending on the specific endpoint version
            ids_str = ",".join(hotel_ids[:20]) 
            if not ids_str:
                return []
                
            response = self.client.shopping.hotel_offers.get(hotelIds=ids_str)
            return response.data
        except ResponseError as error:
            logger.error(f"Amadeus API Error (Offers): {repr(error)}")
            if hasattr(error, 'response'):
                logger.error(f"Response status: {error.response.status_code}")
                logger.error(f"Response body: {error.response.body}")
            return []
            
    def search_hotel_offers_by_city(self, location_query: str, check_in: str = None, check_out: str = None, **kwargs):
        """
        Combined workflow: Resolve City -> Find hotels in city -> Get offers
        (Note: hotel_offers_search requires hotelIds in this environment, not just cityCode)
        Supported kwargs are passed to search_hotels_by_city
        """
        # 1. Resolve City Code
        city_code = location_query.upper()
        if len(city_code) != 3:
            city_code = self.resolve_city_code(location_query)
        
        if not city_code:
            logger.warning(f"Could not resolve city code for query: {location_query}")
            return []

        # 2. Find Hotel IDs in City with Filters
        hotels = self.search_hotels_by_city(city_code, **kwargs)
        if not hotels:
            return []
            
        # Get list of hotel IDs (limit to 20 to avoid URL length/rate limits)
        hotel_ids = [h['hotelId'] for h in hotels]
        if not hotel_ids:
            return []

        # 3. Call Hotel Offers Search API with IDs
        try:
            # Default to a future date if not provided
            if not check_in:
                check_in = '2026-02-01'
            if not check_out:
                check_out = '2026-02-03'

            ids_str = ",".join(hotel_ids[:20])
            
            # Handle Max Price
            search_params = {
                'hotelIds': ids_str,
                'checkInDate': check_in,
                'checkOutDate': check_out,
                'adults': int(kwargs.get('adults', 2)), # Ensure int
                'roomQuantity': 1,
                'bestRateOnly': True
            }
            
            if kwargs.get('maxPrice'):
                # Format: min-max, e.g. "1-500"
                # Amadeus priceRange requires a currency to be well-defined or it may error with INVALID FORMAT
                # We default to USD for now as the UI shows $
                search_params['priceRange'] = f"1-{kwargs.get('maxPrice')}"
                search_params['currency'] = 'USD'

            response = self.client.shopping.hotel_offers_search.get(**search_params)
            return response.data
        except ResponseError as error:
            logger.error(f"Amadeus API Error (Offers Search): {repr(error)}")
            if hasattr(error, 'response'):
                logger.error(f"Response status: {error.response.status_code}")
                # Log the body to see why 400
                logger.error(f"Response body: {error.response.body}")
            return []

    def get_hotel_sentiments(self, hotel_ids: list):
        """
        Get sentiment analysis for a list of hotel IDs.
        Ref: https://test.api.amadeus.com/v2/e-reputation/hotel-sentiments
        """
        try:
             # Limit to 10 IDs as per API best practices/limitations
            ids_str = ",".join(hotel_ids[:10])
            if not ids_str:
                return []
                
            response = self.client.e_reputation.hotel_sentiments.get(hotelIds=ids_str)
            return response.data or []
        except ResponseError as error:
            logger.error(f"Amadeus API Error (Sentiments): {repr(error)}")
            # Sentiment API might not be available for all hotels or might return 404 for some.
            # We fail gracefully.
            return []
