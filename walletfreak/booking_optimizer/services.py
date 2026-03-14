import json
import os
import csv
import requests
from django.conf import settings
from django.core.cache import cache
from core.services import db
from core.services.google_places_service import GooglePlacesService
from .premium_programs import match_hotel_to_programs

DATA_DIR = os.path.join(settings.BASE_DIR, 'walletfreak_data')


def get_serpapi_key():
    return os.environ.get('SERPAPI_KEY', '')

# Brand keywords → loyalty program mapping
BRAND_KEYWORDS = {
    'hyatt': {'chain_name': 'Hyatt', 'program_id': 'world_of_hyatt', 'program_name': 'World of Hyatt'},
    'park hyatt': {'chain_name': 'Hyatt', 'program_id': 'world_of_hyatt', 'program_name': 'World of Hyatt'},
    'andaz': {'chain_name': 'Hyatt', 'program_id': 'world_of_hyatt', 'program_name': 'World of Hyatt'},
    'thompson': {'chain_name': 'Hyatt', 'program_id': 'world_of_hyatt', 'program_name': 'World of Hyatt'},
    'alila': {'chain_name': 'Hyatt', 'program_id': 'world_of_hyatt', 'program_name': 'World of Hyatt'},
    'hilton': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'waldorf': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'conrad': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'doubletree': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'hampton': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'embassy suites': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'curio': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'canopy': {'chain_name': 'Hilton', 'program_id': 'hilton_honors', 'program_name': 'Hilton Honors'},
    'marriott': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'sheraton': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'westin': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'ritz-carlton': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'ritz carlton': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'st. regis': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'w hotel': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'courtyard': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'fairfield': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'residence inn': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'le meridien': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'edition': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'jw marriott': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'autograph': {'chain_name': 'Marriott', 'program_id': 'marriott_bonvoy', 'program_name': 'Marriott Bonvoy'},
    'ihg': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'intercontinental': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'holiday inn': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'crowne plaza': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'kimpton': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'indigo': {'chain_name': 'IHG', 'program_id': 'ihg_rewards', 'program_name': 'IHG One Rewards'},
    'wyndham': {'chain_name': 'Wyndham', 'program_id': 'wyndham_rewards', 'program_name': 'Wyndham Rewards'},
    'choice': {'chain_name': 'Choice', 'program_id': 'choice_privileges', 'program_name': 'Choice Privileges'},
    'best western': {'chain_name': 'Best Western', 'program_id': 'best_western_rewards', 'program_name': 'Best Western Rewards'},
    'four seasons': {'chain_name': 'Four Seasons', 'program_id': '', 'program_name': ''},
    'mandarin oriental': {'chain_name': 'Mandarin Oriental', 'program_id': '', 'program_name': ''},
}

# Price level mapping (Google Places uses enum strings)
PRICE_LEVEL_MAP = {
    'PRICE_LEVEL_FREE': 0,
    'PRICE_LEVEL_INEXPENSIVE': 1,
    'PRICE_LEVEL_MODERATE': 2,
    'PRICE_LEVEL_EXPENSIVE': 3,
    'PRICE_LEVEL_VERY_EXPENSIVE': 4,
}


