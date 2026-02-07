from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from core.services import db
from datetime import datetime, timedelta
import json
from .services import HotelSearchService
from .strategy_service import StrategyAnalysisService

# --- MAIN VIEWS ---

@login_required
def index(request):
    """
    Initial Search View.
    Fetches raw hotel data from Amadeus and renders the list.
    """
    hotels = []
    location_query = request.GET.get('location')
    
    # Dates
    today = datetime.now().date()
    default_check_in = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    default_check_out = (today + timedelta(days=3)).strftime('%Y-%m-%d')
    
    context = {
        'default_check_in': default_check_in,
        'default_check_out': default_check_out,
        'hotels': []
    }

    if location_query:
        service = HotelSearchService()
        check_in_raw = request.GET.get('checkInDate') or default_check_in
        check_out_raw = request.GET.get('checkOutDate') or default_check_out
        
        hotels = service.search_hotels(
            location_query, 
            check_in_raw, 
            check_out_raw, 
            request.GET.get('guests', '1')
        )
        context['hotels'] = hotels

    return render(request, 'booking_optimizer/index.html', context)


@login_required
def compare(request):
    """
    Analyzes selected hotels using AI (Simulated) to determine the best booking strategy.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    uid = request.session.get('uid')
    
    # Get parameters
    check_in = request.POST.get('checkInDate', '2025-06-01')
    check_out = request.POST.get('checkOutDate', '2025-06-03')
    guests = request.POST.get('guests', '1')
    location_text = request.POST.get('location')
    selected_hotels_raw = request.POST.getlist('selected_hotels')

    strategy_service = StrategyAnalysisService()

    if uid:
        try:
            # Run connected strategy
            strategy_service.initiate_strategy(
                uid, location_text, check_in, check_out, guests, selected_hotels_raw
            )
            
            # Redirect to History
            return redirect('booking_optimizer:history')
            
        except Exception as e:
            print(f"Error initiating strategy: {e}")
            return JsonResponse({'error': str(e)}, status=500)

    # Fallback if no User (cannot save history) - run synchronously (demo mode)
    analysis_results = strategy_service.run_anonymous_strategy(
        location_text, check_in, check_out, guests, selected_hotels_raw
    )
    
    context = {
        'analysis': {'analysis_results': analysis_results or []},
        'search_params': {
            'location': location_text,
            'checkInDate': check_in,
            'checkOutDate': check_out,
            'guests': guests
        }
    }
    return render(request, 'booking_optimizer/strategy_report.html', context)

@login_required
def history(request):
    """
    Displays the user's strategy history.
    """
    uid = request.session.get('uid')
    strategies = []
    if uid:
        strategies = db.get_user_hotel_strategies(uid)
        # Parse date strings to datetime objects for template formatting
        for s in strategies:
            try:
                if s.get('check_in'):
                    s['check_in'] = datetime.strptime(s['check_in'], '%Y-%m-%d')
                if s.get('check_out'):
                    s['check_out'] = datetime.strptime(s['check_out'], '%Y-%m-%d')
            except:
                pass
    
    return render(request, 'booking_optimizer/history.html', {'strategies': strategies})

@login_required
def strategy_report(request, strategy_id):
    """
    Displays a specific saved strategy report.
    """
    uid = request.session.get('uid')
    
    strategy = None
    if uid:
        strategy = db.get_hotel_strategy(uid, strategy_id)
        
    if not strategy:
        # Handle not found or unauthorized
        return render(request, 'booking_optimizer/index.html', {'error': 'Report not found'})
        
    # Check if user is super staff
    is_super_staff = False
    if uid:
        user_profile = db.get_user_profile(uid)
        if user_profile:
            is_super_staff = user_profile.get('is_super_staff', False)

    context = {
        'analysis': {'analysis_results': strategy.get('analysis_results', [])},
        'search_params': {
            'location': strategy.get('location_text'),
            'checkInDate': strategy.get('check_in'),
            'checkOutDate': strategy.get('check_out'),
            'guests': strategy.get('guests', '1')
        },
        'strategy_id': strategy_id,
        'is_history_view': True,
        'prompt_used': strategy.get('prompt_used', ''),
        'is_super_staff': is_super_staff
    }
    
    return render(request, 'booking_optimizer/strategy_report.html', context)


@login_required
def check_strategy_status(request):
    """
    API call to check status of specific strategies.
    Expects GET param 'ids' (comma separated).
    """
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    ids = request.GET.get('ids', '').split(',')
    ids = [i.strip() for i in ids if i.strip()]
    
    if not ids:
        return JsonResponse({'statuses': {}})
        
    results = {}
    for sid in ids:
        strat = db.get_hotel_strategy(uid, sid)
        if strat:
            results[sid] = strat.get('status', 'unknown')
    
    return JsonResponse({'statuses': results})

@login_required
def download_prompt(request, strategy_id):
    """
    Download the prompt used to generate a strategy report as a text file.
    """
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    strategy = db.get_hotel_strategy(uid, strategy_id)
    if not strategy:
        return HttpResponse("Strategy not found", status=404)
    
    prompt_text = strategy.get('prompt_used', 'Prompt not available for this report.')
    
    response = HttpResponse(prompt_text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="strategy_{strategy_id}_prompt.txt"'
    return response
