from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from django.template.loader import render_to_string
import csv
import json
import os
import math
import ast
from datetime import datetime, date
from core.services import db
from .services import OptimizerService

def index(request):
    """
    Renders the Calculators hub page.
    Includes logic for the SUB Optimizer card state (authed vs unauthed).
    """
    context = {
        'page_title': 'The Freak Lab',
    }
    return render(request, 'calculators/index.html', context)

def load_credit_card_questions():
    """
    Reads credit_card_questions.csv and returns a lookup dict for CSV-driven questions.
    Returns: { slug: [ {question_data}, ... ] }
    """
    csv_path = os.path.join(os.path.dirname(__file__), 'credit_card_questions.csv')
    questions_by_slug = {}
    
    if not os.path.exists(csv_path):
        return questions_by_slug

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                slug = row.get('slug-id', '').strip()
                short_desc = row.get('BenefitShortDescription', '').strip()
                
                # Parse ChoiceList string to list
                try:
                    choice_list_str = row.get('ChoiceList', '[]')
                    choice_list = ast.literal_eval(choice_list_str)
                except (ValueError, SyntaxError):
                    choice_list = []

                # Parse ChoiceWeight string to list
                try:
                    choice_weight_str = row.get('ChoiceWeight', '[]')
                    choice_weights = ast.literal_eval(choice_weight_str)
                except (ValueError, SyntaxError):
                    choice_weights = []

                if slug and short_desc:
                    if slug not in questions_by_slug:
                        questions_by_slug[slug] = []
                    
                    questions_by_slug[slug].append({
                        'short_desc': short_desc,
                        'question_type': row.get('QuestionType', 'yes_no'),
                        'choices': choice_list,
                        'weights': choice_weights,
                        'question': row.get('Question', ''),
                        'category': row.get('BenefitCategory', '')
                    })
    except Exception as e:
        print(f"Error reading questions CSV: {e}")
        
    return questions_by_slug

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
        if c.get('annual_fee', 0) > 0:
            # Check for benefits with dollar value
            has_benefits = False
            for b in c.get('benefits', []):
                if b.get('dollar_value') and b.get('dollar_value') > 0:
                    has_benefits = True
                    break
            
            if has_benefits:
                af_cards.append(c)

    # Sort by Annual Fee desc
    af_cards.sort(key=lambda x: x.get('annual_fee', 0), reverse=True)

    return render(request, 'calculators/worth_it_list.html', {
        'cards': af_cards
    })

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

    # Load custom questions strictly from CSV
    all_questions = load_credit_card_questions()
    card_questions = all_questions.get(card_slug, [])

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

def worth_it_calculate(request, card_slug):
    """
    Calculate the optimization score.
    Returns JSON for AJAX or renders result template.
    """
    if request.method == 'POST':
        card = db.get_card_by_slug(card_slug)
        annual_fee = card.get('annual_fee', 0)
        total_value = 0.0
        
        # Load questions strictly from CSV
        all_questions = load_credit_card_questions()
        card_questions = all_questions.get(card_slug, [])

        # Benefit lookup map
        benefits_map = {b.get('short_description', ''): b for b in card.get('benefits', [])}
        
        # Iterate through QUESTIONS to calculate value
        for idx, q_data in enumerate(card_questions):
            # Form field name: benefit_{index}
            field_name = f'benefit_{idx}'
            value_str = request.POST.get(field_name)
            
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
                        weights = q_data.get('weights', [])
                        
                        if choices:
                            idx_val = int(val)
                            # Check if we have valid weights for this choice
                            if weights and 0 <= idx_val < len(weights):
                                utilization = weights[idx_val]
                                benefit_value = utilization * dollar_val
                            else:
                                # Fallback: Linear interpolation
                                max_idx = len(choices) - 1
                                if max_idx > 0:
                                    utilization = val / max_idx
                                    benefit_value = utilization * dollar_val
                                else:
                                    # Single choice? assume 100%
                                    benefit_value = dollar_val if val >= 0 else 0
                        else:
                            benefit_value = dollar_val if val > 0 else 0
                    
                    elif 'Monthly' in time_cat:
                        benefit_value = (val / 12.0) * dollar_val
                    elif 'Quarterly' in time_cat:
                        benefit_value = (val / 4.0) * dollar_val
                    elif 'Semi' in time_cat:
                        benefit_value = (val / 2.0) * dollar_val
                    else:
                        # Toggle (1 or 0)
                        benefit_value = val * dollar_val
                        
                    total_value += benefit_value

                except (ValueError, IndexError):
                    continue
        
        score = total_value - annual_fee
        
        # Calculate percentage for circular progress (arbitrary max scale, e.g. 2x annual fee or fixed max)
        # Let's say max score is 100 for visual purposes, or relative to fees.
        # User design shows "84 SCORE". Let's map it:
        # If score > 0, maybe percentage is (score / (annual_fee * 2)) * 100?
        # Or simply, let's treat "Score" as a proprietary 0-100 metric for now, 
        # or just visualize the profitability ratio.
        # Simple approach: If profitable, 100%. If breakeven 50%. 
        # Better: (Total Value / Annual Fee) * 50. scale.
        
        # Implementation for "Score" based on Value vs Fee ratio.
        # 1.0 (Break even) = 50 score.
        # 2.0 (2x value) = 100 score.
        if annual_fee > 0:
            ratio = total_value / annual_fee
            optimization_score = min(max(int(ratio * 50), 0), 100)
        else:
            optimization_score = 100 # No fee, infinite value ratio essentially

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

def optimizer_input(request):
    """
    Renders the SUB Optimizer input form.
    """
    if not request.user.is_authenticated:
        return redirect('calculators_index')
    return render(request, 'calculators/optimizer_input.html')

def load_signup_bonuses():
    """
    Reads the default_signup.csv file and returns a dict of bonuses keyed by slug-id.
    """
    csv_path = os.path.join(settings.BASE_DIR, 'default_signup.csv')
    bonuses = {}
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV not found at {csv_path}")
        return bonuses

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                slug = row.get('slug-id')
                if slug:
                    bonuses[slug] = row
    except Exception as e:
        print(f"Error reading signup CSV: {e}")
        
    return bonuses

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
        mode=mode
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
