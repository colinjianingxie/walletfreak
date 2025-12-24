from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
import csv
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
    Reads credit_card_questions.csv and returns a lookup dict.
    Key: (slug-id, BenefitShortDescription) -> Question Data Dict
    """
    csv_path = os.path.join(os.path.dirname(__file__), 'credit_card_questions.csv')
    questions = {}
    
    if not os.path.exists(csv_path):
        return questions

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

                if slug and short_desc:
                    questions[(slug, short_desc)] = {
                        'question_type': row.get('QuestionType', 'yes_no'),
                        'choices': choice_list,
                        'question': row.get('Question', ''),
                        'category': row.get('BenefitCategory', '')
                    }
    except Exception as e:
        print(f"Error reading questions CSV: {e}")
        
    return questions

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

    # Load custom questions
    questions_map = load_credit_card_questions()

    # Filter benefits with dollar value
    benefits = card.get('benefits', [])
    audit_benefits = []
    
    for b in benefits:
        if b.get('dollar_value') and b.get('dollar_value') > 0:
            short_desc = b.get('short_description', '')
            
            # Check for custom question
            q_data = questions_map.get((card_slug, short_desc))
            
            # Defaults
            time_cat = b.get('time_category', 'Annually')
            input_type = 'toggle' # Default
            choices = []
            max_val = 1
            
            if q_data:
                # Use data from CSV
                label = q_data['question']
                q_type = q_data['question_type']
                choices = q_data['choices']
                
                if q_type == 'multiple_choice' and choices:
                    input_type = 'multiple_choice'
                    max_val = len(choices) - 1 # We'll use index as value
                else:
                    input_type = 'toggle'
                    max_val = 1
            else:
                # Fallback logic
                if 'Monthly' in time_cat:
                    input_type = 'slider'
                    max_val = 12
                elif 'Quarterly' in time_cat:
                    input_type = 'slider'
                    max_val = 4
                elif 'Semi' in time_cat:
                    input_type = 'slider'
                    max_val = 2
                
                if 'Monthly' in time_cat or 'Quarterly' in time_cat:
                    label = f"How often do you use the ${b.get('dollar_value')} {b.get('short_description', 'credit')}?"
                else:
                    label = f"Would you use the ${b.get('dollar_value')} {b.get('short_description', 'credit')}?"

            b['audit_config'] = {
                'input_type': input_type,
                'max_val': max_val,
                'label': label,
                'choices': choices
            }
            audit_benefits.append(b)

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
        
        # Load questions map for calculation logic
        questions_map = load_credit_card_questions()
        
        # Iterate through POST data
        # Expected format: benefit_{index}: value
        for key, value in request.POST.items():
            if key.startswith('benefit_'):
                try:
                    val = float(value)
                    # We need to know the 'value per unit' or calculate based on the benefit logic.
                    # Let's look up by index.
                    b_idx = int(key.split('_')[1])
                    if 0 <= b_idx < len(card.get('benefits', [])):
                        benefit = card['benefits'][b_idx]
                        short_desc = benefit.get('short_description', '')
                        
                        # Check for custom question to match logic
                        q_data = questions_map.get((card_slug, short_desc))
                        
                        # Calculation Logic
                        time_cat = benefit.get('time_category', '')
                        dollar_val = benefit.get('dollar_value') or 0
                        
                        benefit_value = 0.0
                        
                        if q_data and q_data['question_type'] == 'multiple_choice':
                            # Logic for multiple choice
                            # val is the INDEX selected (0 to N-1)
                            choices = q_data['choices']
                            if choices:
                                max_idx = len(choices) - 1
                                if max_idx > 0:
                                    # Linear interpolation: index / max_idx
                                    # 0 -> 0%, Max -> 100%
                                    # Example: ['Never', 'Rarely', 'Often'] -> 0, 0.5, 1.0
                                    utilization = val / max_idx
                                    benefit_value = utilization * dollar_val
                                else:
                                    # Single choice? assume 100% if selected?
                                    benefit_value = dollar_val if val >= 0 else 0
                            else:
                                benefit_value = dollar_val if val > 0 else 0
                        
                        elif 'Monthly' in time_cat:
                            # dollar_val is annual total.
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

        # Return context for result template
        return render(request, 'calculators/worth_it_result.html', {
            'card': card,
            'annual_fee': annual_fee,
            'total_value': total_value,
            'net_profit': score, # This is the dollar amount
            'net_profit_abs': abs(score),
            'score_display': optimization_score, # 0-100
            'score_percentage': optimization_score, # For CSS circle
            'is_worth_it': score >= 0
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
    
    return render(request, 'calculators/optimizer_results.html', context)
