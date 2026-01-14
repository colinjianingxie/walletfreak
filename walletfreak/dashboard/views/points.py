from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from core.services import db
import json

@login_required
def points_collection(request):
    """Points collection view showing loyalty balances"""
    uid = request.session.get('uid')
    if not uid:
        return redirect('login')
    
    # 1. Fetch all available loyalty programs (Master List)
    all_programs = db.get_all_loyalty_programs()
    programs_map = {p['id']: p for p in all_programs}
    
    # 2. Fetch user's saved balances
    user_balances = db.get_user_loyalty_balances(uid)
    
    # 3. Fetch user's active cards for cross-referencing
    user_cards = db.get_user_cards(uid, status='active')
    
    # Filter for cards that have a loyalty program (for "Active Cards" section)
    active_cards = user_cards 
    
    # 4. Determine display list
    # Combine user's explicit balances with programs from active cards
    programs_to_display = {}
    
    # 4a. Add explicit balances
    for b in user_balances:
        pid = b['program_id']
        programs_to_display[pid] = {
            'balance': b.get('balance', 0),
            'source': 'balance'
        }
        
    # 4b. Add programs from active cards
    for card in active_cards:
        # We know card has loyalty_program because of filter above
        lp = card.get('loyalty_program')
        if lp and lp not in programs_to_display:
            programs_to_display[lp] = { # Create new entry with 0 balance
                'balance': 0,
                'source': 'card'
            }
    
    # Generate Display List
    display_programs = []
    
    for pid, data in programs_to_display.items():
        prog_details = programs_map.get(pid, {})
        if not prog_details:
             prog_details = {'program_name': 'Unknown Program', 'id': pid, 'type': 'other'}
             
        # Find active cards for this program
        active_cards_for_program = []
        for card in active_cards: # Use our filtered list
            if card.get('loyalty_program') == pid:
                active_cards_for_program.append(card)
                
        # Calculate valuation value
        balance = data.get('balance', 0)
        valuation = prog_details.get('valuation', 1.0) # Default 1.0 cpp if missing
        est_value = (balance * valuation) / 100.0
        
        display_programs.append({
            'program_id': pid,
            'name': prog_details.get('program_name'),
            'type': prog_details.get('type', 'other'),
            'balance': balance,
            'valuation': valuation,
            'est_value': est_value,
            'active_cards': active_cards_for_program,
            'logo_url': prog_details.get('logo_url'),
            'category': prog_details.get('currency_group', 'Points')
        })
        
    # Sort display programs?
    display_programs.sort(key=lambda x: x['name'])
    
    # Total Est Value
    total_est_value = sum(p['est_value'] for p in display_programs)

    # Attach balances to active_cards for the UI
    for card in active_cards:
        pid = card.get('loyalty_program')
        if pid and pid in programs_to_display:
            card['program_balance'] = programs_to_display[pid].get('balance', 0)




    

    context = {
        'display_programs': display_programs,
        'all_programs_json': json.dumps(all_programs, default=str),
        'total_est_value': total_est_value,

        'active_cards': active_cards
    }
    
    return render(request, 'dashboard/points_collection.html', context)


@login_required
@require_POST
def add_loyalty_program(request):
    """Add a loyalty program to user's collection"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    try:
        data = json.loads(request.body)
        program_id = data.get('program_id')
        
        if not program_id:
            return JsonResponse({'success': False, 'error': 'Missing program_id'}, status=400)
            
        success = db.update_user_loyalty_balance(uid, program_id, 0)
        
        return JsonResponse({'success': success})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def update_loyalty_balance(request):
    """Update balance for a program"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    try:
        data = json.loads(request.body)
        program_id = data.get('program_id')
        balance = data.get('balance')
        
        if not program_id or balance is None:
            return JsonResponse({'success': False, 'error': 'Missing data'}, status=400)
            
        success = db.update_user_loyalty_balance(uid, program_id, balance)
        
        return JsonResponse({'success': success})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_POST
def remove_loyalty_program(request):
    """Remove a program from collection"""
    uid = request.session.get('uid')
    if not uid:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
        
    try:
        data = json.loads(request.body)
        program_id = data.get('program_id')
        
        if not program_id:
            return JsonResponse({'success': False, 'error': 'Missing program_id'}, status=400)
            
        success = db.remove_user_loyalty_program(uid, program_id)
        
        return JsonResponse({'success': success})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
