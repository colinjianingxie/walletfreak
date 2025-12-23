from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from core.services import db

def index(request):
    """
    Renders the Calculators hub page.
    Includes logic for the SUB Optimizer card state (authed vs unauthed).
    """
    context = {
        'page_title': 'The Freak Lab',
    }
    return render(request, 'calculators/index.html', context)

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

    # Filter benefits with dollar value
    benefits = card.get('benefits', [])
    audit_benefits = []
    
    for b in benefits:
        if b.get('dollar_value') and b.get('dollar_value') > 0:
            # Determine input type based on time_category
            time_cat = b.get('time_category', 'Annually')
            input_type = 'toggle' # Default
            max_val = 1
            
            if 'Monthly' in time_cat:
                input_type = 'slider'
                max_val = 12
                # Ensure period_values exists or is calculable
            elif 'Quarterly' in time_cat:
                input_type = 'slider' # or number
                max_val = 4
            elif 'Semi' in time_cat:
                input_type = 'slider'
                max_val = 2
                
            b['audit_config'] = {
                'input_type': input_type,
                'max_val': max_val,
                'label': f"How often do you use the ${b.get('dollar_value')} {b.get('short_description', 'credit')}?"
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
        
        # Iterate through POST data
        # Expected format: benefit_{index}: value
        for key, value in request.POST.items():
            if key.startswith('benefit_'):
                try:
                    val = float(value)
                    # We need to know the 'value per unit' or calculate based on the benefit logic.
                    # Simpler approach: Pass the dollar value per unit in the form or look it up.
                    # Let's look up by index.
                    b_idx = int(key.split('_')[1])
                    if 0 <= b_idx < len(card.get('benefits', [])):
                        benefit = card['benefits'][b_idx]
                        
                        # Calculation Logic
                        time_cat = benefit.get('time_category', '')
                        dollar_val = benefit.get('dollar_value') or 0
                        
                        if 'Monthly' in time_cat:
                            # dollar_val is usually Total Annual Value in the CSV? 
                            # Let's check parse_benefits_csv.py.
                            # "per_month = dollar_value / 12". So dollar_value IS the annual total.
                            # So value obtained = (input_months / 12) * dollar_value
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
        
        # Return context for result template
        return render(request, 'calculators/worth_it_result.html', {
            'card': card,
            'annual_fee': annual_fee,
            'total_value': total_value,
            'score': score,
            'is_worth_it': score >= 0
        })
    
    return redirect('worth_it_audit', card_slug=card_slug)
