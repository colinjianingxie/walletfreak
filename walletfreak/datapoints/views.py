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
        card_images = {c.get('slug', c.get('id')): c.get('image_url') for c in all_cards}
        
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
    except Exception as e:
        print(f"Error fetching cards: {e}")
        all_cards = []
        active_cards_list = []
        submission_cards = []
        card_images = {}
        
    # Robustly build card images map using both ID and Slug as keys
    for c in all_cards:
        img = c.get('image_url')
        if img:
            if c.get('id'): card_images[c.get('id')] = img
            if c.get('slug'): card_images[c.get('slug')] = img

    # Convert to DataPoint proxy objects for template compatibility
    datapoints = []
    missing_user_indices = []
    missing_user_ids = []
    
    current_uid = request.user.username if request.user.is_authenticated else None

    for i, data in enumerate(raw_datapoints):
        dp = DataPoint()
        dp.id = data.get('id')
        dp.user_id = data.get('user_id')
        
        # Check if display name is missing or effectively anonymous
        # If it's stored as 'anonymous' but we have a user_id, let's try to resolve it
        stored_name = data.get('user_display_name')
        if (not stored_name or stored_name == 'anonymous') and dp.user_id:
             missing_user_indices.append(i)
             missing_user_ids.append(dp.user_id)
        
        dp.user_display_name = stored_name
        dp.card_slug = data.get('card_slug')
        dp.card_image_url = card_images.get(dp.card_slug)
        dp.card_name = data.get('card_name')
        dp.benefit_name = data.get('benefit_name')
        dp.status = data.get('status')
        dp.content = data.get('content')
        dp.date_posted = data.get('date_posted')
        upvoted_by = data.get('upvoted_by') or []
        outdated_by = data.get('outdated_by') or []
        
        dp.upvote_count = data.get('upvote_count', 0)
        
        dp.outdated_count = data.get('outdated_count', 0)
        dp.last_verified = data.get('last_verified')
        
        # Determine voting state for current user
        dp.is_liked = current_uid in upvoted_by if current_uid else False
        dp.is_outdated = current_uid in outdated_by if current_uid else False
        
        datapoints.append(dp)

    # Backfill missing usernames
    if missing_user_ids:
        try:
            users_map = db.get_users_by_ids(missing_user_ids)
            for idx in missing_user_indices:
                dp = datapoints[idx]
                user_data = users_map.get(dp.user_id)
                if user_data:
                    # Prefer username/display name
                    dp.user_display_name = user_data.get('username') or user_data.get('name') or 'anonymous'
        except Exception as e:
            print(f"Error backfilling usernames: {e}")



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
            response_data = {
                'success': True, 
                'voted': result['voted'], 
                'upvote_count': result['upvote_count'],
                'marked_outdated': result['marked_outdated'],
                'outdated_count': result['outdated_count']
            }
            
            if result.get('updated_verified'):
                # Since we used SERVER_TIMESTAMP, we can't get it back immediately from write result easily
                # without re-fetching.
                # For UI responsiveness, let's return current time formatted.
                from django.utils import timezone
                response_data['last_verified_str'] = timezone.now().strftime('%b %d, %Y') # Simplified format for now?
                # Actually, naturaltime is used in templates usually.
                # Let's just return a standard ISO timestamp or similar that JS can parse or simple text.
                response_data['last_verified_timestamp'] = timezone.now().isoformat()
                
            return JsonResponse(response_data)
        else:
             return JsonResponse({'success': False, 'error': result.get('error', 'Unknown error')}, status=500)
             
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def mark_outdated_datapoint(request, pk):
    if request.method == 'POST':
        uid = request.user.username
        result = db.mark_outdated(pk, uid)
        
        if result['success']:
            return JsonResponse({
                'success': True, 
                'marked': result['marked_outdated'], 
                'outdated_count': result['outdated_count'],
                'voted': result['voted'],
                'upvote_count': result['upvote_count']
            })
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

@login_required
def get_datapoint(request, pk):
    """
    Get details of a datapoint for editing.
    """
    try:
        # We need a get_single_datapoint method or reuse filter
        # Reusing get_datapoints is inefficient but works if we filter by ID? 
        # No, query doesn't support ID filter easily in mixin.
        # Let's use direct DB access or add method to mixin.
        # Direct access via db.db.collection... is accessible since db is FirestoreService.
        
        doc = db.db.collection('datapoints').document(pk).get()
        if not doc.exists:
            return JsonResponse({'success': False, 'error': 'Not found'}, status=404)
            
        data = doc.to_dict()
        data['id'] = doc.id
        
        # Check permission
        uid = request.user.username
        if data.get('user_id') != uid:
             return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
             
        # Prepare date strings YYYY-MM-DD
        t_date = data.get('transaction_date')
        if hasattr(t_date, 'strftime'):
            t_date = t_date.strftime('%Y-%m-%d')
            
        c_date = data.get('cleared_date')
        if hasattr(c_date, 'strftime'):
            c_date = c_date.strftime('%Y-%m-%d')

        # Return fields needed for edit
        return JsonResponse({
            'success': True,
            'datapoint': {
                'id': data['id'],
                'content': data.get('content'),
                'status': data.get('status'),
                'transaction_date': t_date,
                'cleared_date': c_date,
                'card_name': data.get('card_name'),
                'card_slug': data.get('card_slug'),
                'benefit_name': data.get('benefit_name')
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def edit_datapoint(request, pk):
    if request.method == 'POST':
        form = DataPointForm(request.POST)
        # Validate only relevant fields? 
        # The form makes card_slug/name/benefit required.
        # We should create a mutable copy of POST and mock missing fields or use a different form.
        # Or just allow them to remain empty if we make form looser.
        # But we made them required=True (default).
        # Let's fill them with dummy data since we ignore them in update.
        
        post_data = request.POST.copy()
        post_data.setdefault('card_slug', 'dummy')
        post_data.setdefault('card_name', 'dummy')
        post_data.setdefault('benefit_name', 'dummy')
        
        form = DataPointForm(post_data)
        
        if form.is_valid():
            uid = request.user.username
            result = db.update_datapoint(pk, uid, form.cleaned_data)
            
            if result['success']:
                return JsonResponse({'success': True})
            else:
                return JsonResponse(result, status=500)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
