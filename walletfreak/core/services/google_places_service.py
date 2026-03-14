import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

PLACES_API_BASE = 'https://places.googleapis.com/v1'


class GooglePlacesService:
    """Google Places API (New) service for hotel discovery."""

    def __init__(self):
        self.api_key = getattr(settings, 'GOOGLE_PLACES_API_KEY', '') or os.environ.get('GOOGLE_PLACES_API_KEY', '')

    def search_hotels(self, query, location_bias=None):
        """
        Text Search for hotels using Google Places API (New).
        Returns list of place results with lodging type filter.
        """
        if not self.api_key:
            logger.warning("GOOGLE_PLACES_API_KEY not configured")
            return []

        url = f'{PLACES_API_BASE}/places:searchText'

        field_mask = ','.join([
            'places.id',
            'places.displayName',
            'places.rating',
            'places.userRatingCount',
            'places.formattedAddress',
            'places.priceLevel',
            'places.photos',
            'places.types',
            'places.location',
        ])

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': field_mask,
        }

        body = {
            'textQuery': query,
            'includedType': 'lodging',
            'languageCode': 'en',
            'maxResultCount': 20,
        }

        if location_bias:
            body['locationBias'] = location_bias

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get('places', [])
        except requests.RequestException as e:
            logger.error(f"Google Places search error: {e}")
            return []

    def get_place_details(self, place_id):
        """Fetch full details for a specific place."""
        if not self.api_key:
            return None

        url = f'{PLACES_API_BASE}/places/{place_id}'

        field_mask = ','.join([
            'id',
            'displayName',
            'rating',
            'userRatingCount',
            'formattedAddress',
            'priceLevel',
            'photos',
            'types',
            'location',
            'websiteUri',
            'internationalPhoneNumber',
        ])

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': field_mask,
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"Google Places details error: {e}")
            return None

    def autocomplete(self, query):
        """Autocomplete location/place suggestions."""
        if not self.api_key or not query:
            return []

        url = f'{PLACES_API_BASE}/places:autocomplete'

        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
        }

        body = {
            'input': query,
            'includedPrimaryTypes': ['locality', 'administrative_area_level_1', 'country', 'neighborhood', 'sublocality'],
            'languageCode': 'en',
        }

        try:
            resp = requests.post(url, json=body, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            suggestions = []
            for s in data.get('suggestions', []):
                place_prediction = s.get('placePrediction', {})
                if place_prediction:
                    text = place_prediction.get('text', {}).get('text', '')
                    place_id = place_prediction.get('placeId', '')
                    if text:
                        suggestions.append({'text': text, 'place_id': place_id})
            return suggestions
        except requests.RequestException as e:
            logger.error(f"Google Places autocomplete error: {e}")
            return []

    def get_photo_url(self, photo_name, max_width=400):
        """Generate a photo URL from a Places photo resource name."""
        if not photo_name or not self.api_key:
            return None
        return f'{PLACES_API_BASE}/{photo_name}/media?maxWidthPx={max_width}&key={self.api_key}'
