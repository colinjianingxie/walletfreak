from ninja import Router
from django.http import JsonResponse
from core.services import db
from api.auth_middleware import BearerAuth
from booking_optimizer.services import HotelSearchService
from booking_optimizer.strategy_service import StrategyAnalysisService
from core.services.google_places_service import GooglePlacesService
from datetime import datetime, timedelta, timezone
import json

router = Router(tags=["booking"], auth=BearerAuth())


@router.get("/autocomplete/")
def autocomplete_location(request, query: str):
    """Autocomplete location suggestions for hotel search."""
    try:
        service = GooglePlacesService()
        suggestions = service.autocomplete(query)
        return {'suggestions': suggestions}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.get("/search/")
def search_hotels(request, location: str, check_in: str = None, check_out: str = None, guests: str = '1'):
    """Search for hotels using Google Places API."""
    try:
        service = HotelSearchService()
        hotels = service.search_hotels(location, check_in, check_out, guests)

        results = []
        for h in hotels:
            item = {
                'place_id': h.get('place_id', ''),
                'name': h.get('name', ''),
                'rating': h.get('rating', 0),
                'user_rating_count': h.get('user_rating_count', 0),
                'price_level': h.get('price_level', 0),
                'rate_per_night': h.get('rate_per_night'),
                'rate_display': h.get('rate_display', ''),
                'total_rate': h.get('total_rate'),
                'photo_url': h.get('photo_url'),
                'address': h.get('address', ''),
                'brand': h.get('brand', 'Independent'),
                'brand_class': h.get('brand_class', 'independent'),
                'program_id': h.get('program_id', ''),
                'program_name': h.get('program_name', ''),
                'premium_programs': h.get('premium_programs', {}),
                'json_data': h.get('json_data', '{}'),
            }
            # Price history (prior observations)
            if h.get('price_history'):
                item['price_history'] = h['price_history']
            # Cached fallback indicator
            if h.get('is_cached'):
                item['is_cached'] = True
                item['cached_at'] = h.get('cached_at', '')
            results.append(item)

        return {'hotels': results}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.post("/analyze/")
def analyze_booking(request):
    """
    Initiate strategy analysis for selected hotels.
    Launches background Grok analysis and returns strategy_id for polling.
    """
    uid = request.auth
    try:
        body = json.loads(request.body)
        selected_hotels = body.get('selected_hotels', [])
        check_in = body.get('check_in', '')
        check_out = body.get('check_out', '')
        guests = body.get('guests', '1')
        location = body.get('location', '')

        if not selected_hotels:
            return JsonResponse({'error': 'No hotels selected'}, status=400)

        # Convert hotel dicts to JSON strings (strategy_service expects list of JSON strings)
        selected_hotels_raw = [json.dumps(h) for h in selected_hotels]

        strategy_service = StrategyAnalysisService()
        strategy_id = strategy_service.initiate_strategy(
            uid, location, check_in, check_out, guests, selected_hotels_raw
        )

        return {'strategy_id': strategy_id, 'status': 'processing'}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.get("/strategies/")
def list_strategies(request):
    """List user's booking strategy history."""
    uid = request.auth
    try:
        strategies = db.get_user_hotel_strategies(uid)
        stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)

        results = []
        for s in strategies:
            status = s.get('status', 'unknown')

            # Mark stale processing strategies as failed
            if status == 'processing':
                created = s.get('created_at')
                if created and hasattr(created, 'timestamp'):
                    # Firestore DatetimeWithNanoseconds
                    if created < stale_cutoff:
                        status = 'failed'

            results.append({
                'id': s.get('id', ''),
                'location_text': s.get('location_text', ''),
                'check_in': s.get('check_in', ''),
                'check_out': s.get('check_out', ''),
                'guests': s.get('guests', '1'),
                'hotel_count': s.get('hotel_count', 0),
                'status': status,
                'created_at': str(s.get('created_at', '')),
            })

        return {'strategies': results}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.get("/strategies/{strategy_id}/")
def get_strategy(request, strategy_id: str):
    """Get full strategy details including analysis results."""
    uid = request.auth
    try:
        strategy = db.get_hotel_strategy(uid, strategy_id)
        if not strategy:
            return JsonResponse({'error': 'Strategy not found'}, status=404)

        return {
            'id': strategy.get('id', ''),
            'location_text': strategy.get('location_text', ''),
            'check_in': strategy.get('check_in', ''),
            'check_out': strategy.get('check_out', ''),
            'guests': strategy.get('guests', '1'),
            'hotel_count': strategy.get('hotel_count', 0),
            'status': strategy.get('status', 'unknown'),
            'analysis_results': strategy.get('analysis_results', []),
            'created_at': str(strategy.get('created_at', '')),
        }
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.get("/strategies/{strategy_id}/status/")
def get_strategy_status(request, strategy_id: str):
    """Check processing status of a strategy."""
    uid = request.auth
    try:
        strategy = db.get_hotel_strategy(uid, strategy_id)
        if not strategy:
            return JsonResponse({'error': 'Strategy not found'}, status=404)

        return {'status': strategy.get('status', 'unknown')}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@router.delete("/strategies/{strategy_id}/")
def delete_strategy(request, strategy_id: str):
    """Delete a strategy from user's history."""
    uid = request.auth
    try:
        doc_ref = db.db.collection('users').document(uid).collection('hotel_strategies').document(strategy_id)
        doc = doc_ref.get()
        if not doc.exists:
            return JsonResponse({'error': 'Strategy not found'}, status=404)
        doc_ref.delete()
        return {'success': True}
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
