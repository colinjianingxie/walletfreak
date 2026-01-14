from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
import csv
import json
import os
import math
import ast
from datetime import datetime, date
from core.services import db
from .services import OptimizerService
from core.decorators import cache_control_header

from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """
    Renders the Calculators hub page.
    Includes logic for the SUB Optimizer card state (authed vs unauthed).
    """
    context = {
        'page_title': 'The Freak Lab',
    }
    return render(request, 'calculators/index.html', context)



@login_required
def worth_it_list(request):
    """
    Display a list of credit cards that have an annual fee > 0.
    """
    # Fetch all cards - assuming get_cards returns a list of dictionaries
    # Creating a new instance to call the method if it's an instance method, 
    # but based on core/services/__init__.py, `db` is an instance.
    all_cards = db.get_cards()
    
    # Filter for cards with annual fee > 0 AND at least one benefit with dollar_value > 0
    af_cards = []
    for c in all_cards:
        if (c.get('annual_fee') or 0) > 0:
            # Check for benefits with dollar value
            has_benefits = False
            for b in c.get('benefits', []):
                if b.get('dollar_value') and b.get('dollar_value') > 0:
                    has_benefits = True
                    break
            
            if has_benefits:
                af_cards.append(c)

    # Sort by Annual Fee desc
    af_cards.sort(key=lambda x: x.get('annual_fee') or 0, reverse=True)

    return render(request, 'calculators/worth_it_list.html', {
        'cards': af_cards
    })

@login_required
def worth_it_audit(request, card_slug):
    """
    Display the questionnaire for the selected card.
    Filters benefits to only those with a dollar value.
    """
    card = db.get_card_by_slug(card_slug)
    if not card:
        # Fallback if slug search fails (e.g. if slug is different from doc ID)
        # In `CardMixin.get_card_by_slug`, it calls `get_document('credit_cards', slug)`
        # If that fails, we might want to search by 'slug' field query, but let's assume direct lookup works for now.
        return redirect('worth_it_list')

    # Load custom questions from Firestore (pre-fetched in card object)
    card_questions = card.get('card_questions', [])

    # Create a lookup map for card benefits to get dollar values
    # Key: short_description -> Benefit Dict
    benefits_map = {b.get('short_description', ''): b for b in card.get('benefits', [])}

    audit_benefits = []
    
    # Iterate purely based on CSV questions
    for q_data in card_questions:
        short_desc = q_data['short_desc']
        
        # Get benefit data from DB if available
        # If not available, we use default or 0 value, but we still show the question if user wants it.
        # But calculator needs dollar_value.
        benefit_data = benefits_map.get(short_desc)
        
        dollar_value = 0
        time_cat = 'Annually'
        
        if benefit_data:
            dollar_value = benefit_data.get('dollar_value', 0)
            time_cat = benefit_data.get('time_category', 'Annually')
        
        # Prepare display logic
        label = q_data['question']
        q_type = q_data['question_type']
        choices = q_data['choices']
        
        if q_type == 'multiple_choice' and choices:
            input_type = 'multiple_choice'
            max_val = len(choices) - 1
        else:
            input_type = 'toggle'
            max_val = 1
        
        # Construct audit item
        # We attach the question config effectively creating a "benefit view model"
        audit_item = {
            'short_description': short_desc,
            'dollar_value': dollar_value,
            'time_category': time_cat,
            'audit_config': {
                'input_type': input_type,
                'max_val': max_val,
                'label': label,
                'choices': choices
            }
        }
        audit_benefits.append(audit_item)

    return render(request, 'calculators/worth_it_audit.html', {
        'card': card,
        'benefits': audit_benefits
    })

