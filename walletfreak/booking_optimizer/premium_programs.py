"""
Premium hotel program matching service.

Matches hotels from Google Places search results against curated lists of:
- Amex Fine Hotels & Resorts (FHR)
- Amex The Hotel Collection (THC)
- Chase The Edit

Uses geo-distance + name similarity for matching since Google Places IDs
don't correspond to these program lists.
"""

import json
import os
import math
from functools import lru_cache
from django.conf import settings
from django.core.cache import cache

DATA_DIR = os.path.join(settings.BASE_DIR, 'walletfreak_data')

# Max distance (km) for geo-match candidates
GEO_MATCH_RADIUS_KM = 2.0


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distance between two lat/lng points in km."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _normalize_name(name):
    """Normalize hotel name for fuzzy comparison."""
    name = name.lower().strip()
    # Remove common suffixes/prefixes
    for term in ['hotel', 'resort', 'spa', '& spa', 'and spa', '& resort', 'and resort',
                 'a luxury collection', 'autograph collection', 'tribute portfolio',
                 'curio collection by hilton', 'the ', 'an ']:
        name = name.replace(term, '')
    # Remove punctuation
    name = ''.join(c for c in name if c.isalnum() or c == ' ')
    return ' '.join(name.split())


def _name_similarity(name1, name2):
    """Simple word-overlap similarity score (0-1)."""
    words1 = set(_normalize_name(name1).split())
    words2 = set(_normalize_name(name2).split())
    if not words1 or not words2:
        return 0
    intersection = words1 & words2
    return len(intersection) / min(len(words1), len(words2))


def _load_json_file(filename):
    """Load a JSON data file from walletfreak_data."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r') as f:
        return json.load(f)


def get_premium_programs_data():
    """
    Load and cache all premium program hotel data.
    Returns dict with 'fhr', 'thc', 'chase_edit' keys.
    """
    cached = cache.get('premium_programs_data')
    if cached:
        return cached

    data = {
        'fhr': _load_json_file('amex_fhr_hotels.json'),
        'thc': _load_json_file('amex_thc_hotels.json'),
        'chase_edit': _load_json_file('chase_edit_hotels.json'),
    }

    cache.set('premium_programs_data', data, 86400)  # 24h cache
    return data


def match_hotel_to_programs(hotel_name, hotel_lat=None, hotel_lng=None):
    """
    Match a hotel from search results against premium program lists.

    Returns dict with program membership info:
    {
        'amex_fhr': {'matched': True, 'credit': '...', 'benefits': [...]},
        'amex_thc': {'matched': True, 'credit': '...'},
        'chase_edit': {'matched': True, 'chase_2026_credit': True, 'brand': '...'},
    }
    """
    programs = get_premium_programs_data()
    result = {
        'amex_fhr': None,
        'amex_thc': None,
        'chase_edit': None,
    }

    # Match against FHR
    match = _find_best_match(hotel_name, hotel_lat, hotel_lng, programs['fhr'], geo_key_lat='latitude', geo_key_lng='longitude')
    if match:
        result['amex_fhr'] = {
            'matched': True,
            'name': match.get('name', ''),
            'credit': match.get('credit', ''),
            'early_checkin': match.get('early_checkin', ''),
            'free_breakfast': match.get('free_breakfast', ''),
            'late_checkout': match.get('late_checkout', ''),
            'room_upgrade': match.get('room_upgrade', ''),
        }

    # Match against THC
    match = _find_best_match(hotel_name, hotel_lat, hotel_lng, programs['thc'], geo_key_lat='latitude', geo_key_lng='longitude')
    if match:
        result['amex_thc'] = {
            'matched': True,
            'name': match.get('name', ''),
            'credit': match.get('credit', ''),
        }

    # Match against Chase Edit
    match = _find_best_match(hotel_name, hotel_lat, hotel_lng, programs['chase_edit'], geo_key_lat='latitude', geo_key_lng='longitude')
    if match:
        result['chase_edit'] = {
            'matched': True,
            'name': match.get('name', ''),
            'brand': match.get('brand', ''),
            'chase_2026_credit': match.get('chase_2026_credit', '') == 'TRUE',
            'michelin_keys': match.get('michelin_keys', ''),
        }

    return result


def _find_best_match(hotel_name, hotel_lat, hotel_lng, program_hotels, geo_key_lat='latitude', geo_key_lng='longitude'):
    """
    Find the best matching hotel in a program list using geo + name similarity.
    """
    if not program_hotels:
        return None

    best_match = None
    best_score = 0

    # If we have coordinates, filter by geo first
    candidates = program_hotels
    if hotel_lat is not None and hotel_lng is not None:
        candidates = []
        for h in program_hotels:
            h_lat = h.get(geo_key_lat)
            h_lng = h.get(geo_key_lng)
            if h_lat is not None and h_lng is not None:
                try:
                    dist = _haversine_km(hotel_lat, hotel_lng, float(h_lat), float(h_lng))
                    if dist <= GEO_MATCH_RADIUS_KM:
                        candidates.append(h)
                except (ValueError, TypeError):
                    continue

    # Score candidates by name similarity
    for candidate in candidates:
        score = _name_similarity(hotel_name, candidate.get('name', ''))
        if score > best_score:
            best_score = score
            best_match = candidate

    # When we used geo-filtering, require higher name similarity
    # since multiple luxury hotels can be within 2km in cities
    threshold = 0.5 if hotel_lat is None else 0.6
    if best_score >= threshold:
        return best_match

    return None
