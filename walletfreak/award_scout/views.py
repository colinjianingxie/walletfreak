from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .services import HyattScraper
from .models import AwardAlert
from subscriptions.models import Subscription
import logging

logger = logging.getLogger(__name__)

@login_required
def index(request):
    search_url = ''
    error_message = None
    found_hotels = None
    scan_active = False

    # Handle Search (POST)
    if request.method == 'POST':
        search_url = request.POST.get('url', '')
    
    # Get user's active alerts
    active_alerts = AwardAlert.objects.filter(user=request.user, is_active=True).order_by('-created_at')
    active_count = active_alerts.count()

    # Determine limit based on subscription
    is_premium = False
    try:
        if hasattr(request.user, 'subscription'):
             # Simplistic check - refined logic might depend on exact status/price_id
            is_premium = request.user.subscription.status in ['active', 'trialing']
    except Exception:
        pass
    
    limit = 5 if is_premium else 1
    
    if search_url:
        scan_active = True
        try:
            scraper = HyattScraper()
            found_hotels = scraper.scrape_url(search_url)
            
            if not found_hotels:
                error_message = "No hotels found. The URL might be invalid, or Hyatt blocked the request. Try again shortly."
        except Exception as e:
             logger.error(f"Scraping failed: {e}")
             found_hotels = []
             error_message = "An error occurred while scanning. Please try again."

    context = {
        'active_alerts': active_alerts,
        'active_count': active_count,
        'limit': limit,
        'search_url': search_url,
        'error_message': error_message,
        'scan_active': scan_active,
        'found_hotels': found_hotels,
    }
    return render(request, 'award_scout/index.html', context)

@login_required
def track_selected(request):
    if request.method == "POST":
        # logic to save selected hotels would go here
        # for now just redirect back
        pass
    return redirect('award_scout:index')