class HotelSearchService:
    def __init__(self):
        self.places_service = GooglePlacesService()

    def load_hotel_mapping(self):
        """Loads partial hotel mapping from CSV (kept for chain code lookups)."""
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

        cache.set('hotel_code_mapping', mapping, 86400)
        return mapping

    def get_brand_class(self, program_id):
        """Maps loyalty program to CSS/style class name for color bars."""
        if not program_id:
            return 'independent'
        if 'hyatt' in program_id:
            return 'hyatt'
        if 'hilton' in program_id:
            return 'hilton'
        if 'marriott' in program_id:
            return 'marriott'
        if 'ihg' in program_id:
            return 'ihg'
        return 'independent'

    def infer_brand(self, hotel_name):
        """Infer hotel brand/loyalty program from the hotel name."""
        name_lower = hotel_name.lower()
        # Check longer keywords first for specificity
        for keyword in sorted(BRAND_KEYWORDS.keys(), key=len, reverse=True):
            if keyword in name_lower:
                return BRAND_KEYWORDS[keyword]
        return {'chain_name': 'Independent', 'program_id': '', 'program_name': ''}

    def search_hotels(self, location_query, check_in_raw=None, check_out_raw=None, guests='1'):
        """
        Search for hotels using SerpApi Google Hotels (prices + images),
        falling back to Firestore cache, then Google Places.

        Flow:
        1. Try SerpApi → on success, save observations + fallback cache, return with price_history
        2. SerpApi fails → read Firestore fallback cache → return with 'cached' flag
        3. No cache → try Google Places (no prices)
        """
        # Short-lived in-memory cache to avoid re-hitting SerpApi on page refreshes
        src = 'serp' if get_serpapi_key() else 'places'
        cache_key = f"hotel_search_{src}_{location_query}_{check_in_raw}_{check_out_raw}_{guests}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        hotels = []
        source = None

        # 1. Try SerpApi Google Hotels first (has prices + images)
        if get_serpapi_key() and check_in_raw and check_out_raw:
            hotels = self._search_via_serpapi(location_query, check_in_raw, check_out_raw, guests)
            if hotels:
                source = 'serpapi'

        # 2. SerpApi failed → try Firestore fallback cache
        if not hotels and check_in_raw and check_out_raw:
            try:
                cached_hotels, fetched_at = db.get_cached_hotel_search(
                    location_query, check_in_raw, check_out_raw, guests
                )
                if cached_hotels:
                    # Mark each hotel as cached with timestamp
                    for h in cached_hotels:
                        h['is_cached'] = True
                        h['cached_at'] = str(fetched_at) if fetched_at else ''
                    hotels = cached_hotels
                    source = 'cache'
            except Exception as e:
                print(f"Firestore cache read error: {e}")

        # 3. Still nothing → try Google Places (no prices)
        if not hotels:
            hotels = self._search_via_places(location_query)
            if hotels:
                source = 'places'

        # Post-processing for SerpApi results: save to Firestore
        if source == 'serpapi' and check_in_raw and check_out_raw:
            try:
                # Save daily rate observations
                hotel_keys = db.save_hotel_daily_rates(
                    hotels, check_in_raw, check_out_raw, location_query
                )
                # Save full result as fallback cache
                db.save_hotel_search_cache(
                    location_query, check_in_raw, check_out_raw, guests, hotels
                )
                # Attach price history for display
                for h in hotels:
                    hkey = hotel_keys.get(h['name'])
                    if hkey:
                        summary = db.get_hotel_price_summary(hkey, check_in_raw)
                        if summary:
                            h['price_history'] = summary
            except Exception as e:
                print(f"Firestore price save error: {e}")

        if hotels:
            cache.set(cache_key, hotels, 3600)

        return hotels

    def _search_via_serpapi(self, location_query, check_in, check_out, guests='1'):
        """Search hotels via SerpApi Google Hotels API — returns prices and images."""
        hotels = []
        try:
            params = {
                'engine': 'google_hotels',
                'q': f'Hotels in {location_query}',
                'check_in_date': check_in,
                'check_out_date': check_out,
                'adults': int(guests),
                'currency': 'USD',
                'hl': 'en',
                'gl': 'us',
                'api_key': get_serpapi_key(),
            }

            resp = requests.get('https://serpapi.com/search', params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            properties = data.get('properties', [])
            for prop in properties:
                try:
                    name = prop.get('name', 'Unknown Hotel')
                    gps = prop.get('gps_coordinates', {})
                    lat = gps.get('latitude')
                    lng = gps.get('longitude')

                    # Price data
                    rate_info = prop.get('rate_per_night', {})
                    rate_per_night = rate_info.get('extracted_lowest')
                    rate_display = rate_info.get('lowest', '')
                    total_info = prop.get('total_rate', {})
                    total_rate = total_info.get('extracted_lowest')

                    # Image
                    images = prop.get('images', [])
                    photo_url = images[0].get('thumbnail') if images else None

                    # Rating
                    rating = prop.get('overall_rating', 0) or 0
                    reviews = prop.get('reviews', 0) or 0
                    hotel_class = prop.get('extracted_hotel_class', 0)

                    # Brand + loyalty
                    brand_info = self.infer_brand(name)
                    brand_name = brand_info['chain_name']
                    program_id = brand_info['program_id']
                    program_name = brand_info['program_name']

                    # Premium programs
                    premium = match_hotel_to_programs(name, lat, lng)

                    # Use property_token as stable ID
                    place_id = prop.get('property_token', name.replace(' ', '_'))

                    # Price sources (e.g., Booking.com, Hotels.com)
                    price_sources = []
                    for p in prop.get('prices', []):
                        price_sources.append({
                            'source': p.get('source', ''),
                            'rate': p.get('rate_per_night', {}).get('extracted_lowest'),
                        })

                    hotel_json_obj = {
                        'place_id': place_id,
                        'name': name,
                        'address': location_query,
                        'brand_name': brand_name,
                        'program_id': program_id,
                        'program_name': program_name,
                        'rating': rating,
                        'rate_per_night': rate_per_night,
                        'total_rate': total_rate,
                        'hotel_class': hotel_class,
                        'premium_programs': premium,
                    }

                    hotels.append({
                        'place_id': place_id,
                        'id_safe': place_id.replace('/', '_').replace(' ', '_'),
                        'name': name,
                        'location_text': f"{location_query} • {brand_name}",
                        'rating': rating,
                        'user_rating_count': reviews,
                        'price_level': hotel_class,
                        'rate_per_night': rate_per_night,
                        'rate_display': rate_display,
                        'total_rate': total_rate,
                        'photo_url': photo_url,
                        'address': location_query,
                        'brand': brand_name,
                        'brand_class': self.get_brand_class(program_id),
                        'program_id': program_id,
                        'program_name': program_name,
                        'premium_programs': premium,
                        'json_data': json.dumps(hotel_json_obj),
                    })

                except Exception as e:
                    print(f"SerpApi parse error: {e}")
                    continue

        except Exception as e:
            print(f"SerpApi search error: {e}")

        return hotels

    def _search_via_places(self, location_query):
        """Fallback: search hotels via Google Places API (no prices)."""
        hotels = []
        search_query = f"Hotels in {location_query}"
        try:
            places = self.places_service.search_hotels(search_query)
            for place in places:
                try:
                    place_id = place.get('id', '')
                    display_name = place.get('displayName', {})
                    name = display_name.get('text', 'Unknown Hotel') if isinstance(display_name, dict) else str(display_name)
                    rating = place.get('rating', 0)
                    user_rating_count = place.get('userRatingCount', 0)
                    address = place.get('formattedAddress', '')
                    price_level_raw = place.get('priceLevel', '')
                    price_level = PRICE_LEVEL_MAP.get(price_level_raw, 0)

                    photo_url = None
                    photos = place.get('photos', [])
                    if photos:
                        photo_name = photos[0].get('name', '')
                        if photo_name:
                            photo_url = self.places_service.get_photo_url(photo_name)

                    brand_info = self.infer_brand(name)
                    brand_name = brand_info['chain_name']
                    program_id = brand_info['program_id']
                    program_name = brand_info['program_name']

                    location = place.get('location', {})
                    lat = location.get('latitude')
                    lng = location.get('longitude')
                    premium = match_hotel_to_programs(name, lat, lng)

                    hotel_json_obj = {
                        'place_id': place_id,
                        'name': name,
                        'address': address,
                        'brand_name': brand_name,
                        'program_id': program_id,
                        'program_name': program_name,
                        'rating': rating,
                        'price_level': price_level,
                        'premium_programs': premium,
                    }

                    hotels.append({
                        'place_id': place_id,
                        'id_safe': place_id.replace('/', '_'),
                        'name': name,
                        'location_text': f"{address.split(',')[-2].strip() if ',' in address else location_query} • {brand_name}",
                        'rating': rating,
                        'user_rating_count': user_rating_count,
                        'price_level': price_level,
                        'rate_per_night': None,
                        'rate_display': '',
                        'total_rate': None,
                        'photo_url': photo_url,
                        'address': address,
                        'brand': brand_name,
                        'brand_class': self.get_brand_class(program_id),
                        'program_id': program_id,
                        'program_name': program_name,
                        'premium_programs': premium,
                        'json_data': json.dumps(hotel_json_obj),
                    })
                except Exception as e:
                    print(f"Places parse error: {e}")
                    continue
        except Exception as e:
            print(f"Google Places search error: {e}")
        return hotels