@login_required
def worth_it_calculate(request, card_slug):
    """
    Calculate the optimization score.
    Returns JSON for AJAX or renders result template.
    """
    if request.method == 'POST':
        card = db.get_card_by_slug(card_slug)
        annual_fee = card.get('annual_fee', 0)
        total_value = 0.0
        
        # Load questions from Firestore (pre-fetched in card object)
        card_questions = card.get('card_questions', [])

        # Benefit lookup map
        benefits_map = {b.get('short_description', ''): b for b in card.get('benefits', [])}
        
        # Iterate through QUESTIONS to calculate value
        total_user_weight = 0.0
        total_max_weight = 0.0
        
        for idx, q_data in enumerate(card_questions):
            # Form field name: benefit_{index}
            field_name = f'benefit_{idx}'
            value_str = request.POST.get(field_name)
            
            # Determining Max Weight for this question
            weights = q_data.get('weights', [])
            this_question_max_weight = 1.0
            if weights:
                try:
                    this_question_max_weight = max(weights)
                except ValueError:
                    this_question_max_weight = 1.0
            
            # Default user weight for this question
            this_question_user_weight = 0.0
            
            if value_str is not None:
                try:
                    val = float(value_str)
                    
                    short_desc = q_data['short_desc']
                    benefit_data = benefits_map.get(short_desc)
                    
                    dollar_val = 0.0
                    time_cat = ''
                    if benefit_data:
                        dollar_val = benefit_data.get('dollar_value') or 0
                        time_cat = benefit_data.get('time_category', '')

                    benefit_value = 0.0
                    
                    if q_data['question_type'] == 'multiple_choice':
                        # Logic for multiple choice
                        # val is the INDEX selected (0 to N-1)
                        choices = q_data['choices']
                        
                        if choices:
                            idx_val = int(val)
                            # Check if we have valid weights for this choice
                            if weights and 0 <= idx_val < len(weights):
                                utilization = weights[idx_val]
                                this_question_user_weight = utilization
                                benefit_value = utilization * dollar_val
                            else:
                                # Fallback: Linear interpolation
                                max_idx = len(choices) - 1
                                if max_idx > 0:
                                    utilization = val / max_idx
                                    this_question_user_weight = utilization # Approx weight
                                    benefit_value = utilization * dollar_val
                                else:
                                    # Single choice? assume 100%
                                    this_question_user_weight = 1.0 if val >= 0 else 0.0
                                    benefit_value = dollar_val if val >= 0 else 0
                        else:
                            this_question_user_weight = 1.0 if val > 0 else 0.0
                            benefit_value = dollar_val if val > 0 else 0
                    
                    elif 'Monthly' in time_cat:
                        # Monthly benfits are often toggles or counters. 
                        # If it's a toggle (val=1), utilization is 1.0
                        # If it is a counter, we might need normalization? 
                        # But standard toggle returns 1.0. 
                        # Assuming val is utilization-proxy for toggle.
                        # For simple toggle: val is 1.0 or 0.0.
                        this_question_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 12.0) * dollar_val
                    elif 'Quarterly' in time_cat:
                        this_question_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 4.0) * dollar_val
                    elif 'Semi' in time_cat:
                        this_question_user_weight = 1.0 if val > 0 else 0.0
                        benefit_value = (val / 2.0) * dollar_val
                    else:
                        # Toggle (1 or 0)
                        this_question_user_weight = val # Assuming val is 0.0 or 1.0
                        benefit_value = val * dollar_val
                        
                    total_value += benefit_value
                    total_user_weight += this_question_user_weight
                    total_max_weight += this_question_max_weight

                except (ValueError, IndexError):
                    # Still add max weight even if user input invalid? 
                    # Probably best to skip or assume 0 user weight.
                    total_max_weight += this_question_max_weight
                    continue
            else:
                # Value missing, still count towards max weight potential
                # Recalculate max weight as it wasn't done above if value_str is None (logic flow adjustment)
                # Actually, duplicate logic needed if we want to count missed questions.
                # But let's assume all questions come in POST or are ignored.
                # If we want to be strict, we really should calculate max_weight outside the 'if value_str' block.
                # Moving max_weight calc up... done.
                total_max_weight += this_question_max_weight
        
        score = total_value - annual_fee
        
        # New Scoring Logic based on Weights
        # Fit Score = (Total User Weight / Total Max Weight) * 100
        fit_percentage = 0
        if total_max_weight > 0:
            fit_percentage = (total_user_weight / total_max_weight) * 100
            
        # Optimization Score / Worth It determination
        # Threshold: 50%
        optimization_score = min(max(int(fit_percentage), 0), 100)
        is_worth_it = fit_percentage >= 50

        # Check wallet status
        wallet_card_ids = []
        if request.user.is_authenticated:
            uid = request.session.get('uid')
            if uid:
                user_cards = db.get_user_cards(uid)
                wallet_card_ids = [c.get('card_id') for c in user_cards]

        # Return context for result template
        return render(request, 'calculators/worth_it_result.html', {
            'card': card,
            'annual_fee': annual_fee,
            'total_value': total_value,
            'net_profit': score, # This is the dollar amount
            'net_profit_abs': abs(score),
            'score_display': optimization_score, # 0-100
            'score_percentage': optimization_score, # For CSS circle
            'is_worth_it': score >= 0,
            'card_json': json.dumps(card, default=str),
            'wallet_card_ids': wallet_card_ids
        })
    
    return redirect('worth_it_audit', card_slug=card_slug)

