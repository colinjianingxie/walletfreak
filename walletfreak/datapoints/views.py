from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import DataPoint
from .forms import DataPointForm
from core.services import db # Import shared DB service for getting cards
import json

def datapoint_list(request):
    sort_by = request.GET.get('sort', 'newest')
    filter_card_slug = request.GET.get('card', None)
    filter_benefit_name = request.GET.get('benefit', None)
    
    # Fetch from Firestore
    # Note: If we need 'benefit_name' filtering in backend, we should add it to DataPointMixin.get_datapoints too.
    # For now, let's filter in memory or update get_datapoints? 
    # Updating get_datapoints is cleaner.
    # But wait, filter_benefit_name is just passed to get_datapoints if we update it.
    # Let's check get_datapoints signature. It doesn't have benefit_name yet.
    # I'll update the call here assuming I'll update the service next, or filter in memory if small.
    # Given limit=50, memory filtering might hide matches. Better to update service.
    # But for this step, let's stick to the plan: "Update datapoint_list to pass selected_card_benefits".
    
    # We'll pass the benefit filter to get_datapoints (will need update)
    # raw_datapoints = db.get_datapoints(limit=50, sort_by=sort_by, card_slug=filter_card_slug, benefit_name=filter_benefit_name)
    # Since I haven't updated service yet, I will filter in memory for NOW to avoid breaking, 
    # but ideally I should update service.
    
    raw_datapoints = db.get_datapoints(limit=50, sort_by=sort_by, card_slug=filter_card_slug)
    
    if filter_benefit_name:
        raw_datapoints = [d for d in raw_datapoints if d.get('benefit_name') == filter_benefit_name]
    
    # Get cards for images and filter
    selected_card_benefits = []
    
    try:
        all_cards = db.get_cards()
        active_slugs = db.get_active_card_slugs()

        # Update all_cards to only include those in active_slugs
        # BUT we still need the full list to detect card names if needed?
        # Actually for filters, we only want active ones.
        # However, for card_images mapping, we might want all? 
        # But images are only shown for datapoints which are by definition "active".
        # So we can safely filter all_cards.
        
        # Keep card_images for all JUST IN CASE there's a race condition or mismatch,
        # but displaying filter options should be restricted.
        card_images = {c['slug']: c.get('image_url') for c in all_cards}
        
        # Filter the 'all_cards' variable passed to template for options
        active_cards_list = [c for c in all_cards if c.get('slug') in active_slugs]
        
        # Replace 'all_cards' context variable logic
        # But wait, lines 71 usage: submission_cards uses all_cards.
        # Submission needs ALL cards (or target list). 
        # So we should create a new variable 'filter_cards' for the UI options.
        if filter_card_slug:
            selected_card = next((c for c in all_cards if c.get('slug') == filter_card_slug), None)
            if selected_card:
                # benefits might be list of strings or objects. 
                # Model says: benefits_json. 
                # Let's inspect how db.get_cards returns it. usually dicts.
                # usage: c.get('benefits', [])
                # If they are objects {title: ...}, extract title.
                raw_benefits = selected_card.get('benefits', [])
                # normalize to list of strings
                for b in raw_benefits:
                    if isinstance(b, dict):
                        # Filter by Benefit Type 'Credit'
                        b_type = b.get('benefit_type') or b.get('BenefitType')
                        if b_type == 'Credit':
                            # Try multiple keys for robustness
                            title = b.get('short_description') or b.get('BenefitDescriptionShort') or b.get('description') or b.get('BenefitDescription') or b.get('title') or 'Unknown'
                            selected_card_benefits.append(title)
                    elif isinstance(b, str):
                        # If it's a string, we can't check type, so exclude or include? 
                        # Assuming strings are legacy/simple and might not be credits. 
                        # Safe to exclude if we only want credits.
                        pass
        
        # Hardcoded list of allowed cards for submission
        TARGET_SLUGS = [
            "american-express-platinum-card", "american-express-gold-card", "chase-sapphire-reserve", 
            "the-business-platinum-card-from-american-express", "chase-sapphire-preferred-card", 
            "capital-one-venture-x-rewards-credit-card", "citi-strata-premier-card", "citi-strata-elite-card",
            "chase-freedom-unlimited", "us-bank-altitude-reserve-visa-infinite-card", 
            "hilton-honors-aspire-card-from-american-express", 
            "hilton-honors-american-express-surpass-card", "the-hilton-honors-american-express-business-card", 
            "delta-skymiles-platinum-american-express-card", "ink-business-cash-credit-card", 
            "ihg-one-rewards-premier-credit-card", "marriott-bonvoy-bevy-american-express-card", 
            "citi-aadvantage-business-world-elite-mastercard"
        ]
        
        # Filter cards for the modal
        submission_cards = [c for c in all_cards if c.get('slug') in TARGET_SLUGS]
        # Sort properly? Maybe by name
        submission_cards.sort(key=lambda x: x.get('name', ''))
        
    except:
        all_cards = []
        active_cards_list = []
        submission_cards = []
        card_images = {}
    
    # Convert to DataPoint proxy objects for template compatibility
    datapoints = []
    for data in raw_datapoints:
        dp = DataPoint()
        dp.id = data.get('id')
        dp.user_id = data.get('user_id')
        dp.user_display_name = data.get('user_display_name')
        dp.card_slug = data.get('card_slug')
        dp.card_name = data.get('card_name')
        dp.benefit_name = data.get('benefit_name')
        dp.status = data.get('status')
        dp.content = data.get('content')
        dp.date_posted = data.get('date_posted')
        dp.upvote_count = data.get('upvote_count', 0)
        dp.upvoted_by_json = json.dumps(data.get('upvoted_by', []))
        dp.card_image_url = card_images.get(dp.card_slug)
        datapoints.append(dp)

    context = {
        'datapoints': datapoints,
        'cards': active_cards_list, # For the main filter - ONLY active cards
        'submission_cards': submission_cards, # For the modal
        'current_sort': sort_by,
        'current_filter_card': filter_card_slug,
        'current_filter_benefit': filter_benefit_name,
        'selected_card_benefits': selected_card_benefits,
    }

    if request.headers.get('HX-Request'):
        context['is_htmx'] = True
        return render(request, 'datapoints/partials/_feed.html', context)

    return render(request, 'datapoints/list.html', context)

@login_required
def submit_datapoint(request):
    if request.method == 'POST':
        form = DataPointForm(request.POST)
        if form.is_valid():
            # Create in Firestore
            data = form.cleaned_data
            
            # Request user might be Django User.
            # We need the Firebase UID. 
            # If used with FirebaseAdminMiddleware, request.user.username IS the UID.
            uid = request.user.username
            
            doc_id = db.create_datapoint(uid, data)
            
            if doc_id:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Database error'}, status=500)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def vote_datapoint(request, pk):
    if request.method == 'POST':
        uid = request.user.username
        result = db.vote_datapoint(pk, uid)
        
        if result['success']:
            return JsonResponse({'success': True, 'voted': result['voted'], 'count': result['count']})
        else:
             return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
             
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

def get_user_wallet(request, uid):
    """
    API endpoint to get a user's wallet cards.
    Publicly accessible to show in modal.
    """
    try:
        # Get active cards for this user
        active_cards = db.get_user_cards(uid, status='active')
        
        # Format for frontend
        cards_data = []
        for card in active_cards:
            cards_data.append({
                'name': card.get('name', 'Unknown Card'),
                'image_url': card.get('image_url') or '',
                'id': card.get('id')
            })
            
        return JsonResponse({'success': True, 'cards': cards_data})
    except Exception as e:
        print(f"Error fetching user wallet for {uid}: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
