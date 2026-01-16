from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.services import db
import json
import os
from django.conf import settings

@login_required
def index(request):
    """
    Renders the Hotel Hunter tool.
    Fetches user's loyalty balances (Hotel & Bank) and displays Chase hotel inventory.
    """
    uid = request.session.get('uid') or request.user.username
    
    # --- 1. Fetch Loyalty Points (Hotel + Transferable Bank Points) ---
    loyalty_points = []
    if uid:
        try:
            # Reusing logic from points_collection
            all_programs = db.get_all_loyalty_programs()
            programs_map = {p['id']: p for p in all_programs}
            user_balances = db.get_user_loyalty_balances(uid)
            user_cards = db.get_user_cards(uid, status='active')
            
            # Build map of program_id -> balance
            prog_balances = {}
            
            # From explicit balances
            for b in user_balances:
                prog_balances[b['program_id']] = b.get('balance', 0)
                
            # From cards (ensure program exists in list even if 0 balance)
            for card in user_cards:
                lp = card.get('loyalty_program')
                if lp and lp not in prog_balances:
                    prog_balances[lp] = 0
            
            # Filter and Format
            for pid, balance in prog_balances.items():
                details = programs_map.get(pid)
                if details:
                    # Filter for 'hotel' or 'bank' (transferable) types
                    p_type = details.get('type', '').lower()
                    if p_type in ['hotel', 'bank', 'credit_card']: 
                        # Helper for color mapping
                        dot_color = 'dot-blue'
                        if 'hyatt' in details.get('program_name', '').lower(): dot_color = 'dot-blue'
                        elif 'marriott' in details.get('program_name', '').lower(): dot_color = 'dot-yellow' 
                        elif 'hilton' in details.get('program_name', '').lower(): dot_color = 'dot-indigo'
                        elif 'ihg' in details.get('program_name', '').lower(): dot_color = 'dot-yellow'
                        elif p_type == 'bank': dot_color = 'dot-green'

                        loyalty_points.append({
                            'name': details.get('program_name_short') or details.get('program_name'),
                            'balance': f"{balance:,}",
                            'dot_class': dot_color
                        })
                        
        except Exception as e:
            print(f"Error fetching points: {e}")

    # --- 2. Fetch Hotels ---
    hotels = []
    location_query = request.GET.get('location', '').strip()
    
    json_path = os.path.join(settings.BASE_DIR, 'walletfreak_data', 'chase_hotels', 'chase_hotels_data.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                chase_data = json.load(f)
                
                # Filter Logic
                for h in chase_data:
                    # Search
                    if location_query:
                        search_str = f"{h.get('name', '')} {h.get('city', '')} {h.get('country', '')} {h.get('address', '')}".lower()
                        if location_query.lower() not in search_str:
                            continue
                            
                    # Construct Display Object
                    loc_display = h.get('address', '')
                    if h.get('city'):
                        parts = [h.get('address_line'), h.get('city'), h.get('state'), h.get('zip_code')]
                        loc_display = ", ".join([p for p in parts if p])
                        if h.get('country') and h.get('country') not in ['United States', 'USA']:
                            loc_display += f", {h.get('country')}"

                    hotels.append({
                        'name': h.get('name'),
                        'location': loc_display,
                        'price': "Check Dates",
                        'rating': "N/A",
                        'tags': [h.get('type', 'The Edit')],
                        'recommendation': {
                            'title': "Chase Luxury Hotel",
                            'description': "Bookable via Chase.",
                            'badge': "LHC",
                            'icon': "shield",
                            'bg_color': "bg-slate-100",
                            'text_color': "text-slate-700",
                            'border_color': "border-slate-200"
                        }
                    })
                    
                # Limit results
                if not location_query:
                     hotels = hotels[:50] 
                else:
                    hotels = hotels[:100]
                    
        except Exception as e:
            print(f"Error loading Chase hotel data: {e}")

    context = {
        'page_title': 'Hotel Hunter',
        'hotels': hotels,
        'location': location_query,
        'dates': request.GET.get('dates', 'Oct 12 - Oct 16'),
        'guests': request.GET.get('guests', '2'),
        'points_list': loyalty_points, 
        'active_cards_count': len(user_cards) if uid else 0
    }
    return render(request, 'hotel_hunter/index.html', context)