@login_required
def optimizer_input(request):
    """
    Renders the SUB Optimizer input form.
    """
    return render(request, 'calculators/optimizer_input.html')



def optimizer_calculate(request):
    """
    Calculates ROI for cards based on planned spend and timeframe.
    Returns HTML partial for htmx/ajax injection.
    """
    if not request.user.is_authenticated:
        return redirect('calculators_index')
        
    if request.method != 'POST':
        return redirect('optimizer_input')
        
    try:
        spend = float(request.POST.get('spend', 0))
        timeframe_months = int(request.POST.get('timeframe', 3))
    except ValueError:
        spend = 4000.0
        timeframe_months = 3
        
    mode = request.POST.get('mode', 'single') # 'single' or 'combo'
    sort_by = request.POST.get('sort_by', 'recommended')

    # Get User Wallet (if authenticated)
    user_wallet_slugs = set()
    if request.user.is_authenticated:
        uid = request.session.get('uid') or request.user.username
        if uid:
            owned_cards = db.get_user_cards(uid)
            user_wallet_slugs = {c.get('card_id') for c in owned_cards}

    # Initialize Service
    service = OptimizerService()
    results = service.calculate_recommendations(
        planned_spend=spend,
        duration_months=timeframe_months,
        user_wallet_slugs=user_wallet_slugs,
        mode=mode,
        uid=uid if request.user.is_authenticated else None,
        sort_by=sort_by
    )
    
    context = {
        'results': results,
        'planned_spend': spend,
        'mode': mode
    }
    
    # Render HTML partial
    html = render_to_string('calculators/optimizer_results.html', context, request=request)
    
    # Extract card data for modal usage
    cards_data = [r['card'] for r in results]
    
    # Ensure JSON serializable (handle datetimes etc)
    cards_data_json = json.loads(json.dumps(cards_data, default=str))
    
    return JsonResponse({
        'html': html,
        'cards_data': cards_data_json,
        'wallet_card_ids': list(user_wallet_slugs)
    })

