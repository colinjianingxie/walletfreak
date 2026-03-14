import hashlib
import re
from datetime import datetime, timedelta
from google.cloud.firestore_v1 import ArrayUnion, SERVER_TIMESTAMP


class HotelPriceMixin:
    """Mixin for hotel price caching and observation history in Firestore."""

    def _hotel_doc_key(self, name, location):
        """Generate a deterministic slug from hotel name + location."""
        raw = f"{name}-{location}".lower()
        # Keep only alphanumeric, spaces, hyphens
        raw = re.sub(r'[^a-z0-9\s-]', '', raw)
        # Replace whitespace with hyphens, collapse multiples
        slug = re.sub(r'[\s-]+', '-', raw).strip('-')
        # Firestore doc IDs max 1500 bytes; truncate to be safe
        return slug[:200]

    def _search_cache_key(self, location, check_in, check_out, guests):
        """MD5 hash of search params for fallback cache doc ID."""
        raw = f"{location}|{check_in}|{check_out}|{guests}"
        return hashlib.md5(raw.encode()).hexdigest()

    def save_hotel_profile(self, hotel, location_text):
        """Upsert the hotel_prices/{hotel_key} profile document."""
        hotel_key = self._hotel_doc_key(hotel['name'], location_text)
        doc_ref = self.db.collection('hotel_prices').document(hotel_key)
        doc_ref.set({
            'name': hotel['name'],
            'location': location_text,
            'gps': hotel.get('gps'),
            'hotel_class': hotel.get('hotel_class') or hotel.get('price_level', 0),
            'brand': hotel.get('brand', 'Independent'),
            'program_id': hotel.get('program_id', ''),
            'photo_url': hotel.get('photo_url'),
            'overall_rating': hotel.get('rating', 0),
            'reviews': hotel.get('user_rating_count', 0),
            'last_updated': SERVER_TIMESTAMP,
        }, merge=True)
        return hotel_key

    def save_hotel_daily_rates(self, hotels, check_in, check_out, location_text):
        """
        For each hotel, append a price observation to each stay-night's
        daily_rates subcollection document.
        Returns a dict mapping hotel name -> hotel_key for downstream use.
        """
        from datetime import date as date_type

        ci = datetime.strptime(check_in, '%Y-%m-%d').date()
        co = datetime.strptime(check_out, '%Y-%m-%d').date()

        # Generate list of stay nights (check-in to day before check-out)
        stay_nights = []
        d = ci
        while d < co:
            stay_nights.append(d.isoformat())
            d += timedelta(days=1)

        hotel_keys = {}
        batch = self.db.batch()
        ops = 0

        for hotel in hotels:
            rate = hotel.get('rate_per_night')
            if rate is None:
                continue

            hotel_key = self._hotel_doc_key(hotel['name'], location_text)
            hotel_keys[hotel['name']] = hotel_key

            # Upsert hotel profile
            profile_ref = self.db.collection('hotel_prices').document(hotel_key)
            batch.set(profile_ref, {
                'name': hotel['name'],
                'location': location_text,
                'hotel_class': hotel.get('hotel_class') or hotel.get('price_level', 0),
                'brand': hotel.get('brand', 'Independent'),
                'program_id': hotel.get('program_id', ''),
                'photo_url': hotel.get('photo_url'),
                'overall_rating': hotel.get('rating', 0),
                'reviews': hotel.get('user_rating_count', 0),
                'last_updated': SERVER_TIMESTAMP,
            }, merge=True)
            ops += 1

            # Append observation to each stay night
            observation = {
                'rate': rate,
                'observed_at': datetime.utcnow().isoformat(),
                'source': 'serpapi',
            }

            for night in stay_nights:
                doc_ref = (
                    self.db.collection('hotel_prices')
                    .document(hotel_key)
                    .collection('daily_rates')
                    .document(night)
                )
                batch.set(doc_ref, {
                    'latest_rate': rate,
                    'latest_observed_at': SERVER_TIMESTAMP,
                    'observations': ArrayUnion([observation]),
                }, merge=True)
                ops += 1

                # Firestore batch limit is 500 ops
                if ops >= 490:
                    batch.commit()
                    batch = self.db.batch()
                    ops = 0

        if ops > 0:
            batch.commit()

        return hotel_keys

    def save_hotel_search_cache(self, location, check_in, check_out, guests, hotels):
        """Write full search result to fallback cache."""
        cache_key = self._search_cache_key(location, check_in, check_out, guests)
        doc_ref = self.db.collection('hotel_search_cache').document(cache_key)
        doc_ref.set({
            'location_text': location,
            'check_in': check_in,
            'check_out': check_out,
            'guests': guests,
            'fetched_at': SERVER_TIMESTAMP,
            'source': 'serpapi',
            'hotels': hotels,
        })

    def get_cached_hotel_search(self, location, check_in, check_out, guests):
        """Read fallback cache. Returns (hotels_list, fetched_at) or (None, None)."""
        cache_key = self._search_cache_key(location, check_in, check_out, guests)
        doc_ref = self.db.collection('hotel_search_cache').document(cache_key)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get('hotels', []), data.get('fetched_at')
        return None, None

    def get_hotel_price_history(self, hotel_key, stay_date):
        """
        Get the observations array for a specific hotel + stay night.
        Returns list of observation dicts or empty list.
        """
        doc_ref = (
            self.db.collection('hotel_prices')
            .document(hotel_key)
            .collection('daily_rates')
            .document(stay_date)
        )
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data.get('observations', [])
        return []

    def get_hotel_price_summary(self, hotel_key, check_in):
        """
        Get price summary for a hotel's first stay night.
        Returns dict with prior observations info, or None.
        """
        observations = self.get_hotel_price_history(hotel_key, check_in)
        if not observations or len(observations) < 2:
            return None

        # Exclude the most recent (just-added) observation
        prior = observations[:-1]
        prior_rates = [o['rate'] for o in prior if o.get('rate')]
        if not prior_rates:
            return None

        avg_prior = sum(prior_rates) / len(prior_rates)
        latest_prior = prior[-1]

        return {
            'prior_avg': round(avg_prior, 0),
            'prior_count': len(prior_rates),
            'last_rate': latest_prior.get('rate'),
            'last_observed_at': latest_prior.get('observed_at', ''),
        }