@login_required
@cache_control_header(max_age=300, private=True)
def spend_it_input(request):
    """
    Renders the Spend It Optimizer input form.
    Loads category structure from default_category_mapping.json
    """
    # Load Category Mapping
    json_path = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'categories_list.json')
    categories = []
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)
        except Exception as e:
            print(f"Error loading category mapping: {e}")

    # Filter out ignored categories
    ignored_categories = ["Financial & Rewards", "Protection", "Travel Perks", "Financial Rewards", "Charity"]
    categories = [cat for cat in categories if cat.get('CategoryName') not in ignored_categories]

    # Map Categories to SVGs (using the keys from the JSON)
    # We'll inject the SVG content or ID directly into the dict for the template
    icon_mapping = {
        # Original & Mapped
        "Airlines": "plane",
        "Hotels": "building-2",
        "Dining": "utensils",
        "Groceries": "store",
        "Gas": "fuel",
        "Transit": "train",
        "Car Rentals": "car",
        "Retail Shopping": "shopping-bag",
        "Entertainment": "ticket",
        "Business": "briefcase",
        "Health": "heart-pulse",
        "Wellness": "spa",
        "Travel Perks": "passport",
        "Financial Rewards": "coins",
        "Protection": "shield",
        
        # New Additions
        "Travel Portals": "globe",
        "Lounges": "armchair",
        "Delivery": "truck",
        "Home Improvement": "hammer",
        "Utilities": "zap",
        "Telecom": "smartphone",
        "Streaming": "tv", 
        "Education": "graduation-cap",
        "Pet Care": "paw",
        "Fixed Expenses": "calendar",
        "Charity": "heart-handshake",
        "Cruises": "anchor",
    }

    # Get valid categories from CSV (already filtered for generics by service)
    service = OptimizerService()
    valid_categories = set(c.lower() for c in service.get_all_unique_categories())

    # Enrich categories with icon keys and JSON-safe details
    for cat in categories:
        cat_name = cat.get('CategoryName')
        cat['IconKey'] = icon_mapping.get(cat_name, 'circle-dollar-sign')
        
        # Filter details to only include those present in active rates
        details = cat.get('CategoryNameDetailed', [])
        # removed filtering to show all categories from list
        filtered_details = details 
        
        # Serialize details for safe JS usage in template data attributes
        cat['json_details'] = json.dumps(filtered_details)

    context = {
        'page_title': '"Spend It" Optimizer',
        'categories': categories
    }
    return render(request, 'calculators/spend_it_input.html', context)

@login_required
def spend_it_calculate(request):
    """
    Calculates best cards for a specific purchase amount and category.
    Returns HTML partial for htmx/ajax injection.
    """
    if request.method != 'POST':
        return redirect('spend_it_input')
        
    try:
        amount = float(request.POST.get('amount', 0))
        # The form sends 'category' which might be specific (e.g. 'Delta') or generic (e.g. 'Dining') via the dynamic inputs
        input_category = request.POST.get('category', '').strip()
        if not input_category:
            input_category = 'Everything Else'
    except ValueError:
        amount = 0.0
        input_category = 'Everything Else'

    # Get User Wallet (if authenticated)
    user_wallet_slugs = set()
    if request.user.is_authenticated:
        uid = request.session.get('uid') or request.user.username
        if uid:
            owned_cards = db.get_user_cards(uid)
            user_wallet_slugs = {c.get('card_id') for c in owned_cards}

    # Resolve Parent Category and Siblings using the mapping file
    json_path = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'categories_list.json')
    parent_category = None
    specific_category = input_category
    sibling_categories = []
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                
            # Search for the input category in the mapping
            for item in mapping:
                cat_name = item.get('CategoryName')
                detailed = item.get('CategoryNameDetailed', [])
                
                if input_category == cat_name or input_category in detailed:
                    # Match found
                    # 1. Determine Parent Rate Category (existing logic)
                    generic_fallback = next((d for d in detailed if d.startswith('Generic ')), None)
                    if generic_fallback:
                        parent_category = generic_fallback
                    else:
                        parent_category = cat_name
                    
                    # 2. Extract Sibling Categories (New Logic)
                    # Exclude the specific category itself and Generic fallback if used as parent
                    sibling_categories = [d for d in detailed if d != specific_category and d != parent_category]
                    
                    break
            
            # Fallback for "Everything Else" or unmapped
            if not parent_category and input_category == 'Everything Else':
                parent_category = 'All Purchases'

        except Exception as e:
            print(f"Error resolving parent/sibling categories: {e}")

    service = OptimizerService()
    results = service.calculate_spend_recommendations(
        amount=amount,
        specific_category=specific_category,
        parent_category=parent_category,
        user_wallet_slugs=user_wallet_slugs,
        sibling_categories=sibling_categories
    )
    
    context = {
        'results': results,
        'amount': amount,
        'category': input_category,
        'parent_category': parent_category
    }
    
    return render(request, 'calculators/spend_it_results.html', context)
